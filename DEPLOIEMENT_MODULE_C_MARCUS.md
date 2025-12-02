# 🚀 Déploiement Module C sur marcus - EN COURS

## ✅ État actuel

### Fichiers déployés
- ✅ `backend/app/models/product_score.py` - Copié
- ✅ `backend/app/services/scoring_service.py` - Copié  
- ✅ `backend/app/jobs/scoring_job.py` - Copié
- ✅ `backend/app/api/routes_scoring.py` - Copié
- ✅ `backend/alembic/versions/003_product_score.py` - Copié
- ✅ `backend/app/config/fees.yml` - Copié
- ✅ `backend/app/config/scoring_rules.yml` - Copié
- ✅ `backend/app/main.py` - Mis à jour avec scoring_router
- ✅ `backend/app/models/__init__.py` - Mis à jour avec ProductScore

### Problèmes identifiés

1. **Migration 003 non détectée** : La migration existe mais Alembic ne la voit pas dans l'historique
   - Vérifier que la référence `down_revision = '002_sourcing_option'` est correcte
   - Forcer l'application avec `alembic upgrade +1` ou `alembic stamp`

2. **Router scoring non actif** : Les endpoints retournent 404
   - Vérifier les logs du container app
   - Vérifier que main.py contient bien `app.include_router(scoring_router)`

## 🔧 Commandes à exécuter

```bash
# 1. Vérifier la migration
cd /root/winner-machine/infra
docker compose exec app alembic current
docker compose exec app alembic history

# 2. Forcer l'application de la migration 003
docker compose exec app alembic upgrade +1

# 3. Vérifier que la table existe
docker compose exec app psql -U winner_machine -d winner_machine -c "\d product_scores"

# 4. Vérifier les logs du container
docker compose logs app --tail 50

# 5. Tester les endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/jobs/scoring/run
curl "http://localhost:8000/api/v1/products/scores/top?decision=A_launch&limit=10"
```

## 📝 Prochaines étapes

1. Appliquer la migration 003_product_score
2. Vérifier que les endpoints scoring fonctionnent
3. Tester le job de scoring avec des données réelles
4. Créer le workflow n8n pipeline A→B→C

---

*Dernière mise à jour : 02/12/2025*

