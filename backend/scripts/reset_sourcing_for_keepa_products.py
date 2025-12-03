"""
Script pour réinitialiser les options de sourcing pour les produits Keepa.

Ce script supprime toutes les options de sourcing existantes pour permettre
de tester le nouveau mécanisme auto-généré.
"""
import sys
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption


def reset_sourcing_options():
    """Supprime toutes les options de sourcing pour les produits Keepa."""
    db: Session = SessionLocal()
    
    try:
        # Compter les options existantes
        total_options = db.query(SourcingOption).count()
        print(f"Nombre total d'options de sourcing en base: {total_options}")
        
        # Supprimer toutes les options de sourcing
        deleted = db.query(SourcingOption).delete()
        db.commit()
        
        print(f"✅ {deleted} option(s) de sourcing supprimée(s)")
        
        # Vérifier les produits sans options
        all_products = db.query(ProductCandidate).count()
        products_with_options = db.query(SourcingOption.product_candidate_id).distinct().count()
        products_without = all_products - products_with_options
        
        print(f"\n📊 État après suppression:")
        print(f"  - Total produits: {all_products}")
        print(f"  - Produits avec options: {products_with_options}")
        print(f"  - Produits sans options: {products_without}")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔄 Réinitialisation des options de sourcing...")
    reset_sourcing_options()
    print("\n✅ Réinitialisation terminée !")

