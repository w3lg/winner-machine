#!/bin/bash
# Script pour copier les fichiers Module D/E sur marcus

SERVER_USER="root"
SERVER_IP="135.181.253.60"
SSH_KEY="_local_config/ssh_keys/ssh_key"
SERVER_PATH="/root/winner-machine"

echo "🚀 Copie des fichiers Module D/E sur marcus..."
echo "=============================================="
echo ""

# Fonction pour copier un fichier
copy_file() {
    local local_file=$1
    local remote_file=$2
    echo "📋 Copie: $local_file -> $remote_file"
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$local_file" "$SERVER_USER@$SERVER_IP:$remote_file"
    if [ $? -eq 0 ]; then
        echo "✅ Copié avec succès"
    else
        echo "❌ Erreur lors de la copie"
        exit 1
    fi
}

# 1. Modèles
echo "📦 Copie des modèles..."
copy_file "backend/app/models/listing_template.py" "$SERVER_PATH/backend/app/models/listing_template.py"
copy_file "backend/app/models/bundle.py" "$SERVER_PATH/backend/app/models/bundle.py"

# 2. Migration
echo ""
echo "📦 Copie de la migration..."
copy_file "backend/alembic/versions/004_listing_template_and_bundle.py" "$SERVER_PATH/backend/alembic/versions/004_listing_template_and_bundle.py"

# 3. Services
echo ""
echo "📦 Copie des services..."
copy_file "backend/app/services/listing_generator_brandable.py" "$SERVER_PATH/backend/app/services/listing_generator_brandable.py"
copy_file "backend/app/services/listing_generator_non_brandable.py" "$SERVER_PATH/backend/app/services/listing_generator_non_brandable.py"
copy_file "backend/app/services/listing_service.py" "$SERVER_PATH/backend/app/services/listing_service.py"

# 4. Jobs
echo ""
echo "📦 Copie des jobs..."
copy_file "backend/app/jobs/listing_job.py" "$SERVER_PATH/backend/app/jobs/listing_job.py"

# 5. Routes API
echo ""
echo "📦 Copie des routes API..."
copy_file "backend/app/api/routes_listings.py" "$SERVER_PATH/backend/app/api/routes_listings.py"
copy_file "backend/app/api/routes_export.py" "$SERVER_PATH/backend/app/api/routes_export.py"

# 6. Fichiers modifiés
echo ""
echo "📦 Mise à jour des fichiers modifiés..."

# Lire le contenu de __init__.py et le copier
cat > /tmp/models_init.py << 'EOF'
"""Initialisation des modèles SQLAlchemy."""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Importer tous les modèles pour qu'ils soient enregistrés avec Alembic
from app.models.product_candidate import ProductCandidate  # noqa: E402
from app.models.sourcing_option import SourcingOption  # noqa: E402
from app.models.product_score import ProductScore  # noqa: E402
from app.models.listing_template import ListingTemplate  # noqa: E402
from app.models.bundle import Bundle  # noqa: E402

__all__ = ["Base", "ProductCandidate", "SourcingOption", "ProductScore", "ListingTemplate", "Bundle"]
EOF
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no /tmp/models_init.py "$SERVER_USER@$SERVER_IP:$SERVER_PATH/backend/app/models/__init__.py"
rm /tmp/models_init.py

echo ""
echo "✅ Tous les fichiers ont été copiés avec succès !"
echo ""
echo "Prochaines étapes:"
echo "1. Rebuild container: docker compose build app"
echo "2. Migration: docker compose exec app alembic upgrade head"
echo "3. Restart: docker compose restart app"

