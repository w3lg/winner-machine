"""
Routes API pour le Dashboard - Visualisation des winners.

Endpoints pour afficher et filtrer les produits gagnants.
"""
import logging
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.product_candidate import ProductCandidate
from app.models.product_score import ProductScore
from app.models.sourcing_option import SourcingOption

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


class WinnerProductOut(BaseModel):
    """Réponse pour un produit winner."""

    product_id: UUID = Field(description="ID du produit candidat")
    asin: str = Field(description="ASIN Amazon")
    title: str | None = Field(description="Titre du produit")
    category: str | None = Field(description="Catégorie du produit")
    supplier_name: str | None = Field(description="Nom du fournisseur")
    purchase_price: Decimal | None = Field(description="Prix d'achat (unit_cost)")
    selling_price_target: Decimal = Field(description="Prix de vente cible")
    amazon_fees_estimate: Decimal | None = Field(description="Frais Amazon estimés (EUR)")
    margin_absolute: Decimal | None = Field(description="Marge absolue (EUR)")
    margin_percent: Decimal | None = Field(description="Marge en pourcentage")
    estimated_sales_per_day: Decimal | None = Field(description="Ventes estimées par jour")
    global_score: Decimal | None = Field(description="Score global")
    decision: str = Field(description="Décision: A_launch, B_review, C_drop")

    class Config:
        from_attributes = True


class WinnersResponse(BaseModel):
    """Réponse de l'endpoint winners."""

    success: bool = Field(description="Indique si la requête a réussi")
    filters: dict = Field(description="Filtres appliqués")
    items: List[WinnerProductOut] = Field(description="Liste des produits winners")
    total_count: int = Field(description="Nombre total d'items retournés")


@router.get(
    "/winners",
    response_model=WinnersResponse,
    summary="Récupérer les produits winners avec filtres",
    description="""
    Récupère la liste des produits winners (candidats avec scores) avec des filtres.
    
    Pour chaque produit, retourne le meilleur score (global_score max) si plusieurs scores existent.
    
    **Filtres disponibles :**
    - decision : A_launch, B_review, C_drop
    - min_margin_percent : marge minimum en pourcentage
    - min_global_score : score global minimum
    - min_sales_per_day : ventes par jour minimum
    - limit : nombre maximum de résultats (défaut: 50)
    """,
)
async def get_winners(
    decision: str = Query("A_launch", description="Décision à filtrer"),
    min_margin_percent: Optional[float] = Query(None, description="Marge minimum en %"),
    min_global_score: Optional[float] = Query(None, description="Score global minimum"),
    min_sales_per_day: Optional[float] = Query(None, description="Ventes par jour minimum"),
    limit: int = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db),
) -> WinnersResponse:
    """
    Récupère les produits winners avec filtres.
    
    Pour chaque produit, retourne le score avec le meilleur global_score
    si plusieurs scores existent pour ce produit.
    """
    logger.info(
        f"Récupération des winners avec filtres: decision={decision}, "
        f"min_margin_percent={min_margin_percent}, min_global_score={min_global_score}, "
        f"min_sales_per_day={min_sales_per_day}, limit={limit}"
    )

    try:
        # Requête principale avec JOINs simples
        # On récupère tous les scores, puis on garde le meilleur par produit en Python
        query = (
            db.query(
                ProductCandidate.id.label("product_id"),
                ProductCandidate.asin,
                ProductCandidate.title,
                ProductCandidate.category,
                SourcingOption.supplier_name,
                SourcingOption.unit_cost.label("purchase_price"),
                ProductScore.selling_price_target,
                ProductScore.amazon_fees_estimate,
                ProductScore.margin_absolute,
                ProductScore.margin_percent,
                ProductScore.estimated_sales_per_day,
                ProductScore.global_score,
                ProductScore.decision,
            )
            .join(ProductScore, ProductScore.product_candidate_id == ProductCandidate.id)
            .join(
                SourcingOption,
                SourcingOption.id == ProductScore.sourcing_option_id,
            )
        )

        # Appliquer les filtres
        if decision and decision.lower() not in ("tous", "all", ""):
            query = query.filter(ProductScore.decision == decision)

        if min_margin_percent is not None:
            query = query.filter(
                ProductScore.margin_percent.isnot(None),
                ProductScore.margin_percent >= min_margin_percent
            )

        if min_global_score is not None:
            query = query.filter(
                ProductScore.global_score.isnot(None),
                ProductScore.global_score >= min_global_score
            )

        if min_sales_per_day is not None:
            query = query.filter(
                ProductScore.estimated_sales_per_day.isnot(None),
                ProductScore.estimated_sales_per_day >= min_sales_per_day
            )

        # Trier par global_score décroissant, puis par margin_percent décroissant
        query = query.order_by(
            desc(ProductScore.global_score),
            desc(ProductScore.margin_percent),
        )

        # Trier par global_score décroissant, puis par margin_percent décroissant
        # Cela permet de récupérer les meilleurs scores en premier
        query = query.order_by(
            desc(ProductScore.global_score),
            desc(ProductScore.margin_percent),
        )

        # Exécuter la requête (sans limite pour l'instant, on limite après le groupement)
        results = query.all()

        # Grouper par product_id pour ne garder que le meilleur score par produit
        # Comme les résultats sont triés par global_score décroissant, le premier pour chaque produit est le meilleur
        products_map = {}
        for row in results:
            product_id = row.product_id
            if product_id not in products_map:
                products_map[product_id] = row
            # Sinon, on ignore (on garde déjà le meilleur qui est venu en premier)

        # Convertir en modèles Pydantic
        items = []
        for row in products_map.values():
            items.append(
                WinnerProductOut(
                    product_id=row.product_id,
                    asin=row.asin,
                    title=row.title,
                    category=row.category,
                    supplier_name=row.supplier_name,
                    purchase_price=row.purchase_price,
                    selling_price_target=row.selling_price_target,
                    amazon_fees_estimate=row.amazon_fees_estimate,
                    margin_absolute=row.margin_absolute,
                    margin_percent=row.margin_percent,
                    estimated_sales_per_day=row.estimated_sales_per_day,
                    global_score=row.global_score,
                    decision=row.decision,
                )
            )
        
        # Re-trier les items par global_score décroissant (après le groupement)
        items.sort(
            key=lambda x: (x.global_score or Decimal("0"), x.margin_percent or Decimal("0")),
            reverse=True
        )
        
        # Appliquer la limite après le groupement
        items = items[:limit]

        filters_applied = {
            "decision": decision,
            "min_margin_percent": min_margin_percent,
            "min_global_score": min_global_score,
            "min_sales_per_day": min_sales_per_day,
            "limit": limit,
        }

        logger.info(f"Retour de {len(items)} winners après filtres")

        return WinnersResponse(
            success=True,
            filters=filters_applied,
            items=items,
            total_count=len(items),
        )

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des winners: {str(e)}", exc_info=True)
        return WinnersResponse(
            success=False,
            filters={},
            items=[],
            total_count=0,
        )

