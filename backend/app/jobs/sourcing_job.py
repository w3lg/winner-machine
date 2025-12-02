"""
Job de sourcing - Module B.

Trouve et crée des options de sourcing pour les produits candidats.
"""
import logging
from typing import Dict

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.services.sourcing_matcher import SourcingMatcher

logger = logging.getLogger(__name__)


class SourcingJob:
    """Job pour trouver et créer des options de sourcing pour les produits candidats."""

    def __init__(self, db: Session):
        """
        Initialise le job.

        Args:
            db: Session SQLAlchemy pour la base de données.
        """
        self.db = db
        self.sourcing_matcher = SourcingMatcher()

    def run(self) -> Dict[str, int]:
        """
        Lance le job de sourcing.

        Traite les ProductCandidate qui n'ont pas encore d'options de sourcing,
        trouve des options via le SourcingMatcher, et les persiste en base.

        Returns:
            Dictionnaire avec les statistiques :
            - processed_products: nombre de produits traités
            - options_created: nombre d'options créées
            - products_without_options: nombre de produits sans aucune option trouvée
        """
        logger.info("=== Démarrage du job de sourcing ===")

        # Récupérer les produits candidats éligibles (sans options de sourcing)
        candidates = self._get_eligible_candidates()

        if not candidates:
            logger.warning("Aucun produit candidat éligible pour le sourcing. Le job ne fera rien.")
            return {
                "processed_products": 0,
                "options_created": 0,
                "products_without_options": 0,
            }

        logger.info(f"Nombre de produits candidats à traiter: {len(candidates)}")

        stats = {
            "processed_products": 0,
            "options_created": 0,
            "products_without_options": 0,
        }

        for candidate in candidates:
            try:
                logger.debug(f"Traitement du produit: {candidate.asin} (ID: {candidate.id})")

                # Trouver les options de sourcing
                options = self.sourcing_matcher.find_sourcing_options_for_candidate(candidate)

                if not options:
                    logger.debug(f"Aucune option de sourcing trouvée pour {candidate.asin}")
                    stats["products_without_options"] += 1
                else:
                    # Persister les options en base
                    for option in options:
                        self.db.add(option)
                        stats["options_created"] += 1

                    logger.debug(
                        f"Création de {len(options)} option(s) pour {candidate.asin}"
                    )

                stats["processed_products"] += 1

            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement du produit {candidate.asin}: {str(e)}",
                    exc_info=True,
                )
                # Continue avec le produit suivant
                stats["processed_products"] += 1

        try:
            self.db.commit()
            logger.info("=== Job de sourcing terminé avec succès ===")
            logger.info(
                f"Statistiques: {stats['processed_products']} produits traités, "
                f"{stats['options_created']} options créées, "
                f"{stats['products_without_options']} produits sans options"
            )
        except Exception as e:
            logger.error(f"Erreur lors du commit en base de données: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

        return stats

    def _get_eligible_candidates(self):
        """
        Récupère les produits candidats éligibles pour le sourcing.

        Stratégie V1 : produits qui n'ont encore AUCUNE option de sourcing.

        Returns:
            Liste des ProductCandidate éligibles.
        """
        # Récupérer tous les IDs des produits qui ont déjà des options
        products_with_options = (
            self.db.query(SourcingOption.product_candidate_id)
            .distinct()
            .all()
        )
        product_ids_with_options = {row[0] for row in products_with_options}

        # Récupérer tous les produits candidats
        all_candidates = self.db.query(ProductCandidate).all()

        # Filtrer ceux qui n'ont pas d'options
        eligible_candidates = [
            candidate
            for candidate in all_candidates
            if candidate.id not in product_ids_with_options
        ]

        return eligible_candidates

