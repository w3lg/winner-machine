"""
Application principale FastAPI pour Winner Machine v1.

Point d'entrée de l'API backend.
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes_discover import router as discover_router
from app.api.routes_sourcing import router as sourcing_router
from app.api.routes_scoring import router as scoring_router
from app.api.routes_listings import router as listings_router
from app.api.routes_export import router as export_router

# Récupérer la configuration
settings = get_settings()

# Configuration du logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="Winner Machine API",
    description="API backend pour Winner Machine v1 - Recherche et commercialisation de produits gagnants",
    version="1.0.0",
    docs_url="/docs" if settings.is_debug else None,
    redoc_url="/redoc" if settings.is_debug else None,
)

logger.info(f"Application démarrée en mode: {settings.APP_ENV}")
logger.info(f"Debug mode: {settings.is_debug}, Log level: {settings.LOG_LEVEL}")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(discover_router)
app.include_router(sourcing_router)
app.include_router(scoring_router)
app.include_router(listings_router)
app.include_router(export_router)


@app.get("/health")
async def health_check():
    """
    Endpoint de health check.
    
    Utilisé pour vérifier que l'application est opérationnelle.
    """
    return {"status": "ok"}


@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "message": "Winner Machine API v1",
        "environment": settings.APP_ENV,
        "docs": "/docs" if settings.is_debug else "disabled",
        "health": "/health",
    }

