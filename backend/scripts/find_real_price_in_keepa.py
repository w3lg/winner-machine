#!/usr/bin/env python3
"""Script pour trouver où se trouve réellement le prix dans la réponse Keepa."""
import sys
from pathlib import Path
import json

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
import httpx

settings = get_settings()
api_key = settings.KEEPA_API_KEY

asin = "B0CGQ3H5XF"
domain = 1

url = "https://api.keepa.com/product"
params = {"key": api_key, "domain": domain, "asin": asin, "stats": 180}

print(f"🔍 Analyse complète de la réponse Keepa pour {asin}")
print("=" * 80)

try:
    with httpx.Client(timeout=30) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    if not data.get("products"):
        print("❌ Aucun produit")
        sys.exit(1)

    product = data["products"][0]
    
    # Sauvegarder la réponse complète
    with open("/tmp/keepa_full_response.json", "w") as f:
        json.dump(product, f, indent=2, default=str)
    print("✅ Réponse sauvegardée dans /tmp/keepa_full_response.json")
    
    # Chercher TOUS les nombres qui pourraient être un prix (entre 100 et 100000)
    def find_price_like_values(obj, path="", prices=[]):
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_path = f"{path}.{key}" if path else key
                find_price_like_values(val, new_path, prices)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]" if path else f"[{i}]"
                find_price_like_values(item, new_path, prices)
        elif isinstance(obj, (int, float)):
            # Prix probable : entre 10000 et 500000 (100€ à 5000€ en centimes)
            if 10000 <= obj <= 500000:
                prices.append((path, obj, obj/100))
    
    prices = []
    find_price_like_values(product, "", prices)
    
    print(f"\n💰 VALEURS RESSEMBLANT À DES PRIX (100€ - 5000€):")
    for path, cents, eur in sorted(prices, key=lambda x: x[2]):
        print(f"   {path}: {cents} centimes = {eur} EUR")
    
    # Vérifier spécifiquement les champs connus
    print(f"\n🔍 VÉRIFICATION DES CHAMPS SPÉCIFIQUES:")
    
    # Stats
    stats = product.get("stats", {})
    if isinstance(stats, dict):
        for key in ["buyBoxPrice", "avg30", "avg90", "avg180", "min", "max", "current"]:
            val = stats.get(key)
            if val and isinstance(val, (int, float)) and val > 0:
                print(f"   stats.{key}: {val} ({val/100 if val > 100 else val} EUR)")
    
    # Product root
    for key in ["buyBoxPrice", "listPrice", "currentPrice", "price", "lastPrice"]:
        val = product.get(key)
        if val and isinstance(val, (int, float)) and val > 0:
            print(f"   product.{key}: {val} ({val/100 if val > 100 else val} EUR)")
    
    print("\n" + "=" * 80)

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

