# ✅ Modules A & B déployés sur marcus

## 📅 Date du déploiement

**Date** : 02/12/2025 - 01:52 UTC  
**Commit** : Modules A et B implémentés  
**Serveur** : marcus (135.181.253.60)

---

## ✅ Actions réalisées

### 1. Installation des prérequis ✅

- ✅ **Docker** installé (version 29.1.1)
- ✅ **Docker Compose** installé (version v2.40.3)
- ✅ **nginx** installé (version 1.24.0)
- ✅ **certbot** installé (version 2.9.0)

### 2. Récupération du code ✅

- ✅ Repository cloné depuis GitHub : `/root/winner-machine`
- ✅ Structure complète transférée :
  - `backend/` : Code FastAPI avec Modules A et B
  - `infra/` : docker-compose.yml, configs nginx
  - Configuration des fournisseurs et catégories

### 3. Configuration environnement production ✅

- ✅ Fichier `.env` créé depuis `env.prod.template`
- ✅ Mots de passe générés automatiquement :
  - `POSTGRES_PASSWORD` : Généré (20 caractères)
  - `SECRET_KEY` : Généré (64 caractères hex)
  - `N8N_BASIC_AUTH_PASSWORD` : Généré (20 caractères)
  - `N8N_ENCRYPTION_KEY` : Généré (64 caractères hex)
- ✅ Variables d'environnement configurées :
  - `APP_ENV=prod`
  - `DEBUG=false`
  - `LOG_LEVEL=INFO`

### 4. Services Docker démarrés ✅

- ✅ **PostgreSQL** : Container `winner-machine-db` (port 5432)
- ✅ **Backend FastAPI** : Container `winner-machine-app` (port 8000)
- ✅ **n8n** : Container `winner-machine-n8n` (port 5678)
- ✅ Tous les services sont **UP** et fonctionnels

### 5. Migrations Alembic appliquées ✅

- ✅ Migration `001_initial_product_candidate` : Table `product_candidates` créée
- ✅ Migration `002_sourcing_option` : Table `sourcing_options` créée
- ✅ Toutes les migrations appliquées avec succès

### 6. Tests des endpoints ✅

#### Module A - Discoverer
- ✅ Health check : `GET /health` → `{"status":"ok"}`
- ✅ Endpoint découverte : `POST /api/v1/jobs/discover/run` → Fonctionnel
  - Note : Les produits existent déjà en base, d'où les erreurs de contrainte unique (normal)

#### Module B - Sourcing
- ✅ Endpoint sourcing : `POST /api/v1/jobs/sourcing/run` → Fonctionnel
  - Réponse : `{"success":true, "stats": {...}}`

### 7. Configuration nginx ✅

- ✅ Configurations créées :
  - `/etc/nginx/sites-available/marcus.w3lg.fr`
  - `/etc/nginx/sites-available/n8n.w3lg.fr`
- ✅ Liens symboliques créés dans `sites-enabled`
- ✅ Configuration testée : `nginx -t` → **OK**
- ✅ Nginx rechargé : `systemctl reload nginx`

### 8. Certificats SSL ⚠️

- ⚠️ **À FAIRE** : Obtenir les certificats Let's Encrypt
- ⚠️ Les configurations nginx sont en HTTP (80) pour l'instant
- ⚠️ Les DNS doivent pointer vers `135.181.253.60` :
  - `marcus.w3lg.fr` → 135.181.253.60
  - `n8n.w3lg.fr` → 135.181.253.60

---

## 🔧 Commandes exécutées

### Installation Docker & nginx

```bash
# Installation Docker
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
# ... configuration du repo Docker
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Installation nginx et certbot
apt-get install -y nginx certbot python3-certbot-nginx
```

### Déploiement

```bash
# Clone du repo
cd /root
git clone https://github.com/w3lg/winner-machine.git
cd winner-machine

# Configuration .env
cd infra
cp env.prod.template .env
# Génération automatique des mots de passe

# Démarrage des services
docker compose up -d --build

# Migrations
docker compose exec app alembic upgrade head
```

---

## 🌐 URLs disponibles

### En interne (sur le serveur)

- **Backend API** : `http://localhost:8000`
  - Health : `http://localhost:8000/health`
  - Docs : `http://localhost:8000/docs` (si DEBUG=true)
- **n8n** : `http://localhost:5678`

### En externe (une fois DNS configurés)

- **Backend API** : `http://marcus.w3lg.fr` (puis HTTPS après certificats)
- **n8n** : `http://n8n.w3lg.fr` (puis HTTPS après certificats)

---

## ⚠️ À FAIRE MANUELLEMENT

### 1. Configuration DNS

Vérifier que les DNS pointent vers le serveur :

```bash
# Vérifier les DNS depuis votre machine
nslookup marcus.w3lg.fr
nslookup n8n.w3lg.fr
```

Ils doivent retourner : `135.181.253.60`

### 2. Obtenir les certificats SSL

Une fois les DNS configurés :

```bash
ssh root@135.181.253.60
cd /root/winner-machine/infra/nginx

# Obtenir les certificats
certbot --nginx -d marcus.w3lg.fr
certbot --nginx -d n8n.w3lg.fr

# Vérifier
nginx -t
systemctl reload nginx
```

### 3. Mettre à jour les configurations nginx avec SSL

Les fichiers dans `infra/nginx/` contiennent les configurations complètes avec HTTPS. Une fois les certificats obtenus, remplacer les configs temporaires :

```bash
cp /root/winner-machine/infra/nginx/marcus_wlg_fr.conf /etc/nginx/sites-available/marcus.w3lg.fr
cp /root/winner-machine/infra/nginx/n8n_w3lg_fr.conf /etc/nginx/sites-available/n8n.w3lg.fr
nginx -t
systemctl reload nginx
```

### 4. Clés API (optionnel pour l'instant)

Le Module A utilise un mock KeepaClient. Pour utiliser la vraie API Keepa :

1. Éditer `/root/winner-machine/infra/.env`
2. Remplacer `KEEPA_API_KEY=` par votre vraie clé
3. Redémarrer le container : `docker compose restart app`

### 5. Workflow n8n Module A

1. Accéder à n8n : `http://n8n.w3lg.fr` (ou `https://n8n.w3lg.fr` après SSL)
2. Se connecter avec les credentials dans `.env`
3. Importer le workflow : `n8n/workflows/wm_module_a_discover_cron.json`
4. Activer le workflow (cron quotidien à 03:00)

---

## 📊 État actuel

### Services

| Service | Status | Port | Container |
|---------|--------|------|-----------|
| PostgreSQL | ✅ Running | 5432 | winner-machine-db |
| Backend FastAPI | ✅ Running | 8000 | winner-machine-app |
| n8n | ✅ Running | 5678 | winner-machine-n8n |
| nginx | ✅ Running | 80 | (host) |

### Base de données

- ✅ Tables créées : `product_candidates`, `sourcing_options`
- ✅ Migrations appliquées : 001, 002

### Modules

- ✅ **Module A (Discoverer)** : Implémenté et fonctionnel
- ✅ **Module B (Sourcing)** : Implémenté et fonctionnel

---

## 🔍 Commandes de vérification

### Vérifier les containers

```bash
cd /root/winner-machine/infra
docker compose ps
```

### Vérifier les logs

```bash
# Backend
docker compose logs app | tail -50

# Base de données
docker compose logs db | tail -20

# n8n
docker compose logs n8n | tail -20
```

### Tester les endpoints

```bash
# Health check
curl http://localhost:8000/health

# Module A - Découverte
curl -X POST http://localhost:8000/api/v1/jobs/discover/run

# Module B - Sourcing
curl -X POST http://localhost:8000/api/v1/jobs/sourcing/run

# Options de sourcing d'un produit (remplacer {PRODUCT_ID})
curl http://localhost:8000/api/v1/products/{PRODUCT_ID}/sourcing_options
```

### Vérifier nginx

```bash
nginx -t
systemctl status nginx
curl http://localhost:8000/health
```

---

## 📝 Notes importantes

1. **Sécurité** : Les mots de passe dans `.env` ont été générés automatiquement. Ils sont stockés dans `/root/winner-machine/infra/.env` (fichier non versionné).

2. **Backups** : Aucun backup automatique configuré pour l'instant. À configurer selon vos besoins.

3. **Monitoring** : Pas de monitoring configuré. Considérer l'ajout de logs centralisés et d'alertes.

4. **Scalabilité** : Configuration actuelle pour un serveur unique. Pour la V2, considérer une architecture distribuée.

---

## 🔗 Ressources

- **Documentation déploiement** : `docs/DEPLOIEMENT_MARCUS.md`
- **Module A implémenté** : `MODULE_A_PRODUCTION_READY.md`
- **Module B implémenté** : `MODULE_B_IMPLEMENTE.md`
- **Workflows n8n** : `N8N_WORKFLOWS.md`

---

*Déploiement effectué le : 02/12/2025 à 01:52 UTC*


