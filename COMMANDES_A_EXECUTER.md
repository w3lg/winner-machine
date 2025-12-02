# 📋 Commandes à exécuter - Winner Machine v1

## ⚠️ Note importante

Docker n'est pas disponible sur cette machine. Les commandes ci-dessous doivent être exécutées sur :
- **Votre machine locale** (avec Docker installé)
- **Le serveur marcus** (135.181.253.60) après connexion SSH

## 🚀 Démarrage rapide

### Option 1 : Script automatique (recommandé)

```powershell
# Windows
.\start.ps1

# Linux/Mac
./start.sh
```

### Option 2 : Commandes manuelles

```bash
# 1. Aller dans le dossier infra
cd infra

# 2. Vérifier/créer le fichier .env
# (Copier .env.example vers .env si nécessaire)

# 3. Démarrer les services
docker-compose up -d

# 4. Attendre que les services soient prêts (10-15 secondes)
# Vérifier avec :
docker-compose ps

# 5. Appliquer les migrations
docker-compose exec app alembic upgrade head

# 6. Vérifier que tout fonctionne
curl http://localhost:8000/health
```

## ✅ Checklist de démarrage

- [ ] Docker Desktop installé et démarré
- [ ] Fichier `infra/.env` créé (ou valeurs par défaut utilisées)
- [ ] Services Docker démarrés (`docker-compose up -d`)
- [ ] Migrations appliquées (`alembic upgrade head`)
- [ ] Health check OK (`curl http://localhost:8000/health`)
- [ ] Endpoint discover testé (`curl -X POST http://localhost:8000/api/v1/jobs/discover/run`)

## 🧪 Tests après démarrage

### 1. Health check

```bash
curl http://localhost:8000/health
# Réponse attendue: {"status":"ok"}
```

### 2. Documentation API

Ouvrir dans le navigateur :
```
http://localhost:8000/docs
```

### 3. Tester le Module A - Discoverer

```bash
# Lancer le job de découverte
curl -X POST http://localhost:8000/api/v1/jobs/discover/run

# Réponse attendue:
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

### 4. Vérifier les données en base

```bash
# Se connecter à la base de données
docker-compose exec db psql -U winner_machine -d winner_machine

# Requêtes SQL utiles :
SELECT COUNT(*) FROM product_candidates;
SELECT asin, title, category, bsr, status FROM product_candidates LIMIT 10;
SELECT status, COUNT(*) FROM product_candidates GROUP BY status;
\q
```

## 📊 Vérification des services

### Voir l'état des services

```bash
docker-compose ps
```

Tous les services doivent avoir le statut "Up".

### Voir les logs

```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f n8n
```

## 🔧 Commandes utiles

### Redémarrer un service

```bash
docker-compose restart app
```

### Arrêter les services

```bash
docker-compose down
```

### Reconstruire l'image de l'app

```bash
docker-compose build app
docker-compose up -d app
```

### Accéder au shell du container

```bash
# Container app
docker-compose exec app bash

# Container db
docker-compose exec db psql -U winner_machine -d winner_machine
```

## 🌐 URLs des services

Une fois démarrés :

- **Backend API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Health check** : http://localhost:8000/health
- **n8n** : http://localhost:5678

## 📝 Prochaines étapes après démarrage

1. **Tester le Module A** : Lancer le job de découverte
2. **Configurer n8n** : Créer un workflow cron pour automatiser la découverte
3. **Vérifier les données** : Consulter les produits découverts en base
4. **Continuer le développement** : Module B (Sourcing) selon `docs/linear_epics.md`

## 🔗 Documentation

- **Guide complet** : `GUIDE_DEMARRAGE.md`
- **Module A implémenté** : `MODULE_A_IMPLEMENTE.md`
- **Architecture** : `docs/architecture_v1.md`

---

*Dernière mise à jour : 02/12/2025*

