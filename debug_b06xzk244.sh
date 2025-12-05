#!/bin/bash
# Script pour debug ASIN B06XZ9K244

echo "=== 1. Contenu de scoring_rules.yml ==="
cat /root/winner-machine/backend/app/config/scoring_rules.yml

echo ""
echo "=== 2. Relance du scoring avec force=true ==="
curl -X POST "http://localhost:8000/api/v1/jobs/scoring/run?force=true"

echo ""
echo "=== 3. Attente 5 secondes ==="
sleep 5

echo ""
echo "=== 4. Logs pour B06XZ9K244 ==="
cd /root/winner-machine/infra
docker compose logs app 2>&1 | grep -E "CHARGEMENT|DEBUG B06XZ9K244|B06XZ9K244.*DECISION" | tail -100

echo ""
echo "=== 5. Vérification DB : Nombre de ProductScore pour B06XZ9K244 ==="
docker compose exec -T app python3 << 'PYTHON'
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
conn = engine.connect()

result = conn.execute(text("""
    SELECT COUNT(*) as count 
    FROM product_scores ps 
    JOIN product_candidates pc ON ps.product_candidate_id = pc.id 
    WHERE pc.asin = 'B06XZ9K244'
"""))
count = result.fetchone()[0]
print(f"Nombre de ProductScore pour B06XZ9K244: {count}")

conn.close()
PYTHON

echo ""
echo "=== 6. Winner JSON pour B06XZ9K244 ==="
curl -s "http://localhost:8000/api/v1/dashboard/winners?limit=10" | python3 -m json.tool | grep -A 30 "B06XZ9K244"

