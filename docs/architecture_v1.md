# Winner Machine v1 - Architecture technique

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Infrastructure V1](#infrastructure-v1)
3. [Modèle de données](#modèle-de-données)
4. [Modules fonctionnels](#modules-fonctionnels)
5. [API & Endpoints](#api--endpoints)
6. [Workflows n8n](#workflows-n8n)
7. [Sécurité](#sécurité)

---

## 1. Vue d'ensemble

### Stack technique

- **Backend** : À définir (Node.js, Python, etc.)
- **Base de données** : À définir (PostgreSQL, MongoDB, etc.)
- **API** : REST + GraphQL (optionnel)
- **Workflows** : n8n
- **Frontend** : À définir
- **Reverse Proxy** : nginx
- **SSL** : Let's Encrypt via certbot

### Architecture globale

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │      nginx          │
        │  (Reverse Proxy)    │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
┌───────┴────────┐         ┌──────────┴────────┐
│ marcus.w3lg.fr  │         │  n8n.w3lg.fr      │
│   Backend      │         │   n8n             │
│   + Frontend   │◄────────┤   (Workflows)     │
└───────┬────────┘         └───────────────────┘
        │
        │
┌───────┴────────┐
│   Database     │
│  (PostgreSQL/  │
│   MongoDB)     │
└────────────────┘
```

---

## 2. Infrastructure V1

### Serveur : marcus

**Spécifications** :
- **Nom** : marcus
- **IP** : 135.181.253.60
- **SSH** : Port 22
- **OS** : Ubuntu 24.04.3 LTS (basé sur les informations précédentes)

### Services déployés

#### 2.1. nginx (Reverse Proxy)

**Configuration** :
- Écoute sur les ports 80 et 443
- Redirection HTTP → HTTPS
- Certificats SSL via Let's Encrypt (certbot)
- Configuration des domaines :
  - `marcus.w3lg.fr` → Backend
  - `n8n.w3lg.fr` → n8n

**Exemple de configuration** :

```nginx
# marcus.w3lg.fr
server {
    listen 80;
    server_name marcus.w3lg.fr;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name marcus.w3lg.fr;

    ssl_certificate /etc/letsencrypt/live/marcus.w3lg.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marcus.w3lg.fr/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;  # Backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# n8n.w3lg.fr
server {
    listen 443 ssl http2;
    server_name n8n.w3lg.fr;

    ssl_certificate /etc/letsencrypt/live/n8n.w3lg.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/n8n.w3lg.fr/privkey.pem;

    location / {
        proxy_pass http://localhost:5678;  # n8n
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 2.2. Backend Application

**Port** : 3000 (à adapter selon la stack)

**Responsabilités** :
- API REST/GraphQL
- Logique métier
- Accès à la base de données
- Intégrations externes (Amazon, KeyBuzz)

#### 2.3. n8n (Workflow Automation)

**Port** : 5678

**Responsabilités** :
- Automatisation des workflows entre modules
- Orchestration des processus métier
- Intégrations avec APIs externes
- Jobs planifiés (cron)

#### 2.4. Base de données

**Type** : À définir (PostgreSQL recommandé pour les relations complexes)

**Backup** : Scripts de backup quotidiens

---

## 3. Modèle de données

### 3.1. Entités principales

#### ProductCandidate

Représente un produit candidat découvert sur Amazon.

```sql
CREATE TABLE product_candidates (
    id UUID PRIMARY KEY,
    asin VARCHAR(10) UNIQUE NOT NULL,
    title VARCHAR(500),
    description TEXT,
    brand VARCHAR(255),
    category VARCHAR(255),
    price DECIMAL(10,2),
    rating DECIMAL(3,2),
    review_count INTEGER,
    sales_rank INTEGER,
    images JSONB,
    raw_data JSONB,
    discovered_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50), -- 'discovered', 'analyzing', 'sourced', 'rejected'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### SourcingOption

Options de sourcing pour un produit.

```sql
CREATE TABLE sourcing_options (
    id UUID PRIMARY KEY,
    product_candidate_id UUID REFERENCES product_candidates(id),
    supplier_name VARCHAR(255),
    supplier_url VARCHAR(500),
    moq INTEGER, -- Minimum Order Quantity
    unit_price DECIMAL(10,2),
    shipping_cost DECIMAL(10,2),
    lead_time_days INTEGER,
    payment_terms VARCHAR(255),
    quality_score DECIMAL(3,2),
    reliability_score DECIMAL(3,2),
    status VARCHAR(50), -- 'pending', 'verified', 'rejected'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### ProductScore

Score calculé pour un produit candidat.

```sql
CREATE TABLE product_scores (
    id UUID PRIMARY KEY,
    product_candidate_id UUID REFERENCES product_candidates(id),
    overall_score DECIMAL(5,2),
    profitability_score DECIMAL(5,2),
    competition_score DECIMAL(5,2),
    trend_score DECIMAL(5,2),
    sourcing_score DECIMAL(5,2),
    market_size_score DECIMAL(5,2),
    criteria_breakdown JSONB,
    calculated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### ListingTemplate

Template de listing Amazon.

```sql
CREATE TABLE listing_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    template_type VARCHAR(50), -- 'brandable', 'non-brandable'
    title_template TEXT,
    bullet_points_template TEXT[],
    description_template TEXT,
    keywords TEXT[],
    variables JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Bundle

Bundle de produits.

```sql
CREATE TABLE bundles (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    product_ids UUID[], -- Array of product_candidate_ids
    bundle_price DECIMAL(10,2),
    individual_total_price DECIMAL(10,2),
    discount_percentage DECIMAL(5,2),
    status VARCHAR(50), -- 'draft', 'published', 'archived'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### MarketplaceListing

Listing publié sur Amazon.

```sql
CREATE TABLE marketplace_listings (
    id UUID PRIMARY KEY,
    product_candidate_id UUID REFERENCES product_candidates(id),
    bundle_id UUID REFERENCES bundles(id),
    listing_template_id UUID REFERENCES listing_templates(id),
    amazon_listing_id VARCHAR(255),
    amazon_sku VARCHAR(255),
    title VARCHAR(500),
    status VARCHAR(50), -- 'draft', 'pending', 'live', 'paused', 'error'
    published_at TIMESTAMP,
    last_synced_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### KBProductKnowledge

Connaissances produit issues de KeyBuzz.

```sql
CREATE TABLE kb_product_knowledge (
    id UUID PRIMARY KEY,
    product_candidate_id UUID REFERENCES product_candidates(id),
    knowledge_type VARCHAR(50), -- 'faq', 'troubleshooting', 'specification'
    content TEXT,
    source VARCHAR(255), -- 'keybuzz', 'manual'
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### ProductFeedback

Feedback client sur un produit.

```sql
CREATE TABLE product_feedback (
    id UUID PRIMARY KEY,
    marketplace_listing_id UUID REFERENCES marketplace_listings(id),
    product_candidate_id UUID REFERENCES product_candidates(id),
    feedback_type VARCHAR(50), -- 'review', 'question', 'complaint'
    rating INTEGER,
    comment TEXT,
    source VARCHAR(50), -- 'amazon', 'keybuzz'
    processed BOOLEAN DEFAULT FALSE,
    sentiment_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2. Relations entre entités

```
ProductCandidate (1) ──< (N) SourcingOption
ProductCandidate (1) ──< (N) ProductScore
ProductCandidate (1) ──< (N) MarketplaceListing
ProductCandidate (N) ──< (N) Bundle (many-to-many via bundle_products)
ProductCandidate (1) ──< (N) KBProductKnowledge
MarketplaceListing (1) ──< (N) ProductFeedback
Bundle (1) ──< (N) MarketplaceListing
ListingTemplate (1) ──< (N) MarketplaceListing
```

---

## 4. Modules fonctionnels

### Module A : Recherche de produits (Product Discovery)

**Objectif** : Découvrir des produits gagnants sur Amazon FR selon des critères configurables.

**Sous-modules** :
- A.1 : Scraping / API Amazon
- A.2 : Filtrage par critères
- A.3 : Détection de tendances
- A.4 : Enrichissement des données produit

**Endpoints** :
- `GET /api/v1/products/candidates` : Lister les produits candidats
- `POST /api/v1/products/candidates/discover` : Lancer une recherche
- `GET /api/v1/products/candidates/:id` : Détails d'un produit
- `PUT /api/v1/products/candidates/:id/status` : Mettre à jour le statut

**Jobs** :
- Job quotidien : Recherche automatique selon critères
- Job horaire : Mise à jour des données produits existants

**Workflows n8n** :
- `workflows/a/discover-products.json` : Workflow de découverte

---

### Module B : Sourcing ✅

**Objectif** : Trouver des options d'approvisionnement pour chaque produit candidat en parcourant les catalogues des fournisseurs.

**Sous-modules** :
- **SupplierConfigService** : Charge la configuration des fournisseurs depuis `suppliers.yml`.
- **SourcingMatcher** : Matche les produits candidats avec les catalogues fournisseurs (CSV) en utilisant des mots-clés.
- **SourcingJob** : Orchestre la recherche et la création d'options de sourcing pour les produits sans options.

**Entités de données** :
- `SourcingOption` : Stocke les informations d'une option de sourcing (fournisseur, coûts, délais, MOQ, etc.).

**Configuration** :
- `backend/app/config/suppliers.yml` : Configuration des fournisseurs (type, chemin catalogue, sourcing_type, brandable, bundle_capable).
- Catalogues CSV : Fichiers CSV contenant les produits disponibles chez les fournisseurs (ex: `infra/sql/demo_supplier_catalog.csv`).

**Algorithme de matching** :
- Extraction de mots-clés depuis le titre et la catégorie du produit candidat.
- Recherche dans les catalogues CSV (colonnes `name` et `keywords`).
- Match si au moins 2 mots-clés significatifs (ou 1 si peu de mots-clés).
- Création d'une `SourcingOption` pour chaque match trouvé.

**Endpoints API** :
- `POST /api/v1/jobs/sourcing/run` : Lance le job de sourcing (trouve et crée les options).
- `GET /api/v1/products/{product_id}/sourcing_options` : Récupère toutes les options de sourcing d'un produit.

**Jobs** :
- `SourcingJob` : Traite les produits candidats sans options de sourcing, matche avec les catalogues, et crée les options en base.

**Workflows n8n** :
- À créer : Workflow cron pour lancer `POST /api/v1/jobs/sourcing/run` après chaque job de découverte.

---

### Module C : Scoring

**Objectif** : Calculer un score global pour chaque produit candidat.

**Sous-modules** :
- C.1 : Calcul de rentabilité
- C.2 : Analyse de la compétition
- C.3 : Détection de tendances
- C.4 : Score de sourcing
- C.5 : Score global pondéré

**Endpoints** :
- `POST /api/v1/scoring/calculate/:productId` : Calculer le score
- `GET /api/v1/scoring/scores` : Lister les scores
- `GET /api/v1/scoring/scores/:id` : Détails d'un score

**Jobs** :
- Job déclenché : Calcul automatique après découverte ou mise à jour produit

**Workflows n8n** :
- `workflows/c/calculate-score.json` : Workflow de scoring

---

### Module D/E : Création de listings (Brandable & Non-Brandable)

**Objectif** : Générer des listings Amazon optimisés (brandables ou non) pour les produits sélectionnés.

**Sous-modules** :
- D : Listings brandables (produits avec marque)
- E : Listings non-brandables (produits sans marque, clone d'existant)

**Modèles de données** :
- `ListingTemplate` : Template de listing avec titre, bullets, description, FAQ, etc.
- `Bundle` : Structure pour les bundles de produits (V1 simple)

**Services** :
- `ListingGeneratorBrandable` : Génère des listings avec marque (Module D)
- `ListingGeneratorNonBrandable` : Génère des listings sans marque (Module E)
- `ListingService` : Orchestre la génération selon le type d'option de sourcing

**Jobs** :
- `ListingJob` : Génère des listings pour tous les produits avec status="selected" sans listing

**Endpoints** :
- `POST /api/v1/jobs/listing/generate_for_selected` : Lancer le job de génération
- `GET /api/v1/products/{product_id}/listing_templates` : Récupérer les listings d'un produit
- `GET /api/v1/listings/top_drafts` : Récupérer les listings en draft (query: limit)
- `POST /api/v1/listings/export_csv` : Exporter des listings en CSV

**Workflows n8n** :
- `WM Winners → Listings Drafts` : Génération quotidienne à 04:00

---

### Module E : Gestion des bundles (Structure V1)

**Objectif** : Créer et gérer des bundles de produits.

**Sous-modules** :
- E.1 : Création de bundles
- E.2 : Calcul de prix optimisé
- E.3 : Gestion des stocks

**Endpoints** :
- `GET /api/v1/bundles` : Lister les bundles
- `POST /api/v1/bundles` : Créer un bundle
- `PUT /api/v1/bundles/:id` : Modifier un bundle
- `DELETE /api/v1/bundles/:id` : Supprimer un bundle

**Workflows n8n** :
- `workflows/e/create-bundle.json` : Création de bundle

---

### Module F : Publication Amazon

**Objectif** : Publier les listings sur Amazon via API.

**Sous-modules** :
- F.1 : Intégration API Amazon Seller Central
- F.2 : Upload de produits
- F.3 : Gestion des stocks
- F.4 : Synchronisation des prix
- F.5 : Gestion des commandes

**Endpoints** :
- `POST /api/v1/amazon/publish` : Publier un listing
- `GET /api/v1/amazon/listings` : Lister les listings publiés
- `PUT /api/v1/amazon/listings/:id/sync` : Synchroniser un listing
- `GET /api/v1/amazon/orders` : Récupérer les commandes

**Jobs** :
- Job horaire : Synchronisation des stocks et prix
- Job quotidien : Récupération des commandes

**Workflows n8n** :
- `workflows/f/publish-to-amazon.json` : Publication sur Amazon
- `workflows/f/sync-listings.json` : Synchronisation

---

### Module G : SAV automatisé KeyBuzz

**Objectif** : Automatiser le service après-vente via KeyBuzz.

**Sous-modules** :
- G.1 : Intégration KeyBuzz API
- G.2 : Gestion des connaissances produit
- G.3 : Réponses automatiques
- G.4 : Escalade vers humain si nécessaire
- G.5 : Feedback loop (apprentissage)

**Endpoints** :
- `GET /api/v1/keybuzz/knowledge` : Récupérer les connaissances
- `POST /api/v1/keybuzz/knowledge` : Ajouter une connaissance
- `GET /api/v1/keybuzz/tickets` : Lister les tickets SAV
- `POST /api/v1/keybuzz/feedback` : Enregistrer un feedback

**Jobs** :
- Job continu : Monitoring des tickets KeyBuzz
- Job quotidien : Analyse des feedbacks et mise à jour connaissances

**Workflows n8n** :
- `workflows/g/monitor-keybuzz.json` : Monitoring KeyBuzz
- `workflows/g/auto-respond.json` : Réponses automatiques
- `workflows/g/feedback-loop.json` : Boucle de feedback

---

## 5. API & Endpoints

### Structure des endpoints

Tous les endpoints suivent le pattern REST :

```
/api/v1/{module}/{resource}/{action}
```

### Authentification

À définir (JWT recommandé)

### Format de réponse

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  },
  "error": null
}
```

---

## 6. Workflows n8n

Les workflows n8n sont organisés par module dans `workflows/{module}/`.

### Exemples de workflows

#### Découverte automatique de produits

```json
{
  "name": "Discover Products Daily",
  "nodes": [
    {
      "type": "Schedule Trigger",
      "cron": "0 2 * * *" // 2h du matin chaque jour
    },
    {
      "type": "HTTP Request",
      "url": "http://localhost:3000/api/v1/products/candidates/discover"
    },
    {
      "type": "PostgreSQL",
      "operation": "Insert",
      "table": "product_candidates"
    }
  ]
}
```

---

## 7. Sécurité

### Authentification & Autorisation

- JWT pour l'API
- Rôles utilisateurs (admin, operator, viewer)
- Rate limiting sur les endpoints

### Données sensibles

- Tokens API stockés chiffrés
- Variables d'environnement pour les secrets
- Accès SSH via clés uniquement

### Monitoring

- Logs centralisés
- Alertes sur erreurs critiques
- Monitoring de santé des services

---

*Document en cours de construction - À compléter avec les spécifications détaillées*

