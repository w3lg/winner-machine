"""
Job de génération de listings - Modules D/E.

Génère des templates de listings pour tous les produits candidats
avec status="selected" qui n'ont pas encore de listing.
"""
import logging
from typing import Dict

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.product_candidate import ProductCandidate
from app.models.listing_template import ListingTemplate
from app.services.listing_service import ListingService

logger = logging.getLogger(__name__)


class ListingJob:
    """Job pour générer des listings pour les produits sélectionnés."""

    def __init__(self, db: Session):
        """
        Initialise le job.

        Args:
            db: Session SQLAlchemy pour la base de données.
        """
        self.db = db
        self.listing_service = ListingService(db)

    def run(self) -> Dict[str, int]:
        """
        Lance le job de génération de listings.

        Traite tous les ProductCandidate avec status="selected"
        qui n'ont pas encore de ListingTemplate.

        Returns:
            Dictionnaire avec les statistiques :
            - products_processed: nombre de produits traités
            - listings_created: nombre de listings créés
            - products_without_sourcing_or_listing: produits sans option de sourcing ou sans listing généré
        """
        logger.info("=== Démarrage du job de génération de listings ===")

        # Récupérer les produits candidats éligibles
        candidates = self._get_eligible_candidates()

        if not candidates:
            logger.warning("Aucun produit candidat éligible pour la génération de listings.")
            return {
                "products_processed": 0,
                "listings_created": 0,
                "products_without_sourcing_or_listing": 0,
            }

        logger.info(f"Nombre de produits candidats à traiter: {len(candidates)}")

        stats = {
            "products_processed": 0,
            "listings_created": 0,
            "products_without_sourcing_or_listing": 0,
        }

        for candidate in candidates:
            try:
                logger.debug(f"Traitement du produit: {candidate.asin} (ID: {candidate.id})")

                # Générer le listing
                listing_template = self.listing_service.generate_listing_for_candidate(candidate)

                if not listing_template:
                    logger.debug(
                        f"Aucun listing généré pour {candidate.asin} "
                        "(aucune option de sourcing disponible)"
                    )
                    stats["products_without_sourcing_or_listing"] += 1
                else:
                    # Persister le listing en base
                    self.db.add(listing_template)
                    stats["listings_created"] += 1
                    logger.debug(
                        f"Listing créé pour {candidate.asin} "
                        f"(brandable={listing_template.brandable})"
                    )

                stats["products_processed"] += 1

            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement du produit {candidate.asin}: {str(e)}",
                    exc_info=True,
                )
                stats["products_processed"] += 1
                continue

        try:
            self.db.commit()
            logger.info("=== Job de génération de listings terminé avec succès ===")
            logger.info(
                f"Statistiques: {stats['products_processed']} produits traités, "
                f"{stats['listings_created']} listings créés, "
                f"{stats['products_without_sourcing_or_listing']} produits sans sourcing/listing"
            )
        except Exception as e:
            logger.error(f"Erreur lors du commit en base de données: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

        return stats

    def _get_eligible_candidates(self):
        """
        Récupère les produits candidats éligibles pour la génération de listings.

        Critères :
        - status="selected"
        - Aucun ListingTemplate existant

        Returns:
            Liste des ProductCandidate éligibles.
        """
        # Récupérer tous les IDs des produits qui ont déjà un listing
        products_with_listings = (
            self.db.query(ListingTemplate.product_candidate_id)
            .distinct()
            .all()
        )
        product_ids_with_listings = {row[0] for row in products_with_listings}

        # Récupérer les produits avec status="selected"
        all_selected = (
            self.db.query(ProductCandidate)
            .filter(ProductCandidate.status == "selected")
            .all()
        )

        # Filtrer ceux qui n'ont pas encore de listing
        eligible_candidates = [
            candidate
            for candidate in all_selected
            if candidate.id not in product_ids_with_listings
        ]

        return eligible_candidates

