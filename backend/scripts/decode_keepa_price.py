"""
Script pour décoder le prix depuis la réponse Keepa API.

Keepa stocke les prix dans un CSV array encodé.
Format: [timestamp1, price1, timestamp2, price2, ...]
Les prix sont en centimes.
"""
import json
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
import httpx

def decode_keepa_price():
    """Test le décodage du prix depuis Keepa."""
    
    settings = get_settings()
    api_key = settings.KEEPA_API_KEY
    
    asin = "B0CGQ3H5XF"
    domain = 1
    
    print(f"🔍 Test décodage prix Keepa pour {asin}")
    print("=" * 80)
    
    url = "https://api.keepa.com/product"
    params = {"key": api_key, "domain": domain, "asin": asin}
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        if not data.get("products"):
            print("❌ Aucun produit dans la réponse")
            return
        
        product = data["products"][0]
        
        # Vérifier stats
        stats = product.get("stats", {})
        print(f"\n📊 STATS:")
        if isinstance(stats, dict):
            print(f"   current: {stats.get('current')}")
            print(f"   avg90: {stats.get('avg90')}")
            print(f"   avg180: {stats.get('avg180')}")
            print(f"   min: {stats.get('min')}")
            print(f"   max: {stats.get('max')}")
        
        # Vérifier CSV array pour les prix Amazon
        csv_arrays = product.get("csv", [])
        print(f"\n📦 CSV ARRAYS (Keepa stocke les données historiques ici):")
        print(f"   Nombre d'arrays: {len(csv_arrays)}")
        
        # Array 0 = Amazon price history
        # Format: [timestamp1, price1, timestamp2, price2, ...]
        if csv_arrays and len(csv_arrays) > 0:
            amazon_prices = csv_arrays[0]
            print(f"   Array 0 (prix Amazon) length: {len(amazon_prices)}")
            
            if len(amazon_prices) >= 2:
                # Les valeurs sont: timestamp, prix, timestamp, prix, ...
                # Prendre la dernière paire (timestamp, prix)
                if len(amazon_prices) % 2 == 0:
                    # Format pair
                    last_price_index = len(amazon_prices) - 1
                    last_price_cents = amazon_prices[last_price_index]
                    
                    if last_price_cents > 0:  # -1 = pas de prix
                        last_price_eur = last_price_cents / 100.0
                        print(f"   ✅ Prix actuel depuis CSV: {last_price_eur} EUR ({last_price_cents} centimes)")
                    else:
                        print(f"   ⚠️ Dernier prix: {last_price_cents} (pas de prix)")
                
                # Chercher le dernier prix valide
                for i in range(len(amazon_prices) - 1, 1, -2):
                    price_cents = amazon_prices[i]
                    if price_cents > 0:
                        price_eur = price_cents / 100.0
                        timestamp = amazon_prices[i-1]
                        print(f"   Dernier prix valide: {price_eur} EUR (timestamp: {timestamp})")
                        break
        
        # Vérifier les autres champs possibles
        print(f"\n💰 AUTRES CHAMPS:")
        for key in ["title", "listPrice", "buyBoxPrice", "currentPrice"]:
            if key in product:
                print(f"   {key}: {product[key]}")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    decode_keepa_price()

