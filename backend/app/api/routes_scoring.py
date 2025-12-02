"""
Routes API pour le Module C : Scoring.

Endpoints pour lancer le scoring et récupérer les scores des produits.
"""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from decimal import Decimal

from app.core.database import get_db
from app.jobs.scoring_job import ScoringJob
from app.models.product_candidate import ProductCandidate
from app.models.product_score import ProductScore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scoring"])


# Modèles Pydantic pour les réponses
class ScoringStats(BaseModel):
    """Statistiques détaillées du job de scoring."""

    pairs_scored: int = Field(description="Nombre de couples (produit, option) scorés")
    products_marked_selected: int = Field(description="Nombre de produits marqués 'selected'")
    products_marked_scored: int = Field(description="Nombre de produits marqués 'scored'")
    products_marked_rejected: int = Field(description="Nombre de produits marqués 'rejected'")


class ScoringJobResponse(BaseModel):
    """Réponse de l'endpoint de scoring job."""

    success: bool = Field(description="Indique si le job s'est terminé avec succès")
    message: str = Field(description="Message descriptif du résultat")
    stats: ScoringStats = Field(description="Statistiques détaillées de l'exécution")


class ProductScoreResponse(BaseModel):
    """Réponse pour un score de produit."""

    id: UUID
    sourcing_option_id: UUID
    selling_price_target: Decimal
    amazon_fees_estimate: Decimal | None
    logistics_cost_estimate: Decimal | None
    margin_absolute: Decimal | None
    margin_percent: Decimal | None
    global_score: Decimal | None
    decision: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post(
    "/jobs/scoring/run",
    response_model=ScoringJobResponse,
    summary="Lancer le job de scoring",
    description="""
    Lance le job de scoring pour calculer les scores de rentabilité.

    **Fonctionnalités :**
    - Trouve tous les couples (ProductCandidate, SourcingOption) sans score
    - Calcule les marges, frais Amazon, et score global pour chaque couple
    - Met à jour le statut des produits selon leurs meilleures décisions :
      - `selected` si au moins un score A_launch
      - `scored` si au moins un score B_review
      - `rejected` sinon

    **Fréquence recommandée :**
    - À lancer après chaque job de sourcing (Module B)
    - Ou sur demande manuelle

    **Retourne :**
    - Statistiques détaillées (couples scorés, produits marqués selected/scored/rejected)
    - Message de succès ou d'erreur
    """,
)
async def run_scoring_job(db: Session = Depends(get_db)) -> ScoringJobResponse:
    """
    Lance le job de scoring.

    Calcule les scores de rentabilité pour tous les couples (produit, option)
    qui n'ont pas encore de score et met à jour le statut des produits.
    """
    logger.info("Démarrage du job de scoring via l'endpoint API")
    try:
        job = ScoringJob(db)
        stats = job.run()

        response = ScoringJobResponse(
            success=True,
            message="Job de scoring terminé avec succès",
            stats=ScoringStats(
                pairs_scored=stats.get("pairs_scored", 0),
                products_marked_selected=stats.get("products_marked_selected", 0),
                products_marked_scored=stats.get("products_marked_scored", 0),
                products_marked_rejected=stats.get("products_marked_rejected", 0),
            ),
        )

        logger.info(
            f"Job terminé: {response.stats.pairs_scored} couples scorés, "
            f"{response.stats.products_marked_selected} produits sélectionnés"
        )

        return response
    except Exception as e:
        logger.error(
            f"Erreur lors de l'exécution du job de scoring: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution du job de scoring: {str(e)}",
        )


@router.get(
    "/products/{product_id}/scores",
    response_model=List[ProductScoreResponse],
    summary="Récupérer les scores d'un produit",
    description="""
    Récupère tous les scores calculés pour un produit candidat.

    **Retourne :**
    - Liste des scores avec leurs détails (marges, score global, décision, etc.)
    - Liste vide si aucun score trouvé

    **Erreurs :**
    - 404 si le produit candidat n'existe pas
    """,
)
async def get_product_scores(
    product_id: UUID = Path(..., description="ID du produit candidat"),
    db: Session = Depends(get_db),
) -> List[ProductScoreResponse]:
    """
    Récupère les scores pour un produit candidat.

    Args:
        product_id: UUID du ProductCandidate.
        db: Session de base de données.

    Returns:
        Liste des scores pour ce produit.
    """
    # Vérifier que le produit existe
    candidate = db.query(ProductCandidate).filter(ProductCandidate.id == product_id).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Produit candidat avec l'ID {product_id} non trouvé",
        )

    # Récupérer les scores
    scores = (
        db.query(ProductScore)
        .filter(ProductScore.product_candidate_id == product_id)
        .order_by(ProductScore.global_score.desc().nulls_last())
        .all()
    )

    logger.debug(f"Récupération de {len(scores)} score(s) pour le produit {product_id}")

    # Convertir en modèles Pydantic
    return [ProductScoreResponse.model_validate(score) for score in scores]


@router.get(
    "/products/scores/top",
    response_model=List[ProductScoreResponse],
    summary="Récupérer les meilleurs scores",
    description="""
    Récupère les meilleurs scores filtrés par décision et triés par score global.

    **Query parameters :**
    - `decision` : Décision à filtrer (A_launch, B_review, C_drop). Défaut: A_launch
    - `limit` : Nombre maximum de résultats. Défaut: 20

    **Retourne :**
    - Liste des meilleurs scores triés par global_score DESC
    - Liste vide si aucun score ne correspond aux critères
    """,
)
async def get_top_scores(
    decision: str = Query(
        default="A_launch",
        description="Décision à filtrer (A_launch, B_review, C_drop)",
        pattern="^(A_launch|B_review|C_drop)$",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db),
) -> List[ProductScoreResponse]:
    """
    Récupère les meilleurs scores filtrés par décision.

    Args:
        decision: Décision à filtrer (A_launch, B_review, C_drop).
        limit: Nombre maximum de résultats.
        db: Session de base de données.

    Returns:
        Liste des meilleurs scores triés par global_score DESC.
    """
    # Récupérer les scores filtrés et triés
    scores = (
        db.query(ProductScore)
        .filter(ProductScore.decision == decision)
        .order_by(ProductScore.global_score.desc().nulls_last())
        .limit(limit)
        .all()
    )

    logger.debug(f"Récupération de {len(scores)} score(s) avec decision={decision}")

    # Convertir en modèles Pydantic
    return [ProductScoreResponse.model_validate(score) for score in scores]

