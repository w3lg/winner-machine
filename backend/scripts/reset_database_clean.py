"""
Script pour réinitialiser complètement la base de données.

Ce script supprime toutes les données de test pour permettre de repartir
sur une base propre et tester le pipeline complet depuis zéro.
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
from app.models.product_score import ProductScore
from app.models.listing_template import ListingTemplate
from app.models.bundle import Bundle


def reset_database():
    """Supprime toutes les données de la base pour repartir sur une base propre."""
    db: Session = SessionLocal()
    
    try:
        print("🔄 Réinitialisation de la base de données...")
        print("=" * 60)
        
        # Compter les données avant suppression
        count_listings = db.query(ListingTemplate).count()
        count_bundles = db.query(Bundle).count()
        count_scores = db.query(ProductScore).count()
        count_options = db.query(SourcingOption).count()
        count_products = db.query(ProductCandidate).count()
        
        print(f"\n📊 État actuel de la base :")
        print(f"  - ProductCandidates: {count_products}")
        print(f"  - SourcingOptions: {count_options}")
        print(f"  - ProductScores: {count_scores}")
        print(f"  - ListingTemplates: {count_listings}")
        print(f"  - Bundles: {count_bundles}")
        
        # Supprimer dans l'ordre des dépendances (FK)
        print(f"\n🗑️  Suppression des données...")
        
        deleted_listings = db.query(ListingTemplate).delete()
        print(f"  ✅ {deleted_listings} ListingTemplate(s) supprimé(s)")
        
        deleted_bundles = db.query(Bundle).delete()
        print(f"  ✅ {deleted_bundles} Bundle(s) supprimé(s)")
        
        deleted_scores = db.query(ProductScore).delete()
        print(f"  ✅ {deleted_scores} ProductScore(s) supprimé(s)")
        
        deleted_options = db.query(SourcingOption).delete()
        print(f"  ✅ {deleted_options} SourcingOption(s) supprimé(s)")
        
        deleted_products = db.query(ProductCandidate).delete()
        print(f"  ✅ {deleted_products} ProductCandidate(s) supprimé(s)")
        
        # Commit toutes les suppressions
        db.commit()
        
        print(f"\n✅ Base de données réinitialisée avec succès !")
        print(f"   Toutes les données ont été supprimées.")
        print(f"\n🚀 Vous pouvez maintenant lancer le pipeline complet :")
        print(f"   1. POST /api/v1/jobs/discover/run?market=amazon_fr")
        print(f"   2. POST /api/v1/jobs/sourcing/run")
        print(f"   3. POST /api/v1/jobs/scoring/run")
        
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()

