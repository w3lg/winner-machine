"""
Routes API pour le Module B : Sourcing.

Endpoints pour lancer le sourcing et récupérer les options de sourcing.
"""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.jobs.sourcing_job import SourcingJob
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["sourcing"])


# Modèles Pydantic pour les réponses
class SourcingStats(BaseModel):
    """Statistiques détaillées du job de sourcing."""

    processed_products: int = Field(description="Nombre de produits traités")
    options_created: int = Field(description="Nombre d'options créées")
    products_without_options: int = Field(description="Nombre de produits sans options trouvées")


class SourcingJobResponse(BaseModel):
    """Réponse de l'endpoint de sourcing job."""

    success: bool = Field(description="Indique si le job s'est terminé avec succès")
    message: str = Field(description="Message descriptif du résultat")
    stats: SourcingStats = Field(description="Statistiques détaillées de l'exécution")


class SourcingOptionResponse(BaseModel):
    """Réponse pour une option de sourcing."""

    id: UUID
    supplier_name: str
    sourcing_type: str
    unit_cost: float | None
    shipping_cost_unit: float | None
    moq: int | None
    lead_time_days: int | None
    brandable: bool
    bundle_capable: bool
    notes: str | None

    class Config:
        from_attributes = True


@router.post(
    "/jobs/sourcing/run",
    response_model=SourcingJobResponse,
    summary="Lancer le job de sourcing",
    description="""
    Lance le job de sourcing pour trouver des options d'approvisionnement.

    **Fonctionnalités :**
    - Trouve les produits candidats sans options de sourcing
    - Matche ces produits avec les catalogues des fournisseurs
    - Crée les options de sourcing en base de données

    **Fréquence recommandée :**
    - À lancer après chaque job de découverte (Module A)
    - Ou sur demande manuelle

    **Retourne :**
    - Statistiques détaillées (produits traités, options créées, produits sans options)
    - Message de succès ou d'erreur
    """,
)
async def run_sourcing_job(db: Session = Depends(get_db)) -> SourcingJobResponse:
    """
    Lance le job de sourcing.

    Trouve les produits candidats sans options de sourcing et crée
    des options en les matchant avec les catalogues des fournisseurs.
    """
    logger.info("Démarrage du job de sourcing via l'endpoint API")
    try:
        job = SourcingJob(db)
        stats = job.run()

        response = SourcingJobResponse(
            success=True,
            message="Job de sourcing terminé avec succès",
            stats=SourcingStats(
                processed_products=stats.get("processed_products", 0),
                options_created=stats.get("options_created", 0),
                products_without_options=stats.get("products_without_options", 0),
            ),
        )

        logger.info(
            f"Job terminé: {response.stats.processed_products} produits traités, "
            f"{response.stats.options_created} options créées"
        )

        return response
    except Exception as e:
        logger.error(
            f"Erreur lors de l'exécution du job de sourcing: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution du job de sourcing: {str(e)}",
        )


@router.get(
    "/products/{product_id}/sourcing_options",
    response_model=List[SourcingOptionResponse],
    summary="Récupérer les options de sourcing d'un produit",
    description="""
    Récupère toutes les options de sourcing disponibles pour un produit candidat.

    **Retourne :**
    - Liste des options de sourcing avec leurs détails (fournisseur, coûts, délais, etc.)
    - Liste vide si aucune option trouvée

    **Erreurs :**
    - 404 si le produit candidat n'existe pas
    """,
)
async def get_product_sourcing_options(
    product_id: UUID = Path(..., description="ID du produit candidat"),
    db: Session = Depends(get_db),
) -> List[SourcingOptionResponse]:
    """
    Récupère les options de sourcing pour un produit candidat.

    Args:
        product_id: UUID du ProductCandidate.
        db: Session de base de données.

    Returns:
        Liste des options de sourcing pour ce produit.
    """
    # Vérifier que le produit existe
    candidate = db.query(ProductCandidate).filter(ProductCandidate.id == product_id).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Produit candidat avec l'ID {product_id} non trouvé",
        )

    # Récupérer les options de sourcing
    options = (
        db.query(SourcingOption)
        .filter(SourcingOption.product_candidate_id == product_id)
        .all()
    )

    logger.debug(f"Récupération de {len(options)} option(s) pour le produit {product_id}")

    # Convertir en modèles Pydantic
    return [SourcingOptionResponse.model_validate(option) for option in options]

