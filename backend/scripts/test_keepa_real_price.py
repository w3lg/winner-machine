"""
Script pour tester l'extraction réelle du prix depuis Keepa API.

Ce script appelle directement l'API Keepa et analyse la structure
de la réponse pour extraire le prix correctement.
"""
import sys
from pathlib import Path
import json

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
import httpx
from decimal import Decimal

settings = get_settings()
api_key = settings.KEEPA_API_KEY

def test_keepa_price_extraction():
    """Test l'extraction du prix depuis Keepa."""
    
    asin = "B0CGQ3H5XF"
    domain = 1  # Amazon FR
    
    print(f"🔍 Test extraction prix Keepa pour ASIN: {asin}")
    print("=" * 80)
    
    url = "https://api.keepa.com/product"
    params = {
        "key": api_key,
        "domain": domain,
        "asin": asin,
        "stats": 180,
    }
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        if not data.get("products"):
            print("❌ Aucun produit dans la réponse")
            return
        
        product = data["products"][0]
        
        print(f"\n✅ Produit trouvé: {product.get('asin')}")
        print(f"   Titre: {product.get('title', 'N/A')[:60]}...")
        
        # Vérifier stats
        stats = product.get("stats", {})
        print(f"\n📊 STATS:")
        if isinstance(stats, dict) and stats:
            print(f"   Type: dict avec {len(stats)} clés")
            print(f"   Clés disponibles: {list(stats.keys())[:20]}")
            
            # Chercher les prix dans stats
            for key in ["current", "avg", "avg90", "avg180", "min", "max", "price", "last", "lastPrice"]:
                if key in stats:
                    val = stats[key]
                    if isinstance(val, (int, float)) and val > 0:
                        price_eur = Decimal(str(val)) / Decimal("100") if val > 100 else Decimal(str(val))
                        print(f"   ✅ {key}: {val} → {price_eur} EUR (si centimes: {val/100})")
                    elif isinstance(val, dict):
                        print(f"   {key}: {val}")
                    else:
                        print(f"   {key}: {val}")
        else:
            print("   ❌ Pas de stats ou stats vide")
        
        # Vérifier CSV arrays
        csv_arrays = product.get("csv", [])
        print(f"\n📦 CSV ARRAYS:")
        print(f"   Nombre d'arrays: {len(csv_arrays)}")
        
        if csv_arrays and len(csv_arrays) > 0:
            # Array 0 = Amazon price history
            amazon_price_array = csv_arrays[0]
            print(f"   Array 0 length: {len(amazon_price_array)}")
            print(f"   Premières valeurs: {amazon_price_array[:10]}")
            print(f"   Dernières valeurs: {amazon_price_array[-10:]}")
            
            # Analyser la structure
            if len(amazon_price_array) >= 2:
                # Format possible: [timestamp, price, timestamp, price, ...]
                # Chercher le dernier prix valide
                last_valid_price = None
                for i in range(len(amazon_price_array) - 1, -1, -1):
                    val = amazon_price_array[i]
                    if val and val > 0 and val < 1000000:  # Raisonnable pour un prix en centimes
                        # Vérifier si c'est un prix (pas un timestamp)
                        # Les timestamps Keepa sont des minutes depuis 2000-01-01
                        # Donc très grands (millions)
                        if val < 100000:  # Probablement un prix en centimes
                            price_cents = val
                            price_eur = Decimal(str(price_cents)) / Decimal("100")
                            print(f"\n   ✅ Dernier prix trouvé (index {i}): {price_cents} centimes = {price_eur} EUR")
                            last_valid_price = price_eur
                            break
                
                if not last_valid_price:
                    print("   ⚠️ Aucun prix valide trouvé dans le CSV array")
        
        # Vérifier autres champs possibles
        print(f"\n💰 AUTRES CHAMPS DE PRIX:")
        for key in ["listPrice", "buyBoxPrice", "currentPrice", "price", "lastPrice", "priceNew", "priceUsed"]:
            if key in product:
                val = product[key]
                if isinstance(val, (int, float)) and val > 0:
                    price_eur = Decimal(str(val)) / Decimal("100") if val > 100 else Decimal(str(val))
                    print(f"   {key}: {val} → {price_eur} EUR")
                elif isinstance(val, list) and val:
                    print(f"   {key}: {val[:5]}...")
                else:
                    print(f"   {key}: {val}")
        
        # Sauvegarder la réponse complète pour analyse
        print(f"\n💾 Structure complète sauvegardée dans /tmp/keepa_response.json")
        with open("/tmp/keepa_response.json", "w") as f:
            json.dump(product, f, indent=2, default=str)
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_keepa_price_extraction()

