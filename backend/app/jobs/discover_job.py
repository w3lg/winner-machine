"""
Job de découverte de produits - Module A.

Récupère des produits depuis Keepa et les stocke en base.
"""
import logging
import json
from typing import Dict, Set
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

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
        Upsert un produit en utilisant PostgreSQL ON CONFLICT DO UPDATE.
        
        Cette méthode utilise du SQL brut via SQLAlchemy Core pour garantir
        qu'il n'y aura jamais de batch INSERT et que l'upsert est natif.
        
        Args:
            keepa_product: Produit Keepa à traiter.
            category_name: Nom de la catégorie.
        
        Returns:
            True si le produit a été créé, False s'il a été mis à jour.
        
        Note:
            Le status est préservé si le produit a déjà été traité (scored, selected, launched),
            sinon il est mis à jour à "new".
        """
        # Vérifier si le produit existe pour déterminer si c'est une création ou mise à jour
        existing = (
            self.db.query(ProductCandidate)
            .filter(ProductCandidate.asin == keepa_product.asin)
            .first()
        )
        
        # Préparer les données
        asin = keepa_product.asin
        product_id = existing.id if existing else uuid4()
        raw_data_json = json.dumps(keepa_product.raw_data) if isinstance(keepa_product.raw_data, dict) else keepa_product.raw_data
        
        # Déterminer le status (préserver si déjà traité)
        if existing and existing.status in ["scored", "selected", "launched"]:
            new_status = existing.status
        else:
            new_status = "new"
        
        # Préparer created_at (préserver si existe, sinon NOW())
        created_at = existing.created_at if existing else datetime.utcnow()
        
        # Construire la requête SQL avec ON CONFLICT DO UPDATE (solution native PostgreSQL)
        # Cette requête garantit qu'il n'y aura jamais de UniqueViolation
        # Utiliser bindparam avec types SQLAlchemy pour les conversions automatiques
        raw_data_dict = keepa_product.raw_data if isinstance(keepa_product.raw_data, dict) else json.loads(keepa_product.raw_data) if isinstance(keepa_product.raw_data, str) else {}
        
        sql_query = text("""
            INSERT INTO product_candidates (
                id, asin, title, category, source_marketplace, avg_price, bsr,
                estimated_sales_per_day, reviews_count, rating, raw_keepa_data, status,
                created_at, updated_at
            ) VALUES (
                :product_id, :asin, :title, :category, :source_marketplace, 
                :avg_price, :bsr, :estimated_sales_per_day, :reviews_count, :rating, 
                :raw_keepa_data, :status, 
                :created_at, NOW()
            )
            ON CONFLICT (asin) DO UPDATE SET
                title = EXCLUDED.title,
                category = EXCLUDED.category,
                avg_price = EXCLUDED.avg_price,
                bsr = EXCLUDED.bsr,
                estimated_sales_per_day = EXCLUDED.estimated_sales_per_day,
                reviews_count = EXCLUDED.reviews_count,
                rating = EXCLUDED.rating,
                raw_keepa_data = EXCLUDED.raw_keepa_data,
                source_marketplace = EXCLUDED.source_marketplace,
                status = CASE 
                    WHEN product_candidates.status IN ('scored', 'selected', 'launched') 
                    THEN product_candidates.status 
                    ELSE EXCLUDED.status 
                END,
                updated_at = NOW()
        """)
        
        # Préparer les paramètres avec types Python natifs
        # psycopg2 et SQLAlchemy géreront automatiquement les conversions
        params = {
            "product_id": product_id,  # Passer directement l'UUID Python, psycopg2 le convertira
            "asin": asin,
            "title": keepa_product.title,
            "category": category_name,
            "source_marketplace": "amazon_fr",
            "avg_price": float(keepa_product.avg_price) if keepa_product.avg_price else None,
            "bsr": keepa_product.bsr,
            "estimated_sales_per_day": float(keepa_product.estimated_sales_per_day) if keepa_product.estimated_sales_per_day else None,
            "reviews_count": keepa_product.reviews_count,
            "rating": float(keepa_product.rating) if keepa_product.rating else None,
            "raw_keepa_data": json.dumps(raw_data_dict),  # Passer en JSON string, PostgreSQL le convertira en JSONB
            "status": new_status,
            "created_at": created_at,
        }
        
        # Exécuter l'upsert avec SQL brut - garanti d'éviter les batch INSERT
        try:
            self.db.execute(sql_query, params)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de l'upsert du produit {asin}: {str(e)}", exc_info=True)
            raise
        
        # Retourner True si nouveau produit, False si mis à jour
        return existing is None

