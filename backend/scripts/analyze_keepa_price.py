#!/usr/bin/env python3
"""Script pour analyser la structure de la réponse Keepa et extraire le prix."""
import json
import sys
from decimal import Decimal
import httpx

# Configuration
API_KEY = "dctu0hf0dmtoje9l4k98v8io5he2qg06q1j3tg4emabv26jb137uhv5f4i4g9c5q"
ASIN = "B0CGQ3H5XF"
DOMAIN = 1  # Amazon FR

url = "https://api.keepa.com/product"
params = {"key": API_KEY, "domain": DOMAIN, "asin": ASIN, "stats": 180}

print(f"🔍 Analyse Keepa pour ASIN: {ASIN}")
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
    print(f"\n✅ Produit: {product.get('title', 'N/A')[:60]}...")

    # Afficher TOUTES les clés du produit
    print(f"\n🔑 TOUTES LES CLÉS DU PRODUIT:")
    for key in sorted(product.keys()):
        val = product[key]
        if key not in ["csv", "categoryTree", "categoryTreeParent"]:  # Trop long
            if isinstance(val, (int, float)):
                if val > 0 and val < 1000000:
                    print(f"   {key}: {val}")
                else:
                    print(f"   {key}: {val}")
            elif isinstance(val, str) and len(val) < 100:
                print(f"   {key}: {val[:60]}...")
            elif isinstance(val, dict):
                print(f"   {key}: dict avec {len(val)} clés")
            elif isinstance(val, list):
                print(f"   {key}: list avec {len(val)} éléments")
            else:
                print(f"   {key}: {type(val).__name__}")

    # Analyser STATS
    stats = product.get("stats", {})
    print(f"\n📊 STATS:")
    if isinstance(stats, dict) and stats:
        for key in sorted(stats.keys()):
            val = stats[key]
            if isinstance(val, (int, float)):
                if key in ["current", "avg", "avg90", "avg180", "min", "max"]:
                    # Les prix Keepa sont en centimes
                    price_eur = Decimal(str(val)) / Decimal("100")
                    print(f"   {key}: {val} centimes = {price_eur} EUR")
                else:
                    print(f"   {key}: {val}")
    else:
        print("   ❌ Pas de stats")

    # Analyser CSV array
    csv_arrays = product.get("csv", [])
    print(f"\n📦 CSV ARRAY:")
    if csv_arrays and len(csv_arrays) > 0:
        amazon_array = csv_arrays[0]
        print(f"   Length: {len(amazon_array)}")
        print(f"   First 10: {amazon_array[:10]}")
        print(f"   Last 10: {amazon_array[-10:]}")
        
        # Chercher le dernier prix valide
        for i in range(len(amazon_array) - 1, -1, -1):
            val = amazon_array[i]
            # Les prix sont en centimes, donc entre 100 et 1000000 (1€ à 10000€)
            if val and val > 100 and val < 1000000:
                price_eur = Decimal(str(val)) / Decimal("100")
                print(f"\n   ✅ Prix trouvé (index {i}): {val} centimes = {price_eur} EUR")
                break
    else:
        print("   ❌ Pas de CSV array")

    print("\n" + "=" * 80)

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

