# 🌱 Seed de Données de Test

## 📋 Description

Ce script permet de créer des données de test dans la base de données pour tester le pipeline complet A→B→C→D/E avec des stats non nulles.

## 🎯 Données créées

Le script `backend/scripts/seed_test_data.py` crée :

1. **3 ProductCandidate** de test :
   - ASINs: `B00TEST001`, `B00TEST002`, `B00TEST003`
   - Catégories: Electronics, Home & Kitchen, Sports & Outdoors
   - Status: `new` (puis `selected` pour ceux avec scores)

2. **6 SourcingOption** (2 par produit) :
   - 1 option non-brandable (EU_wholesale)
   - 1 option brandable (import_CN)

3. **3 ProductScore** (1 par produit) :
   - Decision: `A_launch`
   - Status produit mis à jour vers `selected`

## 🚀 Utilisation

### Option 1 : Depuis le container Docker

```bash
# Se connecter au serveur marcus
ssh root@135.181.253.60

# Aller dans le répertoire du projet
cd /root/winner-machine/infra

# Exécuter le script via le container app
docker compose exec app python scripts/seed_test_data.py
```

### Option 2 : En local (si la DB est accessible)

```bash
# Depuis la racine du projet
cd backend
python scripts/seed_test_data.py
```

### Option 3 : Via Docker Compose local

```bash
# Depuis infra/
docker compose exec app python scripts/seed_test_data.py
```

## ✅ Vérification

Après avoir exécuté le script, vous pouvez vérifier les données :

```bash
# Compter les produits
docker compose exec -T db psql -U winner_machine -d winner_machine -c "SELECT COUNT(*) FROM product_candidates;"

# Voir les produits 'selected'
docker compose exec -T db psql -U winner_machine -d winner_machine -c "SELECT asin, title, status FROM product_candidates WHERE status = 'selected';"

# Compter les options de sourcing
docker compose exec -T db psql -U winner_machine -d winner_machine -c "SELECT COUNT(*) FROM sourcing_options;"

# Compter les scores
docker compose exec -T db psql -U winner_machine -d winner_machine -c "SELECT COUNT(*) FROM product_scores;"
```

## 🔄 Utilisation avec le pipeline

Une fois les données de test créées :

1. **Lancer le job Listing** :
   ```bash
   curl -X POST http://localhost:8000/api/v1/jobs/listing/generate_for_selected
   ```

2. **Vérifier les listings créés** :
   ```bash
   curl "http://localhost:8000/api/v1/listings/top_drafts?limit=10"
   ```

3. **Exporter en CSV** :
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"export_all_drafts": true}' \
     http://localhost:8000/api/v1/listings/export_csv \
     -o listings_test.csv
   ```

## ⚠️ Attention

- Ce script vérifie l'existence des produits avant de les créer (évite les doublons)
- Les ASINs de test commencent par `B00TEST`
- En production, ne pas exécuter ce script si vous avez déjà des données réelles importantes

## 🧹 Nettoyage (optionnel)

Pour supprimer les données de test :

```sql
-- Attention : Supprime toutes les données de test !
DELETE FROM product_scores WHERE product_candidate_id IN (
    SELECT id FROM product_candidates WHERE asin LIKE 'B00TEST%'
);
DELETE FROM sourcing_options WHERE product_candidate_id IN (
    SELECT id FROM product_candidates WHERE asin LIKE 'B00TEST%'
);
DELETE FROM listing_templates WHERE product_candidate_id IN (
    SELECT id FROM product_candidates WHERE asin LIKE 'B00TEST%'
);
DELETE FROM product_candidates WHERE asin LIKE 'B00TEST%';
```

---

*Document créé le : 02/12/2025*

