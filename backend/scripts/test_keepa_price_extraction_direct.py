#!/usr/bin/env python3
"""Script pour tester directement l'extraction du prix depuis Keepa."""
import sys
from pathlib import Path
from decimal import Decimal

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
from app.services.keepa_client import KeepaClient
from app.services.category_config import CategoryConfig

settings = get_settings()
client = KeepaClient()

asin = "B0CGQ3H5XF"
domain = 1

print(f"Test extraction prix pour {asin}")
print("=" * 80)

products = client.get_products_by_asins(domain=domain, asin_list=[asin])

if products:
    p = products[0]
    print(f"ASIN: {p.asin}")
    print(f"avg_price extrait: {p.avg_price}")
    print(f"Title: {p.title[:60]}...")
    
    # Vérifier les données brutes
    if p.raw_data:
        stats = p.raw_data.get("stats", {})
        print(f"\nStats disponibles: {list(stats.keys())[:10]}")
        print(f"buyBoxPrice dans stats: {stats.get('buyBoxPrice')}")
        print(f"avg30: {stats.get('avg30')}")
        print(f"avg90: {stats.get('avg90')}")
        print(f"avg180: {stats.get('avg180')}")
        
        print(f"\nbuyBoxSellerIdHistory: {p.raw_data.get('buyBoxSellerIdHistory')}")
        print(f"buyBoxPrice dans product: {p.raw_data.get('buyBoxPrice')}")
        print(f"currentPrices: {p.raw_data.get('currentPrices')}")
else:
    print("Aucun produit retourné")

