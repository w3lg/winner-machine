"""
Routes API pour les Modules D/E : Listings.

Endpoints pour générer des listings et les exporter.
"""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.jobs.listing_job import ListingJob
from app.models.product_candidate import ProductCandidate
from app.models.listing_template import ListingTemplate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["listings"])


# Modèles Pydantic pour les réponses
class ListingStats(BaseModel):
    """Statistiques détaillées du job de génération de listings."""

    products_processed: int = Field(description="Nombre de produits traités")
    listings_created: int = Field(description="Nombre de listings créés")
    products_without_sourcing_or_listing: int = Field(
        description="Nombre de produits sans option de sourcing ou sans listing généré"
    )


class ListingJobResponse(BaseModel):
    """Réponse de l'endpoint de listing job."""

    success: bool = Field(description="Indique si le job s'est terminé avec succès")
    message: str = Field(description="Message descriptif du résultat")
    stats: ListingStats = Field(description="Statistiques détaillées de l'exécution")


class ListingTemplateOut(BaseModel):
    """Réponse pour un template de listing."""

    id: UUID
    brandable: bool
    brand_name: str | None
    title: str
    bullets: list[str] | None
    status: str
    strategy: str
    marketplace: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post(
    "/jobs/listing/generate_for_selected",
    response_model=ListingJobResponse,
    summary="Générer des listings pour les produits sélectionnés",
    description="""
    Lance le job de génération de listings pour tous les produits avec status="selected".

    **Fonctionnalités :**
    - Trouve tous les produits candidats avec status="selected" sans listing
    - Génère un listing brandable ou non-brandable selon l'option de sourcing
    - Crée les ListingTemplate en base de données avec status="draft"

    **Fréquence recommandée :**
    - À lancer après chaque job de scoring (Module C)
    - Ou sur demande manuelle

    **Retourne :**
    - Statistiques détaillées (produits traités, listings créés, produits sans sourcing)
    - Message de succès ou d'erreur
    """,
)
async def generate_listings_for_selected(db: Session = Depends(get_db)) -> ListingJobResponse:
    """
    Lance le job de génération de listings pour les produits sélectionnés.

    Génère des templates de listings (brandables ou non) pour tous les produits
    avec status="selected" qui n'ont pas encore de listing.
    """
    logger.info("Démarrage du job de génération de listings via l'endpoint API")
    try:
        job = ListingJob(db)
        stats = job.run()

        response = ListingJobResponse(
            success=True,
            message="Job de génération de listings terminé avec succès",
            stats=ListingStats(
                products_processed=stats.get("products_processed", 0),
                listings_created=stats.get("listings_created", 0),
                products_without_sourcing_or_listing=stats.get(
                    "products_without_sourcing_or_listing", 0
                ),
            ),
        )

        logger.info(
            f"Job terminé: {response.stats.products_processed} produits traités, "
            f"{response.stats.listings_created} listings créés"
        )

        return response
    except Exception as e:
        logger.error(
            f"Erreur lors de l'exécution du job de génération de listings: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution du job de génération de listings: {str(e)}",
        )


@router.get(
    "/products/{product_id}/listing_templates",
    response_model=List[ListingTemplateOut],
    summary="Récupérer les listings d'un produit",
    description="""
    Récupère tous les templates de listing pour un produit candidat.

    **Retourne :**
    - Liste des templates avec leurs détails (brandable, title, bullets, status, etc.)
    - Liste vide si aucun template trouvé

    **Erreurs :**
    - 404 si le produit candidat n'existe pas
    """,
)
async def get_product_listing_templates(
    product_id: UUID = Path(..., description="ID du produit candidat"),
    db: Session = Depends(get_db),
) -> List[ListingTemplateOut]:
    """
    Récupère les templates de listing pour un produit candidat.

    Args:
        product_id: UUID du ProductCandidate.
        db: Session de base de données.

    Returns:
        Liste des templates de listing pour ce produit.
    """
    # Vérifier que le produit existe
    candidate = db.query(ProductCandidate).filter(ProductCandidate.id == product_id).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Produit candidat avec l'ID {product_id} non trouvé",
        )

    # Récupérer les templates
    templates = (
        db.query(ListingTemplate)
        .filter(ListingTemplate.product_candidate_id == product_id)
        .order_by(ListingTemplate.created_at.desc())
        .all()
    )

    logger.debug(f"Récupération de {len(templates)} template(s) pour le produit {product_id}")

    # Convertir en modèles Pydantic
    return [ListingTemplateOut.model_validate(template) for template in templates]


@router.get(
    "/listings/top_drafts",
    response_model=List[ListingTemplateOut],
    summary="Récupérer les listings en draft pour produits sélectionnés",
    description="""
    Récupère les templates de listing en status="draft" pour des produits avec status="selected",
    triés par date de création DESC.

    **Query parameters :**
    - `limit` : Nombre maximum de résultats. Défaut: 20

    **Retourne :**
    - Liste des templates en draft pour des produits sélectionnés
    """,
)
async def get_top_draft_listings(
    limit: int = Query(default=20, ge=1, le=100, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db),
) -> List[ListingTemplateOut]:
    """
    Récupère les templates de listing en draft pour des produits sélectionnés.

    Args:
        limit: Nombre maximum de résultats.
        db: Session de base de données.

    Returns:
        Liste des templates en draft triés par date de création DESC.
    """
    # Récupérer les templates en draft pour des produits sélectionnés
    templates = (
        db.query(ListingTemplate)
        .join(ProductCandidate, ListingTemplate.product_candidate_id == ProductCandidate.id)
        .filter(
            ListingTemplate.status == "draft",
            ProductCandidate.status == "selected",
        )
        .order_by(ListingTemplate.created_at.desc())
        .limit(limit)
        .all()
    )

    logger.debug(f"Récupération de {len(templates)} template(s) en draft")

    # Convertir en modèles Pydantic
    return [ListingTemplateOut.model_validate(template) for template in templates]

