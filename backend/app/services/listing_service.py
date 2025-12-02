"""
Service de génération de listings (Modules D/E).

Orchestre la génération de listings brandables ou non-brandables
pour les produits candidats.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore
from app.models.listing_template import ListingTemplate
from app.services.listing_generator_brandable import ListingGeneratorBrandable
from app.services.listing_generator_non_brandable import ListingGeneratorNonBrandable

logger = logging.getLogger(__name__)


class ListingService:
    """Service pour générer des listings de produits."""

    def __init__(self, db: Session):
        """
        Initialise le service.

        Args:
            db: Session SQLAlchemy pour la base de données.
        """
        self.db = db
        self.generator_brandable = ListingGeneratorBrandable()
        self.generator_non_brandable = ListingGeneratorNonBrandable()

    def generate_listing_for_candidate(
        self, candidate: ProductCandidate
    ) -> Optional[ListingTemplate]:
        """
        Génère un listing pour un produit candidat.

        Trouve la meilleure option de sourcing associée et génère
        un listing brandable ou non-brandable selon l'option.

        Args:
            candidate: Produit candidat.

        Returns:
            ListingTemplate créé (non persisté) ou None si aucune option trouvée.
        """
        logger.debug(f"Génération de listing pour {candidate.asin}")

        # Trouver la meilleure option de sourcing
        option = self._find_best_sourcing_option(candidate)

        if not option:
            logger.warning(f"Aucune option de sourcing trouvée pour {candidate.asin}")
            return None

        logger.debug(
            f"Option de sourcing trouvée: {option.supplier_name} "
            f"(brandable={option.brandable})"
        )

        # Générer le listing selon le type (brandable ou non)
        if option.brandable:
            listing_template = self.generator_brandable.generate(candidate, option)
        else:
            listing_template = self.generator_non_brandable.generate(candidate, option)

        logger.debug(f"Listing généré pour {candidate.asin} (brandable={listing_template.brandable})")
        return listing_template

    def _find_best_sourcing_option(
        self, candidate: ProductCandidate
    ) -> Optional[SourcingOption]:
        """
        Trouve la meilleure option de sourcing pour un produit candidat.

        Priorité :
        1. Option avec un score A_launch (si disponible)
        2. Première option disponible

        Args:
            candidate: Produit candidat.

        Returns:
            Meilleure SourcingOption ou None si aucune trouvée.
        """
        # Récupérer toutes les options de sourcing pour ce produit
        options = (
            self.db.query(SourcingOption)
            .filter(SourcingOption.product_candidate_id == candidate.id)
            .all()
        )

        if not options:
            return None

        # Essayer de trouver une option avec un score A_launch
        for option in options:
            score = (
                self.db.query(ProductScore)
                .filter(
                    ProductScore.product_candidate_id == candidate.id,
                    ProductScore.sourcing_option_id == option.id,
                    ProductScore.decision == "A_launch",
                )
                .order_by(ProductScore.global_score.desc().nulls_last())
                .first()
            )

            if score:
                logger.debug(
                    f"Option trouvée avec score A_launch: {option.supplier_name} "
                    f"(score={score.global_score})"
                )
                return option

        # Sinon, retourner la première option disponible
        logger.debug(f"Utilisation de la première option disponible: {options[0].supplier_name}")
        return options[0]

