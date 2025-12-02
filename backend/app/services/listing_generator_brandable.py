"""
Service de génération de listings brandables (Module D).

Génère des templates de listings pour des produits brandables
avec une marque et un contenu personnalisé.
"""
import logging
from typing import Optional, List, Dict

from app.core.config import get_settings
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.listing_template import ListingTemplate

logger = logging.getLogger(__name__)


class ListingGeneratorBrandable:
    """Générateur de listings pour produits brandables."""

    def __init__(self):
        """Initialise le générateur."""
        self.settings = get_settings()

    def generate(
        self,
        candidate: ProductCandidate,
        option: SourcingOption,
    ) -> ListingTemplate:
        """
        Génère un ListingTemplate pour un produit brandable.

        Args:
            candidate: Produit candidat.
            option: Option de sourcing (doit être brandable).

        Returns:
            ListingTemplate créé (non persisté).
        """
        logger.debug(f"Génération de listing brandable pour {candidate.asin}")

        # Récupérer le nom de marque (config ou placeholder)
        brand_name = self.settings.DEFAULT_BRAND_NAME

        # Générer le titre brandable
        title = self._generate_title(candidate, brand_name)

        # Générer les bullet points
        bullets = self._generate_bullets(candidate, brand_name)

        # Générer la description
        description = self._generate_description(candidate, brand_name)

        # Générer la FAQ
        faq = self._generate_faq()

        # Générer les search terms
        search_terms = self._generate_search_terms(candidate, brand_name)

        # Créer le ListingTemplate
        listing_template = ListingTemplate(
            product_candidate_id=candidate.id,
            sourcing_option_id=option.id,
            brandable=True,
            brand_name=brand_name,
            strategy="brand_new",
            title=title,
            bullets=bullets,
            description=description,
            search_terms=search_terms,
            faq=faq,
            status="draft",
            marketplace="amazon_fr",
        )

        logger.debug(f"Listing brandable généré pour {candidate.asin} avec marque {brand_name}")
        return listing_template

    def _generate_title(self, candidate: ProductCandidate, brand_name: str) -> str:
        """Génère un titre brandable pour le produit."""
        # Extraire des mots-clés du titre existant
        base_title = candidate.title or "Produit Premium"
        
        # Simplifier et créer un titre brandable
        # Format: [BRAND] + caractéristiques principales + type
        words = base_title.split()[:8]  # Prendre les premiers mots significatifs
        
        # Construire le titre
        title_parts = [brand_name]
        title_parts.extend(words)
        
        title = " ".join(title_parts)
        
        # Limiter à 200 caractères (limite Amazon)
        if len(title) > 200:
            title = title[:197] + "..."
        
        return title

    def _generate_bullets(self, candidate: ProductCandidate, brand_name: str) -> List[str]:
        """Génère 4-5 bullet points standards pour un produit brandable."""
        bullets = []

        # Bullet 1 : Marque et qualité
        bullets.append(f"Marque {brand_name} - Qualité premium garantie")

        # Bullet 2 : Caractéristiques principales
        if candidate.title:
            # Extraire une caractéristique du titre
            words = candidate.title.split()
            if len(words) > 0:
                bullets.append(f"Caractéristiques : {words[0]} professionnel")
            else:
                bullets.append("Design professionnel et soigné")
        else:
            bullets.append("Design professionnel et soigné")

        # Bullet 3 : Usage et bénéfices
        if candidate.category:
            bullets.append(f"Idéal pour {candidate.category.lower()}")
        else:
            bullets.append("Idéal pour un usage quotidien")

        # Bullet 4 : Garantie et service
        bullets.append("Garantie satisfaction client - Support réactif")

        # Bullet 5 : Livraison
        bullets.append("Livraison rapide et sécurisée en France")

        # Limiter à 5 bullets (limite Amazon)
        return bullets[:5]

    def _generate_description(self, candidate: ProductCandidate, brand_name: str) -> str:
        """Génère une description plus longue pour un produit brandable."""
        description_parts = []

        # Introduction avec la marque
        description_parts.append(f"Présentation du produit {brand_name}")
        description_parts.append("\n\n")

        # Description du produit
        if candidate.title:
            description_parts.append(f"{candidate.title}")
        else:
            description_parts.append("Produit de qualité professionnelle")

        description_parts.append("\n\n")

        # Section caractéristiques
        description_parts.append("Caractéristiques principales :")
        description_parts.append("\n")
        description_parts.append("• Qualité premium et matériaux soignés")
        description_parts.append("\n")
        description_parts.append("• Design moderne et fonctionnel")
        description_parts.append("\n")
        description_parts.append("• Testé et validé pour la qualité")

        description_parts.append("\n\n")

        # Section garantie
        description_parts.append("Garantie et service client :")
        description_parts.append("\n")
        description_parts.append("Nous garantissons la qualité de nos produits. ")
        description_parts.append("En cas de problème, notre service client est à votre disposition.")

        description_parts.append("\n\n")

        # Catégorie si disponible
        if candidate.category:
            description_parts.append(f"Catégorie : {candidate.category}")

        description = "".join(description_parts)

        # Limiter à 2000 caractères (limite Amazon)
        if len(description) > 2000:
            description = description[:1997] + "..."

        return description

    def _generate_faq(self) -> List[Dict[str, str]]:
        """Génère 2-3 questions/réponses fréquentes."""
        faq = [
            {
                "question": "Le produit est-il garanti ?",
                "answer": "Oui, tous nos produits sont garantis. En cas de problème, notre service client vous accompagne."
            },
            {
                "question": "Quels sont les délais de livraison ?",
                "answer": "La livraison est rapide et sécurisée. Les délais varient selon votre localisation et la méthode de livraison choisie."
            },
            {
                "question": "Puis-je retourner le produit si je ne suis pas satisfait ?",
                "answer": "Oui, nous acceptons les retours sous certaines conditions. Contactez notre service client pour plus d'informations."
            }
        ]

        return faq[:3]  # Limiter à 3 Q/R

    def _generate_search_terms(self, candidate: ProductCandidate, brand_name: str) -> str:
        """Génère les mots-clés de recherche pour un produit brandable."""
        terms = []

        # Ajouter le nom de la marque
        terms.append(brand_name.lower())

        # Extraire des mots du titre
        if candidate.title:
            words = [w.lower() for w in candidate.title.split() if len(w) > 3]
            terms.extend(words[:8])

        # Ajouter la catégorie
        if candidate.category:
            terms.append(candidate.category.lower())

        # Ajouter des termes génériques
        terms.extend(["qualité", "premium", "professionnel"])

        # Joindre avec des espaces
        return " ".join(terms[:20])  # Limite Amazon: ~250 caractères total

