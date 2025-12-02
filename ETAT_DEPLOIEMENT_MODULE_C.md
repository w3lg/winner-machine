# 📊 État du déploiement Module C sur marcus

## ✅ Fichiers déployés sur le serveur

Tous les fichiers du Module C ont été copiés dans `/root/winner-machine/backend/` :
- ✅ `app/models/product_score.py`
- ✅ `app/services/scoring_service.py`
- ✅ `app/jobs/scoring_job.py`
- ✅ `app/api/routes_scoring.py`
- ✅ `alembic/versions/003_product_score.py`
- ✅ `app/config/fees.yml`
- ✅ `app/config/scoring_rules.yml`
- ✅ `app/main.py` (mis à jour avec scoring_router)
- ✅ `app/models/__init__.py` (mis à jour avec ProductScore)

## ⚠️ Problèmes identifiés

### 1. Migration 003 non détectée par Alembic
**Symptôme** : `alembic upgrade head` ne détecte pas la migration 003
- La migration existe dans `/root/winner-machine/backend/alembic/versions/003_product_score.py`
- Mais Alembic dans le container ne la voit pas
- **Cause probable** : Le code backend n'est pas monté comme volume dans docker-compose, donc la migration n'est pas accessible depuis le container

### 2. Router scoring retourne 404
**Symptôme** : Les endpoints `/api/v1/jobs/scoring/run` retournent `{"detail":"Not Found"}`
- Le fichier `routes_scoring.py` existe
- `main.py` a été mis à jour avec `scoring_router`
- Mais le container app n'a peut-être pas été reconstruit avec le nouveau code

## 🔧 Solutions recommandées

### Option 1 : Rebuild du container app (recommandé)
```bash
cd /root/winner-machine/infra
docker compose down app
docker compose build app
docker compose up -d app
```

### Option 2 : Copier la migration dans le container
```bash
docker compose exec app bash
# Dans le container
cd /app
# La migration devrait être là si le volume est monté
alembic upgrade head
```

### Option 3 : Appliquer la migration SQL directement
```bash
docker compose exec db psql -U winner_machine -d winner_machine -f /path/to/003_migration.sql
```

## 📝 Actions immédiates

1. **Vérifier le volume mount dans docker-compose.yml**
   - Le backend doit être monté pour que les migrations soient visibles

2. **Rebuild le container app**
   - Pour intégrer le nouveau code avec scoring_router

3. **Appliquer la migration**
   - Soit via Alembic, soit manuellement en SQL

4. **Vérifier les endpoints**
   - Tester `/api/v1/jobs/scoring/run`
   - Tester `/api/v1/products/scores/top`

## 🎯 Prochaines étapes

Une fois le déploiement validé :
1. ✅ Migration appliquée
2. ✅ Endpoints scoring fonctionnels
3. ⏭️ Créer le workflow n8n pipeline A→B→C

---

*État au : 02/12/2025 - 12:40*

