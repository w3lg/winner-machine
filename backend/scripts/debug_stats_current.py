#!/usr/bin/env python3
"""Script pour analyser stats.current en détail."""
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

print(f"🔍 Analyse stats.current pour {asin}")
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
    stats = product.get("stats", {})
    
    current = stats.get("current")
    print(f"\n📊 stats.current:")
    print(f"   Type: {type(current)}")
    print(f"   Valeur: {current}")
    
    if isinstance(current, list):
        print(f"   Longueur: {len(current)}")
        for i, val in enumerate(current):
            if val and val > 0:
                eur = val / 100
                print(f"   [{i}]: {val} centimes = {eur} EUR")
    elif isinstance(current, dict):
        print(f"   Clés: {list(current.keys())}")
        for key, val in current.items():
            if val and val > 0:
                eur = val / 100 if val > 100 else val
                print(f"   {key}: {val} ({eur} EUR)")
    
    print("\n💰 Recherche du prix 208.81 EUR (20881 centimes):")
    if isinstance(current, list):
        for i, val in enumerate(current):
            if val == 20881 or abs(val - 20881) < 100:  # Proche de 20881
                print(f"   ✅ Trouvé à current[{i}]: {val} centimes = {val/100} EUR")
    
    print("\n" + "=" * 80)

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

