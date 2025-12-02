"""
Modèles SQLAlchemy pour Winner Machine.

Les modèles métier (ProductCandidate, SourcingOption, etc.) seront créés
progressivement lors du développement des modules.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass


# Importer tous les modèles pour qu'ils soient enregistrés avec Alembic
from app.models.product_candidate import ProductCandidate  # noqa: E402
from app.models.sourcing_option import SourcingOption  # noqa: E402
from app.models.product_score import ProductScore  # noqa: E402
from app.models.listing_template import ListingTemplate  # noqa: E402
from app.models.bundle import Bundle  # noqa: E402

__all__ = ["Base", "ProductCandidate", "SourcingOption", "ProductScore", "ListingTemplate", "Bundle"]
