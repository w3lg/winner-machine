#!/bin/bash
# Script de démarrage pour Winner Machine v1

set -e

echo "🚀 Démarrage de Winner Machine v1"
echo ""

# Vérifier que docker-compose est disponible
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose n'est pas installé"
    exit 1
fi

# Aller dans le dossier infra
cd infra

echo "📋 Configuration de l'environnement..."
if [ ! -f .env ]; then
    echo "   Création du fichier .env depuis .env.example..."
    cp .env.example .env 2>/dev/null || echo "   ⚠️  .env.example non trouvé, utilisez les valeurs par défaut"
else
    echo "   ✅ Fichier .env existe déjà"
fi

echo ""
echo "🐳 Démarrage des services Docker..."
docker-compose up -d

echo ""
echo "⏳ Attente que les services soient prêts..."
sleep 5

echo ""
echo "🗄️  Application des migrations de base de données..."
docker-compose exec -T app alembic upgrade head || {
    echo "   ⚠️  Les migrations ont peut-être déjà été appliquées"
}

echo ""
echo "✅ Services démarrés !"
echo ""
echo "🌐 Accès aux services :"
echo "   - Backend API : http://localhost:8000"
echo "   - Documentation : http://localhost:8000/docs"
echo "   - Health check : http://localhost:8000/health"
echo "   - n8n : http://localhost:5678"
echo ""
echo "📝 Pour voir les logs :"
echo "   docker-compose logs -f"
echo ""
echo "🧪 Tester le Module A :"
echo "   curl -X POST http://localhost:8000/api/v1/jobs/discover/run"

