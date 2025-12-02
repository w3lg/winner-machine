# Déploiement sur le serveur marcus

Guide complet pour déployer Winner Machine v1 sur le serveur de production marcus.

## 📋 Prérequis sur le serveur marcus

Avant de déployer, assurez-vous que le serveur a :

- ✅ **Docker** installé et fonctionnel
- ✅ **docker-compose** installé
- ✅ **nginx** installé et configuré
- ✅ **Git** installé
- ✅ Accès SSH configuré (clé dans `_local_config/ssh_keys/ssh_key`)

## 🔧 Vérification des prérequis

### Vérifier Docker

```bash
ssh -i _local_config/ssh_keys/ssh_key root@135.181.253.60
docker --version
docker-compose --version
```

### Vérifier nginx

```bash
nginx -v
systemctl status nginx
```

## 🚀 Déploiement

### Option 1 : Script automatique (recommandé)

Depuis votre machine locale :

```bash
chmod +x deploy_to_marcus.sh
./deploy_to_marcus.sh
```

Le script va :
1. Se connecter au serveur via SSH
2. Cloner/mettre à jour le repository
3. Créer le fichier `.env` depuis le template
4. Démarrer les services Docker
5. Appliquer les migrations

### Option 2 : Déploiement manuel

#### 1. Connexion au serveur

```bash
ssh -i _local_config/ssh_keys/ssh_key root@135.181.253.60
```

#### 2. Cloner ou mettre à jour le repository

```bash
# Si première fois
cd /root
git clone https://github.com/w3lg/winner-machine.git
cd winner-machine

# Si déjà déployé, mettre à jour
cd /root/winner-machine
git pull origin main
```

#### 3. Configuration de l'environnement

```bash
cd /root/winner-machine/infra

# Créer le fichier .env depuis le template
cp env.prod.template .env

# Éditer avec vos vraies valeurs
nano .env
```

**⚠️ IMPORTANT** : Remplacer toutes les valeurs dans `.env` :
- `POSTGRES_PASSWORD` : Mot de passe fort pour PostgreSQL
- `SECRET_KEY` : Clé secrète aléatoire forte
- `KEEPA_API_KEY` : Votre vraie clé API Keepa
- `N8N_BASIC_AUTH_PASSWORD` : Mot de passe admin n8n
- `N8N_ENCRYPTION_KEY` : Clé d'encryption n8n

#### 4. Démarrer les services

```bash
cd /root/winner-machine/infra

# Arrêter les services existants (si présents)
docker-compose down

# Pull des images les plus récentes
docker-compose pull

# Démarrer les services
docker-compose up -d
```

#### 5. Vérifier que les services sont démarrés

```bash
docker-compose ps
```

Vous devriez voir 3 services avec le statut "Up" :
- `winner-machine-db`
- `winner-machine-app`
- `winner-machine-n8n`

#### 6. Appliquer les migrations de base de données

```bash
docker-compose exec app alembic upgrade head
```

#### 7. Vérifier que tout fonctionne

```bash
# Health check du backend
curl http://localhost:8000/health

# Réponse attendue: {"status":"ok"}
```

## 🌐 Configuration nginx et certificats Let's Encrypt

### 1. Copier les configurations nginx

Les fichiers de configuration sont dans `infra/nginx/` :

- `marcus_wlg_fr.conf` → Backend
- `n8n_w3lg_fr.conf` → n8n

Sur le serveur :

```bash
cd /root/winner-machine/infra/nginx

# Copier vers sites-available
cp marcus_wlg_fr.conf /etc/nginx/sites-available/marcus.wlg.fr
cp n8n_w3lg_fr.conf /etc/nginx/sites-available/n8n.w3lg.fr

# Créer les liens symboliques vers sites-enabled
ln -sf /etc/nginx/sites-available/marcus.wlg.fr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/n8n.w3lg.fr /etc/nginx/sites-enabled/

# Vérifier la configuration nginx
nginx -t
```

### 2. Obtenir les certificats Let's Encrypt

#### Pour marcus.wlg.fr

```bash
# Installer certbot si nécessaire
apt-get update
apt-get install certbot python3-certbot-nginx

# Obtenir le certificat
certbot --nginx -d marcus.wlg.fr

# Suivre les instructions :
# - Email : votre email
# - Accepter les conditions
# - Redirection HTTP → HTTPS : Oui
```

#### Pour n8n.w3lg.fr

```bash
certbot --nginx -d n8n.w3lg.fr

# Suivre les mêmes instructions
```

### 3. Configurer le renouvellement automatique

Les certificats Let's Encrypt expirent après 90 jours. Le renouvellement est automatique via un cron :

```bash
# Vérifier que le cron existe
certbot renew --dry-run

# Le cron est généralement installé automatiquement par certbot
# Sinon, créer un cron :
# 0 0 * * * certbot renew --quiet
```

### 4. Recharger nginx

```bash
systemctl reload nginx
```

### 5. Vérifier que tout fonctionne

```bash
# Backend
curl https://marcus.wlg.fr/health

# n8n (nécessite authentification)
curl https://n8n.w3lg.fr
```

## 📊 Vérifications post-déploiement

### 1. Vérifier les logs

```bash
cd /root/winner-machine/infra

# Logs de tous les services
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f n8n
```

### 2. Tester le Module A

```bash
# Lancer le job de découverte
curl -X POST http://localhost:8000/api/v1/jobs/discover/run

# Ou depuis l'extérieur (si nginx configuré)
curl -X POST https://marcus.wlg.fr/api/v1/jobs/discover/run
```

### 3. Vérifier les données en base

```bash
docker-compose exec db psql -U winner_machine -d winner_machine

# Dans psql :
SELECT COUNT(*) FROM product_candidates;
SELECT asin, title, category, status FROM product_candidates LIMIT 10;
\q
```

## 🔄 Mises à jour futures

Pour mettre à jour le code après un commit :

```bash
ssh -i _local_config/ssh_keys/ssh_key root@135.181.253.60

cd /root/winner-machine
git pull origin main

cd infra
docker-compose pull
docker-compose up -d
docker-compose exec app alembic upgrade head
```

## 🛠️ Commandes utiles

### Redémarrer un service

```bash
cd /root/winner-machine/infra
docker-compose restart app
```

### Voir l'état des services

```bash
docker-compose ps
```

### Arrêter tous les services

```bash
docker-compose down
```

### Reconstruire l'image de l'app

```bash
docker-compose build app
docker-compose up -d app
```

## 🔐 Sécurité

### Fichier .env

Le fichier `.env` contient des informations sensibles. Assurez-vous :

- ✅ Il n'est **jamais** commité dans Git (déjà dans `.gitignore`)
- ✅ Permissions restreintes : `chmod 600 /root/winner-machine/infra/.env`
- ✅ Ne le partagez jamais

### Mots de passe

- Utilisez des mots de passe forts et uniques
- Changez les valeurs par défaut
- Considérez l'utilisation d'un gestionnaire de secrets pour la production

## 📝 Notes importantes

- Les certificats Let's Encrypt doivent être renouvelés tous les 90 jours (automatique)
- Les backups de la base de données doivent être configurés (non couvert ici)
- Surveillez les logs régulièrement
- Configurez des alertes pour les erreurs critiques

## 🔗 Liens utiles

- **Backend** : https://marcus.wlg.fr
- **Documentation API** : https://marcus.wlg.fr/docs (si DEBUG=true)
- **n8n** : https://n8n.w3lg.fr

---

*Documentation créée le : 02/12/2025*

