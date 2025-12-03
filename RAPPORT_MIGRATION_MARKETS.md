# 📊 Rapport : Migration de Catégories vers Listes d'ASINs par Marché

## ✅ Modifications Complétées

### 1. Configuration des Marchés (`markets_asins.yml`)

**Fichier créé** : `backend/app/config/markets_asins.yml`

**Structure** :
```yaml
markets:
  amazon_fr:
    domain: 1
    label: "France"
    active: true
    asins:
      - B08XYZ1234
      - B08ABC5678
      - B09DEF9012
      - B08NCR9Y9T
      - B07XYZ1234
      - B08KX5Y3ZP
  amazon_de:
    domain: 3
    label: "Allemagne"
    active: false
    asins: []
  amazon_es:
    domain: 9
    label: "Espagne"
    active: false
    asins: []
```

### 2. Service de Configuration des Marchés

**Fichier créé** : `backend/app/services/market_config.py`

**Fonctionnalités** :
- ✅ `get_market_configs()` : Charge tous les marchés depuis le YAML
- ✅ `get_market_by_code(code: str)` : Retourne la config d'un marché spécifique
- ✅ `get_active_markets()` : Retourne uniquement les marchés actifs

### 3. KeepaClient - Méthode `get_products_by_asins()`

**Fichier modifié** : `backend/app/services/keepa_client.py`

**Nouvelle méthode** :
```python
def get_products_by_asins(
    self, domain: int, asin_list: List[str]
) -> List[KeepaProduct]
```

**Comportement** :
- ✅ Traite jusqu'à 100 ASINs par batch (limite Keepa)
- ✅ Appelle `/product?key=...&domain=DOMAIN&asin=ASIN1,ASIN2,...&stats=180`
- ✅ Normalise les produits avec `_normalize_products()`
- ✅ Gestion d'erreurs robuste (ne plante pas le job)

### 4. DiscoverJob - Migration vers les Marchés

**Fichier modifié** : `backend/app/jobs/discover_job.py`

**Changements principaux** :
- ✅ Remplace la boucle sur `CategoryConfig` par une boucle sur `MarketConfig`
- ✅ `__init__()` accepte maintenant `market_code` (défaut: "amazon_fr")
- ✅ `run()` traite un marché spécifié au lieu de toutes les catégories
- ✅ `_process_market()` remplace `_process_category()`
- ✅ Utilise `get_products_by_asins()` au lieu de `get_top_products_by_category()`

**Nouveau comportement** :
- Par défaut, traite uniquement "amazon_fr"
- Si la liste d'ASINs est vide → log WARNING et skip
- Appelle Keepa avec la liste d'ASINs configurée
- Enrichit chaque ASIN avec Keepa API

### 5. API Endpoint - Paramètre `market`

**Fichier modifié** : `backend/app/api/routes_discover.py`

**Changement** :
- ✅ Endpoint `/api/v1/jobs/discover/run` accepte maintenant :
  - Paramètre query `market` (optionnel, défaut: "amazon_fr")
  - Exemple : `/api/v1/jobs/discover/run?market=amazon_fr`

**Réponse mise à jour** :
- `markets_processed` au lieu de `categories_processed`

### 6. UI Dashboard - Sélecteur de Marché

**Fichier modifié** : `backend/app/templates/dashboard.html`
**Fichier modifié** : `backend/app/api/routes_ui.py`

**Nouveau dans l'UI** :
- ✅ Sélecteur de marketplace dans la section "Module A : Discover"
- ✅ Affiche tous les marchés configurés avec leur nombre d'ASINs
- ✅ Par défaut sélectionne "amazon_fr"
- ✅ Envoie le paramètre `market` dans le body de la requête POST

**Route UI mise à jour** :
- `/ui/run/discover` accepte maintenant un body JSON avec `{ "market": "amazon_fr" }`

## 📝 Exemple de Données

### Exemple de marché configuré
```yaml
amazon_fr:
  domain: 1
  label: "France"
  active: true
  asins:
    - B08XYZ1234
    - B08ABC5678
    - B09DEF9012
```

### Exemple de réponse Keepa normalisée (à venir)
Une fois les ASINs enrichis par Keepa, la structure sera :
```json
{
  "asin": "B08XYZ1234",
  "title": "Nom du produit réel",
  "category": "Domain_1",
  "avg_price": 29.99,
  "bsr": 1234,
  "estimated_sales_per_day": 15.5,
  "reviews_count": 1250,
  "rating": 4.5,
  "raw_data": {
    "asin": "B08XYZ1234",
    "source": "keepa_api",
    "domain": 1,
    ...
  }
}
```

## 🚀 Prochaines Étapes

### Tests à Effectuer

1. **Remplir la liste d'ASINs** dans `markets_asins.yml` avec de vrais ASINs Amazon FR
2. **Déployer sur marcus** (git pull, docker compose build, restart)
3. **Tester le job Discover** via `/ui` ou `curl`
4. **Vérifier les produits** dans la base de données
5. **Lancer le pipeline complet** (Sourcing → Scoring → Listing)
6. **Vérifier les Winners** dans l'UI

### Commandes de Déploiement

```bash
# Sur marcus
cd /root/winner-machine
git pull origin main
cd infra
docker compose build app
docker compose restart app

# Test
curl -X POST "http://localhost:8000/api/v1/jobs/discover/run?market=amazon_fr"
```

## 📊 Statistiques Attendues

Une fois les vrais ASINs configurés, les statistiques seront :
- **Produits découverts** : Nombre d'ASINs dans la liste (ex: 6)
- **Sourcing options** : Dépend du matching avec les catalogues
- **Scores créés** : Nombre de couples (ProductCandidate, SourcingOption)
- **Winners** : Produits avec `decision=A_launch`

## ✅ Avantages de cette Approche

1. **✅ Compatible avec l'API Keepa** : Utilise `/product` qui fonctionne réellement
2. **✅ Flexible** : Facile d'ajouter/retirer des ASINs
3. **✅ Multi-marchés** : Supporte plusieurs pays (FR, DE, ES, etc.)
4. **✅ Pas de dépendance catégories** : Plus besoin de rechercher par catégorie
5. **✅ Contrôle total** : Vous choisissez exactement quels produits traiter

## ⚠️ Notes Importantes

- Les ASINs dans `markets_asins.yml` sont actuellement des **exemples de test**
- Il faudra remplacer ces ASINs par de **vrais ASINs Amazon FR** pour obtenir des produits réels
- L'API Keepa enrichira ces ASINs avec les données réelles (prix, BSR, reviews, etc.)

