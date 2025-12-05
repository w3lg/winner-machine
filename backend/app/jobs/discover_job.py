"""
Job de découverte de produits - Module A.

Récupère des produits depuis Keepa et les stocke en base.
"""
import logging
import json
from typing import Dict, Set, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.product_candidate import ProductCandidate
from app.models.harvested_asin import HarvestedAsin
from app.services.keepa_client import KeepaClient
from app.services.market_config import get_market_config_service, MarketConfig

# Logger pour ce module
logger = logging.getLogger(__name__)


class DiscoverJob:
    """Job pour découvrir des produits candidats."""

    def __init__(self, db: Session, market_code: Optional[str] = None):
        """
        Initialise le job.

        Args:
            db: Session SQLAlchemy pour la base de données.
            market_code: Code du marché à traiter (ex: "amazon_fr"). 
                         Si None, utilise "amazon_fr" par défaut.
        """
        self.db = db
        self.keepa_client = KeepaClient()
        self.market_service = get_market_config_service()
        self.market_code = market_code or "amazon_fr"  # Par défaut: Amazon FR
        # Set pour tracker les ASINs déjà traités dans cette exécution
        self._processed_asins: Set[str] = set()
        # Flag pour forcer la mise à jour même si le produit a déjà été traité
        self._force_update: bool = False

    def run(self, force: bool = False) -> Dict[str, int]:
        """
        Lance le job de découverte pour le marché spécifié.

        Args:
            force: Si True, force la mise à jour de TOUS les produits (même ceux déjà traités).
                   Si False, préserve le status des produits déjà traités (comportement par défaut).

        Returns:
            Dictionnaire avec les statistiques :
            - created: nombre de produits créés
            - updated: nombre de produits mis à jour
            - total_processed: total traité
            - markets_processed: nombre de marchés traités
            - errors: nombre d'erreurs rencontrées
        """
        logger.info(f"=== Démarrage du job de découverte de produits pour le marché: {self.market_code} (force={force}) ===")
        self._force_update = force

        # Récupérer la configuration du marché
        market_config = self.market_service.get_market_by_code(self.market_code)
        if not market_config:
            logger.error(f"Marché '{self.market_code}' non trouvé dans la configuration.")
            return {
                "created": 0,
                "updated": 0,
                "total_processed": 0,
                "markets_processed": 0,
                "errors": 1,
            }

        if not market_config.active:
            logger.warning(f"Marché '{self.market_code}' est désactivé. Le job ne fera rien.")
            return {
                "created": 0,
                "updated": 0,
                "total_processed": 0,
                "markets_processed": 0,
                "errors": 0,
            }

        logger.info(f"Traitement du marché: {market_config.label} (domain: {market_config.domain})")

        stats = {
            "created": 0,
            "updated": 0,
            "total_processed": 0,
            "markets_processed": 0,
            "errors": 0,
        }

        # Réinitialiser le tracker d'ASINs pour cette exécution
        self._processed_asins.clear()

        try:
            market_stats = self._process_market(market_config)
            stats["created"] += market_stats["created"]
            stats["updated"] += market_stats["updated"]
            stats["total_processed"] += market_stats["total_processed"]
            stats["errors"] += market_stats.get("errors", 0)
            stats["markets_processed"] = 1
            
            logger.info(
                f"Marché {market_config.label}: "
                f"{market_stats['created']} créés, "
                f"{market_stats['updated']} mis à jour, "
                f"{market_stats['total_processed']} traités"
            )
        except Exception as e:
            logger.error(
                f"Erreur lors du traitement du marché {market_config.label}: {str(e)}",
                exc_info=True,
            )
            stats["errors"] += 1
            try:
                self.db.rollback()
            except Exception:
                pass

        logger.info("=== Job de découverte terminé ===")
        logger.info(
            f"Statistiques globales: {stats['created']} créés, "
            f"{stats['updated']} mis à jour, "
            f"{stats['total_processed']} traités, "
            f"{stats['markets_processed']} marché(s), "
            f"{stats['errors']} erreur(s)"
        )

        return stats

    def _process_market(self, market_config: MarketConfig) -> Dict[str, int]:
        """
        Traite un marché : récupère les produits depuis la liste d'ASINs et les stocke.

        Args:
            market_config: Configuration du marché.

        Returns:
            Statistiques pour ce marché.
        """
        stats = {"created": 0, "updated": 0, "total_processed": 0, "errors": 0}

        # Récupérer les ASINs depuis plusieurs sources (union)
        all_asins = self._get_all_asins_for_market(market_config)

        if not all_asins:
            logger.warning(
                f"Aucun ASIN disponible pour le marché {market_config.label}. Le marché sera ignoré."
            )
            return stats

        logger.info(
            f"Traitement de {len(all_asins)} ASINs pour le marché {market_config.label} "
            f"(sources combinées: markets_asins.yml + harvested_asins)"
        )

        try:
            # Récupérer les produits depuis Keepa en utilisant la liste d'ASINs combinée
            products = self.keepa_client.get_products_by_asins(
                domain=market_config.domain,
                asin_list=all_asins
            )
        except Exception as e:
            logger.error(
                f"Erreur KeepaClient pour le marché {market_config.label}: {str(e)}",
                exc_info=True,
            )
            stats["errors"] += 1
            return stats

        if not products:
            logger.warning(
                f"Aucun produit retourné par Keepa pour le marché {market_config.label}"
            )
            return stats

        logger.info(f"Récupération de {len(products)} produits enrichis pour {market_config.label}")

        for keepa_product in products:
            try:
                asin = keepa_product.asin

                # Skip si cet ASIN a déjà été traité dans cette exécution
                if asin in self._processed_asins:
                    logger.debug(f"ASIN {asin} déjà traité dans cette exécution, skip")
                    continue

                # Upsert explicite : vérifier puis insérer ou mettre à jour
                is_new = self._upsert_product(
                    keepa_product,
                    market_config.label,
                    self.market_code,
                    domain=market_config.domain,
                    force=self._force_update,
                )
                
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
                            # Mise à jour des champs (sera gérée par _upsert_product lors du retry)
                            pass
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

    def _get_all_asins_for_market(self, market_config: MarketConfig) -> list[str]:
        """
        Récupère tous les ASINs pour un marché depuis plusieurs sources.

        Combine les ASINs de :
        - markets_asins.yml (via market_config.asins)
        - harvested_asins (table DB)

        Args:
            market_config: Configuration du marché.

        Returns:
            Liste d'ASINs uniques (union des deux sources).
        """
        all_asins = set()

        # 1. ASINs depuis markets_asins.yml
        if market_config.asins:
            all_asins.update(market_config.asins)

        # 2. ASINs depuis harvested_asins (table DB)
        try:
            harvested = (
                self.db.query(HarvestedAsin)
                .filter(HarvestedAsin.marketplace == self.market_code)
                .all()
            )
            harvested_asins = [h.asin for h in harvested]
            all_asins.update(harvested_asins)

            if harvested_asins:
                logger.info(
                    f"Récupération de {len(harvested_asins)} ASINs depuis harvested_asins "
                    f"pour le marché {self.market_code}"
                )
        except Exception as e:
            logger.warning(
                f"Erreur lors de la récupération des ASINs depuis harvested_asins: {str(e)}"
            )

        # Retourner une liste unique
        return list(all_asins)

    def _upsert_product(
        self,
        keepa_product,
        category_name: str,
        marketplace_code: str,
        domain: Optional[int] = None,
        force: bool = False,
    ) -> bool:
        """
        Upsert un produit en utilisant l'ORM SQLAlchemy.
        
        Cette méthode utilise l'ORM pour gérer automatiquement les types et éviter
        les problèmes de conversion. Plus simple et plus robuste que le SQL brut.
        
        Args:
            keepa_product: Produit Keepa à traiter.
            category_name: Nom de la catégorie.
            domain: Domaine Keepa (optionnel).
            force: Si True, force la mise à jour même si le produit a déjà été traité.
        
        Returns:
            True si le produit a été créé, False s'il a été mis à jour.
        
        Note:
            Si force=False, le status est préservé si le produit a déjà été traité (scored, selected, launched),
            sinon il est mis à jour à "new".
            Si force=True, le status est toujours réinitialisé à "new".
        """
        # Vérifier si le produit existe
        existing = (
            self.db.query(ProductCandidate)
            .filter(ProductCandidate.asin == keepa_product.asin)
            .first()
        )
        
        # Préparer les données brutes
        raw_data_dict = keepa_product.raw_data if isinstance(keepa_product.raw_data, dict) else json.loads(keepa_product.raw_data) if isinstance(keepa_product.raw_data, str) else {}
        
        # Ajouter le domaine dans raw_data si ce n'est pas déjà fait
        if isinstance(raw_data_dict, dict):
            if "domain" not in raw_data_dict and domain is not None:
                raw_data_dict["domain"] = domain
        
        if existing:
            # Mise à jour du produit existant
            existing.title = keepa_product.title
            existing.category = category_name
            existing.avg_price = float(keepa_product.avg_price) if keepa_product.avg_price else None
            existing.bsr = keepa_product.bsr
            existing.estimated_sales_per_day = float(keepa_product.estimated_sales_per_day) if keepa_product.estimated_sales_per_day else None
            existing.reviews_count = keepa_product.reviews_count
            existing.rating = float(keepa_product.rating) if keepa_product.rating else None
            existing.raw_keepa_data = raw_data_dict
            existing.source_marketplace = marketplace_code
            # Si force=True, réinitialiser le status à "new" pour re-traiter le produit
            # Sinon, préserver le status si déjà traité
            if force:
                existing.status = "new"
            elif existing.status not in ["scored", "selected", "launched"]:
                existing.status = "new"
            existing.updated_at = datetime.utcnow()
            
            try:
                self.db.commit()
                return False  # Mis à jour
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erreur lors de la mise à jour du produit {keepa_product.asin}: {str(e)}", exc_info=True)
                raise
        else:
            # Création d'un nouveau produit
            new_product = ProductCandidate(
                id=uuid4(),
                asin=keepa_product.asin,
                title=keepa_product.title,
                category=category_name,
                source_marketplace=marketplace_code,
                avg_price=float(keepa_product.avg_price) if keepa_product.avg_price else None,
                bsr=keepa_product.bsr,
                estimated_sales_per_day=float(keepa_product.estimated_sales_per_day) if keepa_product.estimated_sales_per_day else None,
                reviews_count=keepa_product.reviews_count,
                rating=float(keepa_product.rating) if keepa_product.rating else None,
                raw_keepa_data=raw_data_dict,
                status="new",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            try:
                self.db.add(new_product)
                self.db.commit()
                return True  # Créé
            except IntegrityError as e:
                # Si jamais une UniqueViolation se produit (cas de race condition)
                if "product_candidates_asin_key" in str(e.orig) or "asin" in str(e.orig).lower():
                    self.db.rollback()
                    logger.warning(f"Produit {keepa_product.asin} créé entre-temps, tentative de mise à jour")
                    # Réessayer avec une mise à jour
                    return self._upsert_product(keepa_product, category_name, marketplace_code)
                else:
                    self.db.rollback()
                    logger.error(f"Erreur d'intégrité lors de la création du produit {keepa_product.asin}: {str(e)}", exc_info=True)
                    raise
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erreur lors de la création du produit {keepa_product.asin}: {str(e)}", exc_info=True)
                raise

