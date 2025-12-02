"""
Job de découverte de produits - Module A.

Récupère des produits depuis Keepa et les stocke en base.
"""
import logging
from typing import Dict, Set

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.product_candidate import ProductCandidate
from app.services.keepa_client import KeepaClient
from app.services.category_config import get_category_config_service, CategoryConfig

# Logger pour ce module
logger = logging.getLogger(__name__)


class DiscoverJob:
    """Job pour découvrir des produits candidats."""

    def __init__(self, db: Session):
        """
        Initialise le job.

        Args:
            db: Session SQLAlchemy pour la base de données.
        """
        self.db = db
        self.keepa_client = KeepaClient()
        self.category_service = get_category_config_service()
        # Set pour tracker les ASINs déjà traités dans cette exécution
        self._processed_asins: Set[str] = set()

    def run(self) -> Dict[str, int]:
        """
        Lance le job de découverte.

        Returns:
            Dictionnaire avec les statistiques :
            - created: nombre de produits créés
            - updated: nombre de produits mis à jour
            - total_processed: total traité
            - categories_processed: nombre de catégories traitées
            - errors: nombre d'erreurs rencontrées
        """
        logger.info("=== Démarrage du job de découverte de produits ===")

        categories = self.category_service.get_active_categories()
        if not categories:
            logger.warning("Aucune catégorie active configurée. Le job ne fera rien.")
            return {
                "created": 0,
                "updated": 0,
                "total_processed": 0,
                "categories_processed": 0,
                "errors": 0,
            }

        logger.info(f"Nombre de catégories actives à traiter: {len(categories)}")

        stats = {
            "created": 0,
            "updated": 0,
            "total_processed": 0,
            "categories_processed": 0,
            "errors": 0,
        }

        # Réinitialiser le tracker d'ASINs pour cette exécution
        self._processed_asins.clear()

        for category_config in categories:
            try:
                logger.info(
                    f"Traitement de la catégorie: {category_config.name} (ID: {category_config.id})"
                )
                category_stats = self._process_category(category_config)
                stats["created"] += category_stats["created"]
                stats["updated"] += category_stats["updated"]
                stats["total_processed"] += category_stats["total_processed"]
                stats["categories_processed"] += 1
                logger.info(
                    f"Catégorie {category_config.name}: "
                    f"{category_stats['created']} créés, "
                    f"{category_stats['updated']} mis à jour, "
                    f"{category_stats['total_processed']} traités"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement de la catégorie {category_config.name}: {str(e)}",
                    exc_info=True,
                )
                stats["errors"] += 1
                # Continue avec la catégorie suivante

        try:
            self.db.commit()
            logger.info("=== Job de découverte terminé avec succès ===")
            logger.info(
                f"Statistiques globales: {stats['created']} créés, "
                f"{stats['updated']} mis à jour, "
                f"{stats['total_processed']} traités, "
                f"{stats['categories_processed']} catégories, "
                f"{stats['errors']} erreurs"
            )
        except SQLAlchemyError as e:
            logger.error(f"Erreur lors du commit en base de données: {str(e)}", exc_info=True)
            self.db.rollback()
            stats["errors"] += 1
            raise

        return stats

    def _process_category(self, category_config: CategoryConfig) -> Dict[str, int]:
        """
        Traite une catégorie : récupère les produits et les stocke.

        Args:
            category_config: Configuration de la catégorie.

        Returns:
            Statistiques pour cette catégorie.
        """
        stats = {"created": 0, "updated": 0, "total_processed": 0}

        try:
            # Récupérer les produits depuis Keepa
            products = self.keepa_client.get_top_products_by_category(category_config)
        except Exception as e:
            logger.error(
                f"Erreur KeepaClient pour la catégorie {category_config.name}: {str(e)}",
                exc_info=True,
            )
            # Retourner des stats vides mais ne pas faire planter le job
            return stats

        if not products:
            logger.warning(
                f"Aucun produit retourné pour la catégorie {category_config.name}"
            )
            return stats

        logger.debug(f"Récupération de {len(products)} produits pour {category_config.name}")

        for keepa_product in products:
            try:
                asin = keepa_product.asin

                # Skip si cet ASIN a déjà été traité dans cette exécution
                if asin in self._processed_asins:
                    logger.debug(f"ASIN {asin} déjà traité dans cette exécution, skip")
                    continue

                # Vérifier si le produit existe déjà en base
                existing = (
                    self.db.query(ProductCandidate)
                    .filter(ProductCandidate.asin == asin)
                    .first()
                )

                if existing:
                    # Mettre à jour le produit existant
                    existing.title = keepa_product.title
                    existing.category = category_config.name
                    existing.avg_price = keepa_product.avg_price
                    existing.bsr = keepa_product.bsr
                    existing.estimated_sales_per_day = keepa_product.estimated_sales_per_day
                    existing.reviews_count = keepa_product.reviews_count
                    existing.rating = keepa_product.rating
                    existing.raw_keepa_data = keepa_product.raw_data
                    existing.source_marketplace = "amazon_fr"
                    # Ne pas changer le status si le produit a déjà été traité
                    if existing.status not in ["scored", "selected", "launched"]:
                        existing.status = "new"
                    stats["updated"] += 1
                else:
                    # Créer un nouveau produit candidat
                    new_candidate = ProductCandidate(
                        asin=asin,
                        title=keepa_product.title,
                        category=category_config.name,
                        source_marketplace="amazon_fr",
                        avg_price=keepa_product.avg_price,
                        bsr=keepa_product.bsr,
                        estimated_sales_per_day=keepa_product.estimated_sales_per_day,
                        reviews_count=keepa_product.reviews_count,
                        rating=keepa_product.rating,
                        raw_keepa_data=keepa_product.raw_data,
                        status="new",
                    )
                    self.db.add(new_candidate)
                    stats["created"] += 1

                # Marquer cet ASIN comme traité
                self._processed_asins.add(asin)
                
                # Flush périodique pour que les nouveaux produits soient visibles
                # dans les requêtes suivantes (pour éviter les doublons)
                if stats["created"] % 10 == 0:
                    self.db.flush()

                stats["total_processed"] += 1
            except IntegrityError as e:
                # Gérer spécifiquement les violations de contrainte unique
                if "product_candidates_asin_key" in str(e.orig) or "asin" in str(e.orig).lower():
                    logger.warning(
                        f"ASIN {keepa_product.asin} existe déjà en base (violation de contrainte unique), "
                        "tentative de mise à jour"
                    )
                    self.db.rollback()
                    # Réessayer avec une mise à jour
                    try:
                        existing = (
                            self.db.query(ProductCandidate)
                            .filter(ProductCandidate.asin == keepa_product.asin)
                            .first()
                        )
                        if existing:
                            existing.title = keepa_product.title
                            existing.category = category_config.name
                            existing.avg_price = keepa_product.avg_price
                            existing.bsr = keepa_product.bsr
                            existing.estimated_sales_per_day = keepa_product.estimated_sales_per_day
                            existing.reviews_count = keepa_product.reviews_count
                            existing.rating = keepa_product.rating
                            existing.raw_keepa_data = keepa_product.raw_data
                            existing.source_marketplace = "amazon_fr"
                            if existing.status not in ["scored", "selected", "launched"]:
                                existing.status = "new"
                            stats["updated"] += 1
                            self._processed_asins.add(keepa_product.asin)
                            stats["total_processed"] += 1
                    except Exception as retry_e:
                        logger.error(
                            f"Erreur lors de la mise à jour du produit {keepa_product.asin}: {str(retry_e)}",
                            exc_info=True,
                        )
                else:
                    logger.error(
                        f"Erreur d'intégrité lors du traitement du produit {keepa_product.asin}: {str(e)}",
                        exc_info=True,
                    )
                continue
            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement du produit {keepa_product.asin}: {str(e)}",
                    exc_info=True,
                )
                # Continue avec le produit suivant
                continue

        return stats

