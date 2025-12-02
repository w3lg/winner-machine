"""
Routes API pour l'interface UI de contrôle (Dashboard).

Permet de lancer les jobs via une interface web simple.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import httpx

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
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.post("/ui/run/{job_name}")
async def run_job(job_name: str) -> Dict[str, Any]:
    """
    Lance un job par son nom.

    Args:
        job_name: Nom du job à lancer :
            - "discover" → Module A
            - "sourcing" → Module B
            - "scoring" → Module C
            - "listing" → Module D/E
            - "pipeline_abcde" → Pipeline complet A→B→C→D/E

    Returns:
        Résultat JSON du job exécuté.
    """
    base_url = "http://localhost:8000"

    job_endpoints = {
        "discover": f"{base_url}/api/v1/jobs/discover/run",
        "sourcing": f"{base_url}/api/v1/jobs/sourcing/run",
        "scoring": f"{base_url}/api/v1/jobs/scoring/run",
        "listing": f"{base_url}/api/v1/jobs/listing/generate_for_selected",
    }

    if job_name not in job_endpoints and job_name != "pipeline_abcde":
        return {
            "success": False,
            "error": f"Job '{job_name}' non reconnu. Jobs disponibles: discover, sourcing, scoring, listing, pipeline_abcde",
        }

    try:
        if job_name == "pipeline_abcde":
            # Enchaîner les 4 jobs dans l'ordre
            results = []
            
            for step_name, step_url in job_endpoints.items():
                logger.info(f"Exécution du job: {step_name}")
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(step_url)
                    result = response.json()
                    results.append({
                        "step": step_name,
                        "result": result,
                        "status_code": response.status_code,
                    })
                    
                    # Si un job échoue, arrêter la chaîne
                    if response.status_code != 200 or result.get("success") is False:
                        logger.error(f"Job {step_name} a échoué, arrêt de la chaîne")
                        break
            
            return {
                "success": True,
                "message": "Pipeline complet exécuté",
                "steps": results,
            }
        else:
            # Job simple
            endpoint = job_endpoints[job_name]
            logger.info(f"Exécution du job: {job_name} via {endpoint}")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(endpoint)
                result = response.json()
                
                return {
                    "success": response.status_code == 200,
                    "job_name": job_name,
                    "status_code": response.status_code,
                    "result": result,
                }

    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du job {job_name}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Erreur lors de l'exécution: {str(e)}",
            "job_name": job_name,
        }

