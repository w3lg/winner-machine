#!/bin/bash
# Script de test complet du pipeline A→B→C→D/E

SERVER="root@135.181.253.60"
SSH_KEY="_local_config/ssh_keys/ssh_key"

echo "🚀 TEST COMPLET DU PIPELINE A→B→C→D/E"
echo "======================================"
echo ""

# Fonction pour exécuter une commande SSH
ssh_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER" "$1"
}

echo "1️⃣  MODULE A : DISCOVER"
echo "----------------------"
RESULT_A=$(ssh_exec 'curl -s -X POST http://localhost:8000/api/v1/jobs/discover/run')
echo "$RESULT_A" | python3 -m json.tool 2>/dev/null || echo "$RESULT_A"
echo ""

echo "2️⃣  MODULE B : SOURCING"
echo "----------------------"
RESULT_B=$(ssh_exec 'curl -s -X POST http://localhost:8000/api/v1/jobs/sourcing/run')
echo "$RESULT_B" | python3 -m json.tool 2>/dev/null || echo "$RESULT_B"
echo ""

echo "3️⃣  MODULE C : SCORING"
echo "----------------------"
RESULT_C=$(ssh_exec 'curl -s -X POST http://localhost:8000/api/v1/jobs/scoring/run')
echo "$RESULT_C" | python3 -m json.tool 2>/dev/null || echo "$RESULT_C"
echo ""

echo "4️⃣  MODULE D/E : LISTINGS"
echo "----------------------"
RESULT_D=$(ssh_exec 'curl -s -X POST http://localhost:8000/api/v1/jobs/listing/generate_for_selected')
echo "$RESULT_D" | python3 -m json.tool 2>/dev/null || echo "$RESULT_D"
echo ""

echo "5️⃣  VÉRIFICATION DES DONNÉES"
echo "----------------------"
echo "Nombre de produits candidats:"
ssh_exec 'cd /root/winner-machine/infra && docker compose exec -T db psql -U winner_machine -d winner_machine -t -c "SELECT COUNT(*) FROM product_candidates;"'

echo "Nombre de produits 'selected':"
ssh_exec 'cd /root/winner-machine/infra && docker compose exec -T db psql -U winner_machine -d winner_machine -t -c "SELECT COUNT(*) FROM product_candidates WHERE status = '\''selected'\'';"'

echo "Nombre de SourcingOption:"
ssh_exec 'cd /root/winner-machine/infra && docker compose exec -T db psql -U winner_machine -d winner_machine -t -c "SELECT COUNT(*) FROM sourcing_options;"'

echo "Nombre de ProductScore:"
ssh_exec 'cd /root/winner-machine/infra && docker compose exec -T db psql -U winner_machine -d winner_machine -t -c "SELECT COUNT(*) FROM product_scores;"'

echo "Nombre de ListingTemplate:"
ssh_exec 'cd /root/winner-machine/infra && docker compose exec -T db psql -U winner_machine -d winner_machine -t -c "SELECT COUNT(*) FROM listing_templates;"'

echo ""
echo "✅ Test terminé !"

