"""
Routes API pour le Module A : Discoverer.

Endpoints pour lancer la découverte de produits.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.jobs.discover_job import DiscoverJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["discover"])


class DiscoverStats(BaseModel):
    """Statistiques détaillées du job de découverte."""

    created: int = Field(description="Nombre de produits créés")
    updated: int = Field(description="Nombre de produits mis à jour")
    total_processed: int = Field(description="Total de produits traités")
    markets_processed: int = Field(description="Nombre de marchés traités")
    errors: int = Field(description="Nombre d'erreurs rencontrées")


class DiscoverResponse(BaseModel):
    """Réponse de l'endpoint de découverte."""

    success: bool = Field(description="Indique si le job s'est terminé avec succès")
    message: str = Field(description="Message descriptif du résultat")
    stats: DiscoverStats = Field(description="Statistiques détaillées de l'exécution")


@router.post(
    "/jobs/discover/run",
    response_model=DiscoverResponse,
    summary="Lancer le job de découverte de produits",
    description="""
    Lance le job de découverte de produits depuis l'API Keepa.

    **Fonctionnalités :**
    - Récupère les produits depuis Keepa pour un marché spécifié (par défaut: amazon_fr)
    - Utilise la liste d'ASINs configurée pour le marché dans markets_asins.yml
    - Stocke les produits en base de données (création ou mise à jour selon l'ASIN)
    - Gère les erreurs sans interrompre le processus global

    **Paramètres :**
    - `market` (optionnel) : Code du marché à traiter (ex: "amazon_fr", "amazon_de", "amazon_es")
      - Par défaut : "amazon_fr"

    **Fréquence recommandée :**
    - En production : 1 fois par jour (ex: 03:00) via n8n cron
    - En développement : sur demande manuelle

    **Statut des produits :**
    - Nouveaux produits : `status = "new"`
    - Produits existants : mise à jour des métriques sans changer le statut s'il a déjà été traité

    **Retourne :**
    - Statistiques détaillées (créés, mis à jour, traités, marchés, erreurs)
    - Message de succès ou d'erreur
    """,
)
async def run_discover_job(
    market: Optional[str] = Query(
        default="amazon_fr",
        description="Code du marché à traiter (ex: amazon_fr, amazon_de, amazon_es)",
    ),
    db: Session = Depends(get_db),
) -> DiscoverResponse:
    """
    Lance le job de découverte de produits pour un marché spécifié.

    Récupère les produits depuis Keepa en utilisant la liste d'ASINs configurée
    pour le marché et les stocke en base de données (création ou mise à jour).
    """
    logger.info(f"Démarrage du job de découverte via l'endpoint API pour le marché: {market}")
    try:
        job = DiscoverJob(db, market_code=market)
        stats = job.run()

        response = DiscoverResponse(
            success=True,
            message=f"Job de découverte terminé avec succès pour le marché {market}",
            stats=DiscoverStats(
                created=stats.get("created", 0),
                updated=stats.get("updated", 0),
                total_processed=stats.get("total_processed", 0),
                markets_processed=stats.get("markets_processed", 0),
                errors=stats.get("errors", 0),
            ),
        )

        logger.info(
            f"Job terminé: {response.stats.created} créés, "
            f"{response.stats.updated} mis à jour, "
            f"{response.stats.total_processed} traités"
        )

        return response
    except Exception as e:
        logger.error(
            f"Erreur lors de l'exécution du job de découverte: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution du job de découverte: {str(e)}",
        )

