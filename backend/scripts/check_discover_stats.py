#!/usr/bin/env python3
"""Script temporaire pour vérifier les stats de découverte."""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore

db = SessionLocal()

try:
    product_count = db.query(ProductCandidate).count()
    print(f"📦 Produits candidats: {product_count}")
    
    # Compter par catégorie
    by_category = {}
    for product in db.query(ProductCandidate).all():
        cat = product.category or "Unknown"
        by_category[cat] = by_category.get(cat, 0) + 1
    
    print(f"\n📊 Par catégorie:")
    for cat, count in sorted(by_category.items()):
        print(f"  - {cat}: {count}")
    
    # Exemple de produit
    sample = db.query(ProductCandidate).filter(
        ProductCandidate.category == "Electronics & Photo"
    ).first()
    
    if sample:
        print(f"\n📋 Exemple produit (ASIN: {sample.asin}):")
        print(f"  - Titre: {sample.title}")
        print(f"  - Prix: {sample.avg_price} €")
        print(f"  - BSR: {sample.bsr}")
        print(f"  - Ventes/jour: {sample.estimated_sales_per_day}")
        print(f"  - Reviews: {sample.reviews_count}")
        print(f"  - Rating: {sample.rating}")
        print(f"  - Status: {sample.status}")
        
        # Vérifier raw_keepa_data
        if sample.raw_keepa_data:
            print(f"  - Raw data keys: {list(sample.raw_keepa_data.keys())[:10]}")
            print(f"  - Source: {sample.raw_keepa_data.get('source', 'unknown')}")
    
    sourcing_count = db.query(SourcingOption).count()
    print(f"\n🏭 Options de sourcing: {sourcing_count}")
    
    score_count = db.query(ProductScore).count()
    print(f"📊 Scores: {score_count}")
    
finally:
    db.close()

