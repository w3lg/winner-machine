"""
Service de génération de listings non-brandables (Module E).

Génère des templates de listings pour des produits non-brandables
en se basant sur les données existantes (Keepa, produit Amazon existant).
"""
import logging
from typing import Optional, List

from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.listing_template import ListingTemplate

logger = logging.getLogger(__name__)


class ListingGeneratorNonBrandable:
    """Générateur de listings pour produits non-brandables."""

    def generate(
        self,
        candidate: ProductCandidate,
        option: Optional[SourcingOption] = None,
    ) -> ListingTemplate:
        """
        Génère un ListingTemplate pour un produit non-brandable.

        Args:
            candidate: Produit candidat.
            option: Option de sourcing (optionnel).

        Returns:
            ListingTemplate créé (non persisté).
        """
        logger.debug(f"Génération de listing non-brandable pour {candidate.asin}")

        # Récupérer le titre depuis le produit
        title = candidate.title or f"Produit {candidate.asin}"
        
        # Simplifier le titre si trop long (limite Amazon: 200 caractères)
        if len(title) > 200:
            title = title[:197] + "..."

        # Créer des bullets basiques à partir du titre et des données disponibles
        bullets = self._generate_bullets(candidate, option)

        # Description courte basée sur les données Keepa
        description = self._generate_description(candidate)

        # Search terms à partir du titre et de la catégorie
        search_terms = self._generate_search_terms(candidate)

        # Créer le ListingTemplate
        listing_template = ListingTemplate(
            product_candidate_id=candidate.id,
            sourcing_option_id=option.id if option else None,
            brandable=False,
            reference_asin=candidate.asin,
            strategy="clone_best",
            title=title,
            bullets=bullets,
            description=description,
            search_terms=search_terms,
            status="draft",
            marketplace="amazon_fr",
        )

        logger.debug(f"Listing non-brandable généré pour {candidate.asin}")
        return listing_template

    def _generate_bullets(self, candidate: ProductCandidate, option: Optional[SourcingOption]) -> List[str]:
        """Génère les bullet points à partir des données disponibles."""
        bullets = []

        # Bullet 1 : Titre simplifié ou caractéristique principale
        if candidate.title:
            # Prendre les premiers mots du titre comme caractéristique principale
            title_words = candidate.title.split()[:5]
            bullets.append(f"{' '.join(title_words)} - Qualité professionnelle")
        else:
            bullets.append("Produit de qualité professionnelle")

        # Bullet 2 : Catégorie
        if candidate.category:
            bullets.append(f"Catégorie : {candidate.category}")

        # Bullet 3 : Rating si disponible
        if candidate.rating:
            bullets.append(f"Note moyenne : {float(candidate.rating)}/5 étoiles")

        # Bullet 4 : Reviews si disponibles
        if candidate.reviews_count:
            bullets.append(f"{candidate.reviews_count} avis clients")

        # Bullet 5 : Informations additionnelles
        bullets.append("Livraison rapide et sécurisée")

        # Limiter à 5 bullets (limite Amazon)
        return bullets[:5]

    def _generate_description(self, candidate: ProductCandidate) -> str:
        """Génère une description courte basée sur les données du produit."""
        description_parts = []

        if candidate.title:
            description_parts.append(candidate.title)

        if candidate.category:
            description_parts.append(f"\n\nCatégorie : {candidate.category}")

        # Ajouter des informations depuis raw_keepa_data si disponible
        if candidate.raw_keepa_data and isinstance(candidate.raw_keepa_data, dict):
            # Extraire quelques informations pertinentes si présentes
            features = candidate.raw_keepa_data.get("features", [])
            if features and isinstance(features, list):
                description_parts.append("\n\nCaractéristiques principales :")
                for feature in features[:3]:  # Limiter à 3 features
                    if isinstance(feature, str):
                        description_parts.append(f"- {feature}")

        description_parts.append("\n\nProduit de qualité, livré rapidement et en toute sécurité.")

        description = " ".join(description_parts)
        
        # Limiter la longueur (Amazon accepte ~2000 caractères pour la description)
        if len(description) > 2000:
            description = description[:1997] + "..."

        return description

    def _generate_search_terms(self, candidate: ProductCandidate) -> str:
        """Génère les mots-clés de recherche à partir du titre et de la catégorie."""
        terms = []

        # Extraire des mots du titre
        if candidate.title:
            # Filtrer les mots vides et garder les mots significatifs
            words = [w.lower() for w in candidate.title.split() if len(w) > 3]
            terms.extend(words[:10])  # Limiter à 10 mots du titre

        # Ajouter la catégorie
        if candidate.category:
            terms.append(candidate.category.lower())

        # Joindre avec des espaces (Amazon attend les search terms séparés par des espaces)
        return " ".join(terms[:20])  # Limite Amazon: ~250 caractères total

