# 🎉 Déploiement complet sur marcus - RÉSUMÉ FINAL

## ✅ Tous les modules sont déployés et opérationnels !

### 📊 Statut du déploiement

| Composant | Statut | URL / Détails |
|-----------|--------|---------------|
| **Backend FastAPI** | ✅ Actif | https://marcus.wlg.fr |
| **PostgreSQL** | ✅ Actif | Port interne 5432 |
| **n8n** | ✅ Actif | https://n8n.w3lg.fr |
| **Module A (Discoverer)** | ✅ Déployé | Endpoint: `/api/v1/jobs/discover/run` |
| **Module B (Sourcer)** | ✅ Déployé | Endpoints: `/api/v1/jobs/sourcing/run`, `/api/v1/products/{id}/sourcing_options` |
| **Module C (Scorer)** | ✅ Déployé | Endpoints: `/api/v1/jobs/scoring/run`, `/api/v1/products/{id}/scores`, `/api/v1/products/scores/top` |
| **Workflow n8n Pipeline A→B→C** | ✅ Actif | ID: `wlaYVQkkS52IZcIg` - Daily à 03:15 |
| **Workflow n8n Module A seul** | ❌ Désactivé | ID: `IgEn1CU6IUTbK09M` (conservé pour tests manuels) |
| **Nginx** | ✅ Configuré | HTTPS avec Let's Encrypt |
| **SSL Certificates** | ✅ Valides | marcus.wlg.fr & n8n.w3lg.fr |

## 🚀 Services Docker

Tous les services Docker sont opérationnels :
- ✅ `app` (FastAPI Backend)
- ✅ `db` (PostgreSQL)
- ✅ `n8n` (Workflow Automation)

## 🔄 Workflow n8n Pipeline A→B→C

**Nom** : WM Pipeline Daily - Discover → Source → Score
- **ID** : `wlaYVQkkS52IZcIg`
- **Schedule** : Tous les jours à 03:15 (cron: `15 3 * * *`)
- **Actions** : 
  - Module A : POST `/api/v1/jobs/discover/run`
  - Module B : POST `/api/v1/jobs/sourcing/run`
  - Module C : POST `/api/v1/jobs/scoring/run`
- **Statut** : ✅ **ACTIF**

### Ancien workflow Module A seul

**Nom** : WM Module A - Discover Products (Cron)
- **ID** : `IgEn1CU6IUTbK09M`
- **Statut** : ❌ **DÉSACTIVÉ** (remplacé par le pipeline complet)
- **Note** : Conservé pour tests manuels si nécessaire

## 🔗 URLs d'accès

- **Backend API** : https://marcus.wlg.fr
  - Health check : https://marcus.wlg.fr/health
  - API docs : https://marcus.wlg.fr/docs
- **n8n** : https://n8n.w3lg.fr

## 📝 Commandes utiles

### Vérifier les services
```bash
ssh root@135.181.253.60
cd /root/winner-machine/infra
docker-compose ps
```

### Voir les logs
```bash
# Logs backend
docker-compose logs app --tail 50

# Logs n8n
docker-compose logs n8n --tail 50

# Logs database
docker-compose logs db --tail 50
```

### Tester les endpoints
```bash
# Health check
curl https://marcus.wlg.fr/health

# Découvrir des produits (Module A)
curl -X POST https://marcus.wlg.fr/api/v1/jobs/discover/run

# Lancer le sourcing (Module B)
curl -X POST https://marcus.wlg.fr/api/v1/jobs/sourcing/run

# Lancer le scoring (Module C)
curl -X POST https://marcus.wlg.fr/api/v1/jobs/scoring/run

# Voir les meilleurs scores
curl "https://marcus.wlg.fr/api/v1/products/scores/top?decision=A_launch&limit=10"
```

## 🎯 Prochaines étapes

1. ✅ Module A déployé
2. ✅ Module B déployé
3. ✅ Module C déployé et workflow pipeline A→B→C actif
4. ⏭️ Module D : Listing (à venir)
5. ⏭️ Modules E, F, G (à venir)

## 📚 Documentation

Toute la documentation est disponible dans le dossier `docs/` :
- `docs/architecture_v1.md` : Architecture complète
- `docs/linear_epics.md` : Roadmap détaillée
- `docs/DEPLOIEMENT_MARCUS.md` : Guide de déploiement
- `N8N_WORKFLOWS.md` : Documentation des workflows n8n
- `PIPELINE_DAILY_ABC.md` : Documentation du pipeline quotidien A→B→C

---

*Déploiement terminé le : 02/12/2025*
*Status : ✅ Production Ready*

