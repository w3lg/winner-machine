"""
Script de test pour extraire le prix depuis la réponse Keepa API.

Keepa stocke les prix dans un array CSV encodé. Ce script teste comment
extraire le prix actuel depuis cette structure.
"""
import sys
import json
import requests
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings

settings = get_settings()
api_key = settings.KEEPA_API_KEY

def test_keepa_price_extraction():
    """Test l'extraction du prix depuis une réponse Keepa."""
    
    asin = "B0CGQ3H5XF"
    domain = 1  # Amazon FR
    
    url = "https://api.keepa.com/product"
    params = {
        "key": api_key,
        "domain": domain,
        "asin": asin,
    }
    
    print(f"Test extraction prix pour ASIN: {asin}")
    print("=" * 80)
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "products" not in data or not data["products"]:
            print("❌ Aucun produit dans la réponse")
            return
        
        product = data["products"][0]
        
        print(f"\n✅ Produit trouvé: {product.get('asin')}")
        print(f"   Titre: {product.get('title', 'N/A')[:60]}...")
        
        # Vérifier les clés disponibles
        print(f"\n📋 Clés disponibles dans la réponse:")
        for key in sorted(product.keys()):
            if key not in ['csv', 'buyBoxSellerIdHistory']:  # Trop long
                print(f"   - {key}")
        
        # Vérifier stats
        stats = product.get("stats")
        print(f"\n📊 STATS:")
        if stats:
            print(f"   Type: {type(stats)}")
            if isinstance(stats, dict):
                print(f"   Clés: {list(stats.keys())[:20]}")
                print(f"   current: {stats.get('current')}")
                print(f"   avg90: {stats.get('avg90')}")
                print(f"   avg180: {stats.get('avg180')}")
                print(f"   min: {stats.get('min')}")
                print(f"   max: {stats.get('max')}")
        else:
            print("   ❌ Pas de stats")
        
        # Vérifier CSV
        csv_data = product.get("csv", [])
        print(f"\n📦 CSV ARRAY:")
        print(f"   Nombre d'arrays: {len(csv_data)}")
        if csv_data:
            last_array = csv_data[-1]
            print(f"   Dernier array length: {len(last_array)}")
            print(f"   Dernières valeurs: {last_array[-10:]}")
            
            # Keepa encode les prix dans le CSV
            # Format: [timestamp1, price1, timestamp2, price2, ...]
            # Les prix sont en centimes
            
            # Prendre les 2 dernières valeurs (timestamp, prix)
            if len(last_array) >= 2:
                last_price = last_array[-1]
                if last_price > 0:  # -1 = pas de prix
                    price_eur = last_price / 100.0
                    print(f"   ✅ Prix extrait du CSV: {price_eur} EUR ({last_price} centimes)")
        
        # Vérifier autres champs de prix
        print(f"\n💰 AUTRES CHAMPS DE PRIX:")
        for key in ["price", "currentPrice", "listPrice", "buyBoxPrice"]:
            if key in product:
                print(f"   {key}: {product[key]}")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_keepa_price_extraction()

