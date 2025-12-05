"""
Routes API pour le module ASIN Harvester.

Endpoints pour récolter des ASINs depuis Apify.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.jobs.asin_harvest_job import AsinHarvestJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["asin-harvest"])


class AsinHarvestStats(BaseModel):
    """Statistiques détaillées du job de récolte d'ASINs."""

    harvested_total: int = Field(description="Nombre total d'ASINs récoltés depuis Apify")
    inserted_new: int = Field(description="Nombre d'ASINs nouvellement insérés")
    duplicates: int = Field(description="Nombre d'ASINs déjà existants (doublons ignorés)")


class AsinHarvestResponse(BaseModel):
    """Réponse de l'endpoint de récolte d'ASINs."""

    success: bool = Field(description="Indique si le job s'est terminé avec succès")
    message: str = Field(description="Message descriptif du résultat")
    stats: AsinHarvestStats = Field(description="Statistiques détaillées de l'exécution")


@router.post(
    "/jobs/asin_harvest/run",
    response_model=AsinHarvestResponse,
    summary="Lancer le job de récolte d'ASINs",
    description="""
    Lance le job de récolte d'ASINs depuis Apify et les stocke dans la table harvested_asins.

    **Fonctionnalités :**
    - Récupère des ASINs depuis Apify (Best Sellers, Movers & Shakers, etc.)
    - Stocke les ASINs dans la table harvested_asins
    - Ignore les doublons (ASINs déjà présents)
    - Gère les erreurs sans interrompre le processus global

    **Paramètres :**
    - `market` (optionnel) : Code du marché (ex: "amazon_fr", "amazon_de")
      - Par défaut : "amazon_fr"
    - `source` (optionnel) : Source de récolte (ex: "apify_bestsellers", "apify_movers")
      - Par défaut : "apify_bestsellers"
    - `limit` (optionnel) : Nombre maximum d'ASINs à récolter
      - Par défaut : 500

    **Fréquence recommandée :**
    - En production : 1 fois par jour ou selon besoin
    - Les ASINs récoltés seront ensuite enrichis via le job Discover

    **Retourne :**
    - Statistiques détaillées (récoltés, nouveaux, doublons)
    - Message de succès ou d'erreur
    """,
)
async def run_asin_harvest_job(
    market: Optional[str] = Query(
        default="amazon_fr",
        description="Code du marché (ex: amazon_fr, amazon_de)",
    ),
    source: Optional[str] = Query(
        default="apify_bestsellers",
        description="Source de récolte (apify_bestsellers, scraper_bestsellers, scraper_search, etc.)",
    ),
    keyword: Optional[str] = Query(
        default=None,
        description="Mot-clé de recherche (pour scraper_search uniquement)",
    ),
    limit: Optional[int] = Query(
        default=500,
        ge=1,
        le=10000,
        description="Nombre maximum d'ASINs à récolter (1-10000)",
    ),
    db: Session = Depends(get_db),
) -> AsinHarvestResponse:
    """
    Lance le job de récolte d'ASINs depuis Apify.

    Récupère des ASINs depuis Apify selon la source spécifiée et les stocke
    dans la table harvested_asins (en ignorant les doublons).
    """
    logger.info(
        f"Démarrage du job de récolte d'ASINs via l'endpoint API: market={market}, source={source}, limit={limit}"
    )
    try:
        job = AsinHarvestJob(db)
        stats = job.run(market=market, source=source, limit=limit)

        response = AsinHarvestResponse(
            success=True,
            message=f"Job de récolte d'ASINs terminé avec succès: {stats['inserted_new']} nouveaux ASINs ajoutés",
            stats=AsinHarvestStats(
                harvested_total=stats.get("harvested_total", 0),
                inserted_new=stats.get("inserted_new", 0),
                duplicates=stats.get("duplicates_ignored", 0),
            ),
        )

        logger.info(
            f"Job terminé: {response.stats.harvested_total} récoltés, "
            f"{response.stats.inserted_new} nouveaux, "
            f"{response.stats.duplicates} doublons"
        )

        return response
    except Exception as e:
        logger.error(
            f"Erreur lors de l'exécution du job de récolte d'ASINs: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution du job de récolte d'ASINs: {str(e)}",
        )

