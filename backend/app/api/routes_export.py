"""
Routes API pour l'export de données.

Endpoints pour exporter les listings en CSV.
"""
import csv
import io
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.models.listing_template import ListingTemplate
from app.models.product_candidate import ProductCandidate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["export"])


class ExportRequest(BaseModel):
    """Requête pour l'export CSV de listings."""

    listing_ids: Optional[List[UUID]] = None
    export_all_drafts: bool = False


@router.post(
    "/listings/export_csv",
    summary="Exporter des listings en CSV",
    description="""
    Exporte des templates de listing en format CSV.

    **Options :**
    - Fournir une liste d'IDs de ListingTemplate dans le body
    - OU activer `export_all_drafts=true` pour exporter tous les drafts

    **Retourne :**
    - Fichier CSV avec les colonnes : asin, title, bullets, description, price_target

    **Format CSV :**
    - Colonnes séparées par des virgules
    - Bullets concaténés avec " | "
    - Encodage UTF-8 avec BOM pour Excel
    """,
    response_class=Response,
)
async def export_listings_csv(
    request: ExportRequest = Body(
        ...,
        example={"listing_ids": None, "export_all_drafts": True},
    ),
    db: Session = Depends(get_db),
) -> Response:
    """
    Exporte des templates de listing en format CSV.

    Args:
        request: Requête avec liste d'IDs ou option export_all_drafts.
        db: Session de base de données.

    Returns:
        Fichier CSV téléchargeable.
    """
    logger.info("Démarrage de l'export CSV des listings")

    try:
        # Déterminer quels listings exporter
        if request.export_all_drafts:
            # Exporter tous les drafts
            listings = (
                db.query(ListingTemplate)
                .filter(ListingTemplate.status == "draft")
                .all()
            )
            logger.info(f"Export de tous les drafts: {len(listings)} listings")
        elif request.listing_ids:
            # Exporter les listings spécifiés
            listings = (
                db.query(ListingTemplate)
                .filter(ListingTemplate.id.in_(request.listing_ids))
                .all()
            )
            logger.info(f"Export de {len(listings)} listing(s) spécifié(s)")
        else:
            raise HTTPException(
                status_code=400,
                detail="Vous devez fournir soit 'listing_ids' soit 'export_all_drafts=true'",
            )

        if not listings:
            raise HTTPException(status_code=404, detail="Aucun listing trouvé à exporter")

        # Créer le CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)

        # En-têtes
        writer.writerow(
            [
                "asin",
                "reference_asin",
                "title",
                "bullets",
                "description",
                "price_target",
                "brandable",
                "brand_name",
                "status",
                "marketplace",
            ]
        )

        # Récupérer les produits associés pour obtenir avg_price
        for listing in listings:
            candidate = (
                db.query(ProductCandidate)
                .filter(ProductCandidate.id == listing.product_candidate_id)
                .first()
            )

            # ASIN
            asin = candidate.asin if candidate else "N/A"

            # Reference ASIN
            reference_asin = listing.reference_asin or asin

            # Title
            title = listing.title

            # Bullets (concaténés avec " | ")
            bullets_str = ""
            if listing.bullets and isinstance(listing.bullets, list):
                bullets_str = " | ".join(str(b) for b in listing.bullets)

            # Description
            description = listing.description or ""

            # Price target
            price_target = ""
            if candidate and candidate.avg_price:
                price_target = str(float(candidate.avg_price))

            # Brandable
            brandable = "Oui" if listing.brandable else "Non"

            # Brand name
            brand_name = listing.brand_name or ""

            # Status
            status = listing.status

            # Marketplace
            marketplace = listing.marketplace

            writer.writerow(
                [
                    asin,
                    reference_asin,
                    title,
                    bullets_str,
                    description,
                    price_target,
                    brandable,
                    brand_name,
                    status,
                    marketplace,
                ]
            )

        # Préparer la réponse CSV
        csv_content = output.getvalue()
        output.close()

        # Encoder en UTF-8 avec BOM pour Excel
        csv_bytes = "\ufeff".encode("utf-8") + csv_content.encode("utf-8")

        logger.info(f"Export CSV terminé: {len(listings)} listing(s) exporté(s)")

        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="listings_export.csv"',
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'export CSV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'export CSV: {str(e)}",
        )

