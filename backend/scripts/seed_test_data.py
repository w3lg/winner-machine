#!/usr/bin/env python3
"""
Script de seed pour créer des données de test.

Ce script insère des données de test dans la base de données pour permettre
de tester le pipeline complet A→B→C→D/E avec des stats non nulles.

Usage:
    python backend/scripts/seed_test_data.py

OU depuis le container:
    docker compose exec app python scripts/seed_test_data.py
"""
import sys
from pathlib import Path

# Ajouter le chemin backend au PYTHONPATH
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore


def seed_test_data(db: Session):
    """Crée des données de test dans la base de données."""
    print("🌱 Démarrage du seed de données de test...")
    
    # 1. Créer quelques ProductCandidate
    print("\n📦 Création de produits candidats...")
    candidates = []
    
    test_products = [
        {
            "asin": "B00TEST001",
            "title": "Produit Test Premium - Électronique",
            "category": "Electronics & Photo",
            "avg_price": Decimal("49.99"),
            "bsr": 5000,
            "estimated_sales_per_day": Decimal("15.5"),
            "reviews_count": 1200,
            "rating": Decimal("4.5"),
            "status": "new",
        },
        {
            "asin": "B00TEST002",
            "title": "Produit Test Home & Kitchen",
            "category": "Home & Kitchen",
            "avg_price": Decimal("29.99"),
            "bsr": 8000,
            "estimated_sales_per_day": Decimal("10.2"),
            "reviews_count": 800,
            "rating": Decimal("4.2"),
            "status": "new",
        },
        {
            "asin": "B00TEST003",
            "title": "Produit Test Sports & Outdoors",
            "category": "Sports & Outdoors",
            "avg_price": Decimal("39.99"),
            "bsr": 6000,
            "estimated_sales_per_day": Decimal("12.8"),
            "reviews_count": 950,
            "rating": Decimal("4.3"),
            "status": "new",
        },
    ]
    
    for product_data in test_products:
        # Vérifier si le produit existe déjà
        existing = db.query(ProductCandidate).filter(
            ProductCandidate.asin == product_data["asin"]
        ).first()
        
        if existing:
            print(f"  ⚠️  Produit {product_data['asin']} existe déjà, ignoré")
            candidates.append(existing)
        else:
            candidate = ProductCandidate(**product_data)
            db.add(candidate)
            candidates.append(candidate)
            print(f"  ✅ Produit créé: {product_data['asin']}")
    
    db.commit()
    
    # Rafraîchir pour obtenir les IDs
    for candidate in candidates:
        db.refresh(candidate)
    
    print(f"\n✅ {len(candidates)} produits candidats créés ou existants")
    
    # 2. Créer des SourcingOption pour chaque produit
    print("\n🏭 Création d'options de sourcing...")
    options_created = 0
    
    for candidate in candidates:
        # Option 1 : Non-brandable
        option1 = SourcingOption(
            product_candidate_id=candidate.id,
            supplier_name="Demo IT Supplier",
            sourcing_type="EU_wholesale",
            unit_cost=Decimal("15.00"),
            shipping_cost_unit=Decimal("2.00"),
            moq=10,
            lead_time_days=7,
            brandable=False,
            bundle_capable=False,
        )
        db.add(option1)
        options_created += 1
        
        # Option 2 : Brandable
        option2 = SourcingOption(
            product_candidate_id=candidate.id,
            supplier_name="Demo Brandable Supplier",
            sourcing_type="import_CN",
            unit_cost=Decimal("12.00"),
            shipping_cost_unit=Decimal("1.50"),
            moq=50,
            lead_time_days=14,
            brandable=True,
            bundle_capable=True,
        )
        db.add(option2)
        options_created += 1
        
        print(f"  ✅ 2 options créées pour {candidate.asin}")
    
    db.commit()
    print(f"\n✅ {options_created} options de sourcing créées")
    
    # 3. Optionnel : Créer quelques ProductScore pour tester les listings
    print("\n📊 Création de scores de test (optionnel)...")
    scores_created = 0
    
    for candidate in candidates:
        # Récupérer les options du produit
        options = db.query(SourcingOption).filter(
            SourcingOption.product_candidate_id == candidate.id
        ).all()
        
        for option in options[:1]:  # Prendre seulement la première option
            # Vérifier si un score existe déjà
            existing_score = db.query(ProductScore).filter(
                ProductScore.product_candidate_id == candidate.id,
                ProductScore.sourcing_option_id == option.id,
            ).first()
            
            if existing_score:
                print(f"  ⚠️  Score existe déjà pour {candidate.asin}, ignoré")
                continue
            
            # Créer un score A_launch pour tester les listings
            score = ProductScore(
                product_candidate_id=candidate.id,
                sourcing_option_id=option.id,
                selling_price_target=candidate.avg_price,
                amazon_fees_estimate=Decimal("7.50"),
                logistics_cost_estimate=option.shipping_cost_unit or Decimal("2.00"),
                margin_absolute=Decimal("25.49"),
                margin_percent=Decimal("51.0"),
                estimated_sales_per_day=candidate.estimated_sales_per_day or Decimal("10.0"),
                risk_factor=Decimal("0.1"),
                global_score=Decimal("459.0"),
                decision="A_launch",
            )
            db.add(score)
            scores_created += 1
            
            # Mettre à jour le statut du produit
            candidate.status = "selected"
            print(f"  ✅ Score A_launch créé pour {candidate.asin} (status → selected)")
    
    db.commit()
    print(f"\n✅ {scores_created} scores créés")
    
    print("\n🎉 Seed terminé avec succès !")
    print("\n📊 Résumé:")
    print(f"  - Produits candidats: {len(candidates)}")
    print(f"  - Options de sourcing: {options_created}")
    print(f"  - Scores: {scores_created}")
    print(f"  - Produits 'selected': {sum(1 for c in candidates if c.status == 'selected')}")
    
    print("\n💡 Vous pouvez maintenant:")
    print("  - Lancer le job Listing pour générer des listings")
    print("  - Voir les listings via GET /api/v1/listings/top_drafts")
    print("  - Exporter les listings via POST /api/v1/listings/export_csv")


def main():
    """Point d'entrée principal."""
    db = SessionLocal()
    try:
        seed_test_data(db)
    except Exception as e:
        print(f"\n❌ Erreur lors du seed: {str(e)}", file=sys.stderr)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

