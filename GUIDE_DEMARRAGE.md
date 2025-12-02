# 🚀 Guide de démarrage - Winner Machine v1

## 📋 Prérequis

- Docker et Docker Compose installés
- Accès au serveur marcus (pour le déploiement production)
- Python 3.11+ (optionnel, pour développement local)

## 🏃 Démarrage rapide avec Docker

### 1. Configuration de l'environnement

Créez un fichier `.env` dans le dossier `infra/` :

```bash
cd infra
cp .env.example .env
# Éditez .env avec vos valeurs
```

Ou utilisez les valeurs par défaut (développement uniquement).

### 2. Démarrer les services

```bash
cd infra
docker-compose up -d
```

Cela démarre :
- **PostgreSQL** sur le port 5432
- **Backend FastAPI** sur le port 8000
- **n8n** sur le port 5678

### 3. Vérifier que les services sont démarrés

```bash
docker-compose ps
```

Vous devriez voir 3 services avec le statut "Up".

### 4. Appliquer les migrations de base de données

```bash
# Entrer dans le container de l'app
docker-compose exec app bash

# Appliquer les migrations
alembic upgrade head

# Ou depuis l'extérieur
docker-compose exec app alembic upgrade head
```

### 5. Vérifier que tout fonctionne

```bash
# Health check
curl http://localhost:8000/health

# Réponse attendue :
# {"status":"ok"}

# Documentation API
open http://localhost:8000/docs
```

### 6. Tester le Module A - Discoverer

```bash
# Lancer le job de découverte
curl -X POST http://localhost:8000/api/v1/jobs/discover/run

# Réponse attendue :
# {
#   "success": true,
#   "message": "Job de découverte terminé avec succès",
#   "stats": {
#     "created": 5,
#     "updated": 0,
#     "total_processed": 5
#   }
# }
```

### 7. Vérifier les données en base

```bash
# Entrer dans le container de la DB
docker-compose exec db psql -U winner_machine -d winner_machine

# Dans psql :
SELECT asin, title, category, bsr, status FROM product_candidates LIMIT 10;
\q
```

## 🧪 Tests

### Lancer les tests unitaires

```bash
# Depuis le container
docker-compose exec app pytest tests/test_discover.py -v

# Ou avec couverture
docker-compose exec app pytest tests/ --cov=app --cov-report=html
```

## 📊 Logs

### Voir les logs des services

```bash
# Logs de tous les services
docker-compose logs -f

# Logs de l'app uniquement
docker-compose logs -f app

# Logs de la DB
docker-compose logs -f db

# Logs de n8n
docker-compose logs -f n8n
```

## 🔧 Commandes utiles

### Redémarrer un service

```bash
docker-compose restart app
```

### Arrêter tous les services

```bash
docker-compose down
```

### Arrêter et supprimer les volumes (⚠️ supprime les données)

```bash
docker-compose down -v
```

### Reconstruire l'image de l'app

```bash
docker-compose build app
docker-compose up -d app
```

## 🌐 Accès aux services

Une fois démarrés :

- **Backend API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Health check** : http://localhost:8000/health
- **n8n** : http://localhost:5678

## 📝 Workflow n8n pour Module A

### Configurer un cron job pour la découverte automatique

1. Accéder à n8n : http://localhost:5678
2. Créer un nouveau workflow
3. Ajouter un nœud "Cron" :
   - Expression : `0 2 * * *` (tous les jours à 2h du matin)
4. Ajouter un nœud "HTTP Request" :
   - Method : POST
   - URL : `http://app:8000/api/v1/jobs/discover/run`
   - Authentication : None (pour l'instant)
5. Sauvegarder et activer le workflow

## 🔍 Dépannage

### Le service app ne démarre pas

```bash
# Voir les logs
docker-compose logs app

# Vérifier que la DB est prête
docker-compose ps db
```

### Erreur de connexion à la base de données

```bash
# Vérifier que le service db est démarré
docker-compose ps db

# Vérifier les variables d'environnement
docker-compose exec app env | grep POSTGRES
```

### Les migrations échouent

```bash
# Vérifier la connexion
docker-compose exec app python -c "from app.core.config import get_settings; print(get_settings().DATABASE_URL)"

# Vérifier que la DB existe
docker-compose exec db psql -U winner_machine -l
```

## 🚀 Déploiement sur le serveur marcus

### Configuration PROD sur marcus

Pour déployer en production sur le serveur marcus :

1. **Utiliser le script de déploiement automatique** (recommandé) :
   ```bash
   ./deploy_to_marcus.sh
   ```

2. **Ou déployer manuellement** (voir `docs/DEPLOIEMENT_MARCUS.md` pour le guide complet) :

   ```bash
   # Se connecter au serveur
   ssh -i _local_config/ssh_keys/ssh_key root@135.181.253.60
   
   # Cloner le repo
   git clone https://github.com/w3lg/winner-machine.git
   cd winner-machine
   
   # Configurer l'environnement PROD
   cd infra
   cp env.prod.template .env
   nano .env  # Éditer avec les vraies valeurs (mots de passe, clés API, etc.)
   
   # Démarrer les services
   docker-compose up -d
   
   # Appliquer les migrations
   docker-compose exec app alembic upgrade head
   
   # Configurer nginx et Let's Encrypt (voir docs/DEPLOIEMENT_MARCUS.md)
   ```

**📖 Documentation complète** : Voir `docs/DEPLOIEMENT_MARCUS.md` pour :
- Prérequis serveur
- Configuration `.env` production
- Configuration nginx + certificats SSL
- Vérifications post-déploiement

## 📚 Documentation

- **Architecture** : `docs/architecture_v1.md`
- **Module A implémenté** : `MODULE_A_IMPLEMENTE.md`
- **Backend README** : `backend/README.md`

---

*Dernière mise à jour : 02/12/2025*

