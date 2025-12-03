"""
Script de diagnostic pour vérifier les prix et calculs.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore


def diagnostic():
    """Affiche un diagnostic des prix et calculs."""
    db: Session = SessionLocal()
    
    try:
        print("=" * 80)
        print("DIAGNOSTIC DES PRIX ET CALCULS")
        print("=" * 80)
        
        # Récupérer un produit exemple
        product = db.query(ProductCandidate).filter(
            ProductCandidate.asin == "B0CGQ3H5XF"
        ).first()
        
        if not product:
            print("❌ Produit B0CGQ3H5XF non trouvé")
            return
        
        print(f"\n📦 PRODUIT : {product.asin}")
        print(f"   Titre: {product.title[:60]}...")
        print(f"   avg_price (Keepa): {product.avg_price} EUR")
        print(f"   estimated_sales_per_day: {product.estimated_sales_per_day}")
        print(f"   BSR: {product.bsr}")
        print(f"   Status: {product.status}")
        
        # Récupérer l'option de sourcing
        option = db.query(SourcingOption).filter(
            SourcingOption.product_candidate_id == product.id
        ).first()
        
        if option:
            print(f"\n💼 SOURCING OPTION")
            print(f"   Supplier: {option.supplier_name}")
            print(f"   unit_cost: {option.unit_cost} EUR")
            print(f"   shipping_cost_unit: {option.shipping_cost_unit} EUR")
            print(f"   moq: {option.moq}")
            
        # Récupérer le score
        score = db.query(ProductScore).filter(
            ProductScore.product_candidate_id == product.id
        ).first()
        
        if score:
            print(f"\n📊 PRODUCT SCORE")
            print(f"   selling_price_target: {score.selling_price_target} EUR")
            print(f"   amazon_fees_estimate: {score.amazon_fees_estimate} EUR")
            print(f"   logistics_cost_estimate: {score.logistics_cost_estimate} EUR")
            print(f"   margin_absolute: {score.margin_absolute} EUR")
            print(f"   margin_percent: {score.margin_percent}%")
            print(f"   global_score: {score.global_score}")
            print(f"   decision: {score.decision}")
            
            # Calculs manuels pour vérifier
            print(f"\n🔍 VÉRIFICATION DES CALCULS")
            selling_price = score.selling_price_target
            unit_cost = option.unit_cost if option else 0
            amazon_fees = score.amazon_fees_estimate or 0
            logistics = score.logistics_cost_estimate or 0
            
            margin_abs = selling_price - amazon_fees - logistics - unit_cost
            margin_pct = (margin_abs / selling_price * 100) if selling_price > 0 else 0
            
            print(f"   Marge calculée: {margin_abs} EUR ({margin_pct:.2f}%)")
            print(f"   Marge enregistrée: {score.margin_absolute} EUR ({score.margin_percent}%)")
            
            if abs(float(margin_abs) - float(score.margin_absolute or 0)) > 0.01:
                print(f"   ⚠️ DIFFÉRENCE DÉTECTÉE!")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    diagnostic()

