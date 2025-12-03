#!/usr/bin/env python3
"""Script pour vérifier le prix en base de données."""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.models.product_candidate import ProductCandidate

db = SessionLocal()
try:
    product = db.query(ProductCandidate).filter(ProductCandidate.asin == "B0CGQ3H5XF").first()
    if product:
        print(f"ASIN: {product.asin}")
        print(f"avg_price en base: {product.avg_price}")
        print(f"Title: {product.title[:60]}...")
        print(f"Status: {product.status}")
    else:
        print("Produit non trouvé")
finally:
    db.close()

