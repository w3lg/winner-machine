"""
Job de récolte d'ASINs depuis Apify - ASIN Harvester.

Récupère des ASINs depuis Apify (Best Sellers, Movers & Shakers, etc.)
et les stocke dans la table harvested_asins.
"""
import logging
from typing import Dict, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.harvested_asin import HarvestedAsin
from app.services.apify_client import ApifyClient
from app.services.scraper_client import ScraperClient

logger = logging.getLogger(__name__)


class AsinHarvestJob:
    """Job pour récolter des ASINs depuis Apify et les stocker en base."""

    def __init__(self, db: Session):
        """
        Initialise le job.

        Args:
            db: Session SQLAlchemy pour la base de données.
        """
        self.db = db
        self.apify_client = ApifyClient()
        self.scraper_client = ScraperClient()

    def run(
        self,
        market: str = "amazon_fr",
        source: str = "apify_bestsellers",
        limit: int = 500,
    ) -> Dict[str, int]:
        """
        Lance le job de récolte d'ASINs.

        Args:
            market: Code du marché (ex: "amazon_fr").
            source: Source de récolte (ex: "apify_bestsellers", "apify_movers").
            limit: Nombre maximum d'ASINs à récolter.

        Returns:
            Dictionnaire avec les statistiques :
            - harvested_total: nombre total d'ASINs récoltés depuis Apify
            - inserted_new: nombre d'ASINs nouvellement insérés
            - duplicates_ignored: nombre d'ASINs déjà existants (doublons ignorés)
        """
        logger.info(
            f"=== Démarrage du job de récolte d'ASINs: market={market}, source={source}, limit={limit} ==="
        )

        stats = {
            "harvested_total": 0,
            "inserted_new": 0,
            "duplicates_ignored": 0,
        }

        try:
            # Récupérer les ASINs selon la source (Apify ou scraper maison)
            asins = self._fetch_asins(source=source, market=market, limit=limit)

            if not asins:
                logger.warning(
                    f"Aucun ASIN récolté pour {source} sur {market}"
                )
                return stats

            stats["harvested_total"] = len(asins)
            logger.info(f"Récupération de {len(asins)} ASINs depuis {source}")

            # Insérer les ASINs en base (ignorer les doublons)
            for asin in asins:
                try:
                    # Vérifier si l'ASIN existe déjà
                    existing = (
                        self.db.query(HarvestedAsin)
                        .filter(HarvestedAsin.asin == asin)
                        .first()
                    )

                    if existing:
                        # Mettre à jour le timestamp si nécessaire
                        if existing.marketplace != market or existing.source != source:
                            existing.marketplace = market
                            existing.source = source
                            existing.updated_at = datetime.utcnow()
                            self.db.commit()
                        stats["duplicates_ignored"] += 1
                        continue

                    # Créer un nouveau HarvestedAsin
                    new_harvested = HarvestedAsin(
                        id=uuid4(),
                        asin=asin,
                        marketplace=market,
                        source=source,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )

                    self.db.add(new_harvested)
                    self.db.commit()
                    stats["inserted_new"] += 1

                except IntegrityError as e:
                    # Si jamais une UniqueViolation se produit (race condition)
                    if "harvested_asins_asin_key" in str(e.orig) or "asin" in str(e.orig).lower():
                        self.db.rollback()
                        logger.debug(f"ASIN {asin} créé entre-temps, doublon ignoré")
                        stats["duplicates_ignored"] += 1
                    else:
                        logger.error(
                            f"Erreur d'intégrité lors de l'insertion de l'ASIN {asin}: {str(e)}",
                            exc_info=True,
                        )
                        self.db.rollback()
                except Exception as e:
                    logger.error(
                        f"Erreur lors de l'insertion de l'ASIN {asin}: {str(e)}",
                        exc_info=True,
                    )
                    self.db.rollback()
                    # Continue avec le prochain ASIN
                    continue

            logger.info("=== Job de récolte d'ASINs terminé ===")
            logger.info(
                f"Statistiques: {stats['harvested_total']} récoltés, "
                f"{stats['inserted_new']} nouveaux, "
                f"{stats['duplicates_ignored']} doublons ignorés"
            )

        except Exception as e:
            logger.error(
                f"Erreur lors de l'exécution du job de récolte: {str(e)}",
                exc_info=True,
            )
            self.db.rollback()
            raise

        return stats

    def _fetch_asins(
        self, source: str, market: str, limit: int
    ) -> list[str]:
        """
        Récupère les ASINs selon la source (Apify ou scraper maison).

        Args:
            source: Source de récolte (apify_bestsellers, scraper_bestsellers, scraper_search, etc.).
            market: Code du marché (amazon_fr, etc.).
            limit: Nombre maximum d'ASINs.

        Returns:
            Liste d'ASINs.
        """
        # Sources scraper maison
        if source == "scraper_bestsellers":
            logger.info(f"Utilisation du scraper maison pour Best Sellers {market}")
            return self.scraper_client.scrape_best_sellers_fr(limit=limit)
        elif source == "scraper_search":
            logger.warning(f"Source {source} nécessite un paramètre keyword (pas encore implémentée dans le job)")
            return []
        
        # Sources Apify (mise en pause mais code conservé)
        domain_map = {
            "amazon_fr": "FR",
            "amazon_de": "DE",
            "amazon_es": "ES",
            "amazon_it": "IT",
            "amazon_uk": "UK",
            "amazon_com": "US",
        }
        domain = domain_map.get(market, "FR")

        if source == "apify_bestsellers":
            logger.info(f"Utilisation d'Apify pour Best Sellers {market} (payant - peut échouer)")
            return self.apify_client.get_bestsellers_asins(domain=domain, limit=limit)
        elif source == "apify_movers":
            logger.warning(f"Source {source} pas encore implémentée")
            return []
        elif source == "apify_search":
            logger.warning(f"Source {source} pas encore implémentée")
            return []
        else:
            logger.warning(f"Source inconnue: {source}")
            return []

