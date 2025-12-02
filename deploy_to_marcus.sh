#!/bin/bash
# ============================================
# Script de déploiement sur le serveur marcus
# ============================================
#
# MODE D'EMPLOI :
#   1. Ce script doit être exécuté DEPUIS VOTRE MACHINE LOCALE
#   2. Il se connecte au serveur marcus et effectue le déploiement
#   3. Assurez-vous d'avoir :
#      - SSH configuré avec accès au serveur
#      - La clé SSH dans _local_config/ssh_keys/ssh_key
#      - Git configuré sur le serveur
#
# USAGE :
#   ./deploy_to_marcus.sh
#
# ============================================

set -e  # Arrêter en cas d'erreur

# Configuration
SERVER_USER="root"
SERVER_IP="135.181.253.60"
SSH_KEY="_local_config/ssh_keys/ssh_key"
SERVER_PATH="/root/winner-machine"
GIT_REPO="https://github.com/w3lg/winner-machine.git"

echo "🚀 Déploiement de Winner Machine v1 sur marcus"
echo "================================================"
echo ""

# Vérifier que la clé SSH existe
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Erreur: Clé SSH non trouvée: $SSH_KEY"
    exit 1
fi

# Fonction pour exécuter une commande sur le serveur
ssh_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
}

echo "📋 Étape 1: Vérification de la connexion SSH..."
if ssh_exec "echo 'Connexion OK'" > /dev/null 2>&1; then
    echo "✅ Connexion SSH réussie"
else
    echo "❌ Impossible de se connecter au serveur"
    exit 1
fi

echo ""
echo "📋 Étape 2: Vérification/création du répertoire..."
if ssh_exec "[ -d $SERVER_PATH ]"; then
    echo "✅ Répertoire existe déjà: $SERVER_PATH"
    echo "   Mise à jour du code (git pull)..."
    ssh_exec "cd $SERVER_PATH && git pull origin main"
else
    echo "📦 Clone du repository..."
    ssh_exec "mkdir -p $(dirname $SERVER_PATH) && cd $(dirname $SERVER_PATH) && git clone $GIT_REPO $(basename $SERVER_PATH)"
fi

echo ""
echo "📋 Étape 3: Configuration de l'environnement..."
if ssh_exec "[ ! -f $SERVER_PATH/infra/.env ]"; then
    echo "   Création du fichier .env depuis le template..."
    ssh_exec "cd $SERVER_PATH/infra && cp env.prod.template .env"
    echo "⚠️  IMPORTANT: Vous devez maintenant éditer $SERVER_PATH/infra/.env"
    echo "   avec les vraies valeurs (mots de passe, clés API, etc.)"
    echo ""
    echo "   Commandes à exécuter sur le serveur:"
    echo "   ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP"
    echo "   nano $SERVER_PATH/infra/.env"
    echo ""
    read -p "Appuyez sur Entrée une fois le .env configuré..."
else
    echo "✅ Fichier .env existe déjà"
fi

echo ""
echo "📋 Étape 4: Arrêt des services existants..."
ssh_exec "cd $SERVER_PATH/infra && docker-compose down || true"

echo ""
echo "📋 Étape 5: Pull des images Docker..."
ssh_exec "cd $SERVER_PATH/infra && docker-compose pull"

echo ""
echo "📋 Étape 6: Démarrage des services..."
ssh_exec "cd $SERVER_PATH/infra && docker-compose up -d"

echo ""
echo "⏳ Attente que les services soient prêts (15 secondes)..."
sleep 15

echo ""
echo "📋 Étape 7: Application des migrations de base de données..."
ssh_exec "cd $SERVER_PATH/infra && docker-compose exec -T app alembic upgrade head"

echo ""
echo "📋 Étape 8: Vérification des services..."
echo "   Vérification du health check..."
if ssh_exec "curl -f http://localhost:8000/health > /dev/null 2>&1"; then
    echo "✅ Backend répond correctement"
else
    echo "⚠️  Le backend ne répond pas encore. Vérifiez les logs:"
    echo "   docker-compose logs app"
fi

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Vérifier les logs: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd $SERVER_PATH/infra && docker-compose logs'"
echo "   2. Configurer nginx (voir docs/DEPLOIEMENT_MARCUS.md)"
echo "   3. Configurer les certificats Let's Encrypt"
echo "   4. Tester: curl https://marcus.w3lg.fr/health"
echo ""
echo "🌐 Services disponibles:"
echo "   - Backend: http://$SERVER_IP:8000 (en interne)"
echo "   - n8n: http://$SERVER_IP:5678 (en interne)"
echo ""

