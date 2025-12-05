"""
Routes API pour l'interface UI de contrôle (Dashboard).

Permet de lancer les jobs via une interface web simple.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.jobs.discover_job import DiscoverJob
from app.jobs.sourcing_job import SourcingJob
from app.jobs.scoring_job import ScoringJob
from app.jobs.listing_job import ListingJob
from app.jobs.asin_harvest_job import AsinHarvestJob
from app.services.market_config import get_market_config_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["ui"])

# Templates Jinja2 - chemin relatif depuis le dossier app
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/ui", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Affiche le dashboard de contrôle des jobs.

    Interface web simple avec des boutons pour déclencher les jobs.
    """
    # Charger les marchés disponibles pour le sélecteur
    market_service = get_market_config_service()
    markets = market_service.get_all_markets()
    
    markets_list = [
        {
            "code": code,
            "label": config.label,
            "active": config.active,
            "asin_count": len(config.asins),
        }
        for code, config in markets.items()
    ]
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "markets": markets_list,
        },
    )


class RunJobRequest(BaseModel):
    """Requête pour lancer un job."""
    market: Optional[str] = None  # Code du marché pour le job discover
    force: Optional[bool] = False  # Si True, force le recalcul pour tous les produits


@router.post("/ui/run/{job_name}")
async def run_job(
    job_name: str,
    request: Optional[RunJobRequest] = Body(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Lance un job par son nom.

    Args:
        job_name: Nom du job à lancer :
            - "discover" → Module A
            - "sourcing" → Module B
            - "scoring" → Module C
            - "listing" → Module D/E
            - "pipeline_abcde" → Pipeline complet A→B→C→D/E
        db: Session de base de données.

    Returns:
        Résultat JSON du job exécuté.
    """
    valid_jobs = {"discover", "sourcing", "scoring", "listing", "pipeline_abcde"}
    
    if job_name not in valid_jobs:
        return {
            "success": False,
            "error": f"Job '{job_name}' non reconnu. Jobs disponibles: {', '.join(valid_jobs)}",
        }

    try:
        if job_name == "pipeline_abcde":
            # Enchaîner les 4 jobs dans l'ordre
            results = []
            jobs_order = ["discover", "sourcing", "scoring", "listing"]
            
            for step_name in jobs_order:
                logger.info(f"Exécution du job: {step_name}")
                try:
                    # Pour le job discover, passer le paramètre market
                    market_code = request.market if request and step_name == "discover" else None
                    # Pour discover, sourcing et scoring, passer force si demandé
                    force = request.force if request and step_name in ["discover", "sourcing", "scoring"] else False
                    result = await _run_single_job(step_name, db, market_code=market_code, force=force)
                    results.append({
                        "step": step_name,
                        "result": result,
                        "status_code": 200 if result.get("success") else 500,
                    })
                    
                    # Si un job échoue, arrêter la chaîne
                    if not result.get("success", False):
                        logger.error(f"Job {step_name} a échoué, arrêt de la chaîne")
                        break
                except Exception as step_error:
                    logger.error(f"Erreur lors de l'exécution du job {step_name}: {str(step_error)}", exc_info=True)
                    results.append({
                        "step": step_name,
                        "result": {
                            "success": False,
                            "error": str(step_error),
                        },
                        "status_code": 500,
                    })
                    break
            
            # Déterminer le succès global
            all_success = all(r.get("result", {}).get("success", False) for r in results)
            
            return {
                "success": all_success,
                "message": "Pipeline complet exécuté" if all_success else "Pipeline interrompu",
                "steps": results,
            }
        else:
            # Job simple
            logger.info(f"Exécution du job: {job_name}")
            market_code = request.market if request and job_name == "discover" else None
            force = request.force if request else False
            result = await _run_single_job(job_name, db, market_code=market_code, force=force)
            return result

    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du job {job_name}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Erreur lors de l'exécution: {str(e)}",
            "job_name": job_name,
        }


async def _run_single_job(
    job_name: str,
    db: Session,
    market_code: Optional[str] = None,
    force: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Exécute un job unique en appelant directement la classe Job.
    
    Args:
        job_name: Nom du job à exécuter.
        db: Session de base de données.
        market_code: Code du marché (pour le job discover uniquement).
    
    Returns:
        Résultat du job sous forme de dictionnaire.
    """
    try:
        if job_name == "discover":
            job = DiscoverJob(db, market_code=market_code or "amazon_fr")
            stats = job.run(force=force)
            return {
                "success": True,
                "job_name": job_name,
                "message": "Job de découverte terminé avec succès",
                "stats": stats,
            }
        elif job_name == "sourcing":
            job = SourcingJob(db)
            stats = job.run(force=force)
            return {
                "success": True,
                "job_name": job_name,
                "message": "Job de sourcing terminé avec succès",
                "stats": stats,
            }
        elif job_name == "scoring":
            job = ScoringJob(db)
            stats = job.run(force=force)
            return {
                "success": True,
                "job_name": job_name,
                "message": "Job de scoring terminé avec succès",
                "stats": stats,
            }
        elif job_name == "listing":
            job = ListingJob(db)
            stats = job.run()
            return {
                "success": True,
                "job_name": job_name,
                "message": "Job de génération de listings terminé avec succès",
                "stats": stats,
            }
        else:
            return {
                "success": False,
                "error": f"Job '{job_name}' non reconnu",
            }
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du job {job_name}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "job_name": job_name,
            "error": f"Erreur lors de l'exécution du job: {str(e)}",
        }

