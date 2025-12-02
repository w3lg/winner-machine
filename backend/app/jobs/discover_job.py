"""
Job de découverte de produits - Module A.

Récupère des produits depuis Keepa et les stocke en base.
"""
import logging
from typing import Dict, Set

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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
                stats["errors"] += category_stats.get("errors", 0)
                stats["categories_processed"] += 1
                logger.info(
                    f"Catégorie {category_config.name}: "
                    f"{category_stats['created']} créés, "
                    f"{category_stats['updated']} mis à jour, "
                    f"{category_stats['total_processed']} traités"
                )
                # Pas besoin de commit ici car on commit déjà après chaque produit
            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement de la catégorie {category_config.name}: {str(e)}",
                    exc_info=True,
                )
                stats["errors"] += 1
                try:
                    self.db.rollback()
                except Exception:
                    pass
                # Continue avec la catégorie suivante

        # Pas besoin de commit final car on commit déjà après chaque produit

        logger.info("=== Job de découverte terminé avec succès ===")
        logger.info(
            f"Statistiques globales: {stats['created']} créés, "
            f"{stats['updated']} mis à jour, "
            f"{stats['total_processed']} traités, "
            f"{stats['categories_processed']} catégories, "
            f"{stats['errors']} erreurs"
        )

        return stats

    def _process_category(self, category_config: CategoryConfig) -> Dict[str, int]:
        """
        Traite une catégorie : récupère les produits et les stocke.

        Args:
            category_config: Configuration de la catégorie.

        Returns:
            Statistiques pour cette catégorie.
        """
        stats = {"created": 0, "updated": 0, "total_processed": 0, "errors": 0}

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

                # Upsert explicite : vérifier puis insérer ou mettre à jour
                is_new = self._upsert_product(keepa_product, category_config.name)
                
                if is_new:
                    stats["created"] += 1
                else:
                    stats["updated"] += 1

                # Marquer cet ASIN comme traité
                self._processed_asins.add(asin)

                stats["total_processed"] += 1
            except IntegrityError as e:
                # Si jamais une UniqueViolation se produit (ne devrait pas arriver avec notre logique)
                if "product_candidates_asin_key" in str(e.orig) or "asin" in str(e.orig).lower():
                    logger.warning(
                        f"ASIN {keepa_product.asin} existe déjà (UniqueViolation inattendue), "
                        "tentative de mise à jour après rollback"
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
                            self.db.commit()
                            stats["updated"] += 1
                            self._processed_asins.add(asin)
                            stats["total_processed"] += 1
                    except Exception as retry_e:
                        logger.error(
                            f"Erreur lors de la mise à jour du produit {keepa_product.asin}: {str(retry_e)}",
                            exc_info=True,
                        )
                        stats["errors"] = stats.get("errors", 0) + 1
                else:
                    logger.error(
                        f"Erreur d'intégrité lors du traitement du produit {keepa_product.asin}: {str(e)}",
                        exc_info=True,
                    )
                    stats["errors"] = stats.get("errors", 0) + 1
                continue
            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement du produit {keepa_product.asin}: {str(e)}",
                    exc_info=True,
                )
                try:
                    self.db.rollback()
                except Exception:
                    pass
                stats["errors"] = stats.get("errors", 0) + 1
                # Continue avec le produit suivant
                continue

        return stats

    def _upsert_product(self, keepa_product, category_name: str) -> bool:
        """
        Upsert un produit : vérifie s'il existe, puis insère ou met à jour.
        
        Args:
            keepa_product: Produit Keepa à traiter.
            category_name: Nom de la catégorie.
        
        Returns:
            True si le produit a été créé, False s'il a été mis à jour.
        
        Note:
            Le status est préservé si le produit a déjà été traité (scored, selected, launched),
            sinon il est mis à jour à "new".
        """
        # Rechercher le produit existant par ASIN
        existing = (
            self.db.query(ProductCandidate)
            .filter(ProductCandidate.asin == keepa_product.asin)
            .first()
        )
        
        if existing:
            # PRODUIT EXISTANT : mise à jour
            existing.title = keepa_product.title
            existing.category = category_name
            existing.avg_price = keepa_product.avg_price
            existing.bsr = keepa_product.bsr
            existing.estimated_sales_per_day = keepa_product.estimated_sales_per_day
            existing.reviews_count = keepa_product.reviews_count
            existing.rating = keepa_product.rating
            existing.raw_keepa_data = keepa_product.raw_data
            existing.source_marketplace = "amazon_fr"
            
            # Préserver le status si le produit a déjà été traité
            if existing.status not in ["scored", "selected", "launched"]:
                existing.status = "new"
            
            # updated_at sera mis à jour automatiquement par le modèle
            self.db.flush()
            self.db.commit()
            
            return False  # Produit mis à jour
        
        else:
            # NOUVEAU PRODUIT : création
            new_candidate = ProductCandidate(
                asin=keepa_product.asin,
                title=keepa_product.title,
                category=category_name,
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
            self.db.flush()
            self.db.commit()
            
            return True  # Produit créé

