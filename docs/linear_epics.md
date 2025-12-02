# Winner Machine v1 - Epics Linear (WM-0 à WM-7)

## 📋 Introduction

Ce document détaille les **8 epics** du projet Winner Machine v1, organisés pour permettre à un développeur qui ne connaît rien au projet de comprendre immédiatement la structure et de savoir par où commencer.

Chaque epic correspond à une phase de développement et contient des **tâches détaillées** qui peuvent être directement créées dans Linear.

---

## 🏗️ Epic WM-0 : Infrastructure & Setup

**Description** : Mettre en place l'infrastructure de base, les outils de développement, et la configuration du serveur.

**Durée estimée** : 1-2 semaines

**Prérequis** : Accès SSH au serveur marcus

### Tâches détaillées

#### WM-0.1 : Configuration du serveur
- [ ] Vérifier la connexion SSH au serveur marcus (135.181.253.60)
- [ ] Configurer les clés SSH
- [ ] Mettre à jour le système (Ubuntu)
- [ ] Installer les outils de base (git, curl, wget, etc.)
- [ ] Configurer le firewall (ufw)
- [ ] Créer les utilisateurs système nécessaires

#### WM-0.2 : Installation et configuration nginx
- [ ] Installer nginx
- [ ] Configurer les domaines :
  - [ ] `marcus.w3lg.fr` → Backend
  - [ ] `n8n.w3lg.fr` → n8n
- [ ] Configurer les redirections HTTP → HTTPS
- [ ] Tester la configuration nginx

#### WM-0.3 : Installation et configuration certbot
- [ ] Installer certbot
- [ ] Obtenir les certificats SSL pour marcus.w3lg.fr
- [ ] Obtenir les certificats SSL pour n8n.w3lg.fr
- [ ] Configurer le renouvellement automatique
- [ ] Vérifier les certificats

#### WM-0.4 : Installation de la base de données
- [ ] Choisir le type de DB (PostgreSQL recommandé)
- [ ] Installer PostgreSQL
- [ ] Configurer la base de données
- [ ] Créer l'utilisateur et les permissions
- [ ] Configurer les backups automatiques
- [ ] Tester la connexion

#### WM-0.5 : Installation de n8n
- [ ] Installer n8n (npm ou Docker)
- [ ] Configurer n8n pour écouter sur le port 5678
- [ ] Configurer l'authentification n8n
- [ ] Tester l'accès via n8n.w3lg.fr
- [ ] Créer la structure de dossiers pour les workflows

#### WM-0.6 : Setup du backend
- [ ] Choisir la stack backend (Node.js, Python, etc.)
- [ ] Initialiser le projet
- [ ] Configurer la structure de dossiers
- [ ] Configurer les variables d'environnement
- [ ] Configurer la connexion à la base de données
- [ ] Créer les scripts de démarrage

#### WM-0.7 : Configuration Git & CI/CD
- [ ] Initialiser le repository Git
- [ ] Configurer .gitignore
- [ ] Créer les branches (main, develop)
- [ ] Configurer les hooks Git (optionnel)
- [ ] Documenter le processus de déploiement

#### WM-0.8 : Documentation initiale
- [ ] Créer le README.md principal
- [ ] Documenter l'installation locale
- [ ] Documenter l'accès au serveur
- [ ] Créer le guide de contribution

**Définition de "Terminé"** :
- Serveur accessible et configuré
- nginx fonctionne avec SSL
- Base de données accessible
- n8n accessible via son domaine
- Backend démarre et se connecte à la DB

---

## 🔍 Epic WM-1 : Module A - Recherche de produits

**Description** : Implémenter le système de découverte automatique de produits gagnants sur Amazon FR.

**Durée estimée** : 2-3 semaines

**Prérequis** : WM-0 terminé

### Tâches détaillées

#### WM-1.1 : Modèle de données ProductCandidate ✅
- [x] Créer la table `product_candidates`
- [x] Définir les champs et contraintes
- [x] Créer les index nécessaires (asin, category, status, bsr, source_marketplace)
- [x] Écrire les migrations (Alembic)
- [x] Créer les modèles/entités dans le backend

#### WM-1.2 : Intégration API Keepa ✅
- [x] Rechercher/documenter l'API Keepa
- [x] Créer le client API Keepa (`KeepaClient`)
- [x] Implémenter la recherche de produits par catégorie
- [x] Mode mock intégré (si pas de clé API)
- [x] Structure prête pour vraie API Keepa
- [x] Gérer les erreurs et exceptions

#### WM-1.3 : Configuration de catégories ✅
- [x] Créer le fichier YAML de configuration (`category_config.yml`)
- [x] Service `CategoryConfigService` pour charger la config
- [x] Support de plusieurs catégories avec seuils (BSR, prix)
- [x] Flags active/inactive par catégorie

#### WM-1.4 : Enrichissement des données ✅
- [x] Stocker les métriques (prix moyen, BSR, ventes estimées)
- [x] Stocker les reviews et ratings
- [x] Stocker les données brutes Keepa (JSON)
- [x] Données enrichies stockées en base

#### WM-1.5 : API Endpoints Module A ✅
- [x] `POST /api/v1/jobs/discover/run` - Lancer la découverte
- [x] Réponse structurée avec statistiques détaillées
- [x] Gestion d'erreurs complète
- [x] Documentation OpenAPI complète

#### WM-1.6 : Jobs automatiques ✅
- [x] Créer le job de découverte (`DiscoverJob`)
- [x] Gestion des erreurs par catégorie (continue sur erreur)
- [x] Logging complet (début, stats par catégorie, fin)
- [x] Upsert intelligent (création ou mise à jour par ASIN)

#### WM-1.7 : Workflow n8n ✅
- [x] Créer le workflow `wm_module_a_discover_cron.json`
- [x] Configurer le trigger Cron (tous les jours à 03:00)
- [x] Connecter à l'API backend
- [x] Gestion des succès/erreurs
- [x] Documentation dans `N8N_WORKFLOWS.md`

#### WM-1.8 : Tests ✅
- [x] Tests unitaires (`test_discover.py`)
- [x] Test création de produits
- [x] Test mise à jour produits existants
- [x] Test structure de réponse

#### WM-1.9 : Configuration dev/prod ✅
- [x] Séparation dev/prod dans `config.py` (APP_ENV)
- [x] Templates `.env` pour dev et prod
- [x] Logging configuré et paramétrable
- [x] Variables d'environnement documentées

#### WM-1.10 : Déploiement production ✅
- [x] Script de déploiement (`deploy_to_marcus.sh`)
- [x] Documentation déploiement (`DEPLOIEMENT_MARCUS.md`)
- [x] Configuration nginx pour marcus.w3lg.fr et n8n.w3lg.fr
- [x] Guide Let's Encrypt et certificats SSL

**Statut : ✅ TERMINÉ (Production Ready V1)**

**Définition de "Terminé"** : ✅
- ✅ Produits découverts automatiquement via endpoint HTTP
- ✅ Données enrichies stockées en base
- ✅ API fonctionnelle avec gestion d'erreurs
- ✅ Workflow n8n opérationnel et documenté
- ✅ Logging complet
- ✅ Configuration dev/prod
- ✅ Scripts de déploiement
- ✅ Documentation complète

---

## 🏭 Epic WM-2 : Module B - Sourcing

**Description** : Implémenter le système de recherche et d'évaluation de fournisseurs.

**Durée estimée** : 2-3 semaines

**Prérequis** : WM-1 terminé (avoir des produits candidats)

### Tâches détaillées

#### WM-2.1 : Modèle de données SourcingOption ✅
- [x] Créer la table `sourcing_options`
- [x] Définir la relation avec `product_candidates` (FK avec CASCADE)
- [x] Créer les index (product_candidate_id, supplier_name, sourcing_type)
- [x] Créer les modèles backend (SourcingOption ORM)
- [x] Migration Alembic (002_sourcing_option.py)

#### WM-2.2 : Configuration fournisseurs ✅
- [x] Créer le fichier `suppliers.yml` pour configurer les fournisseurs
- [x] Service `SupplierConfigService` pour charger la config
- [x] Support des catalogues CSV
- [x] Catalogue CSV de démo (`demo_supplier_catalog.csv`)

#### WM-2.3 : Service SourcingMatcher ✅
- [x] Matching par mots-clés (titre + catégorie du produit)
- [x] Parsing de catalogues CSV
- [x] Normalisation des mots-clés (stopwords, filtrage)
- [x] Construction des SourcingOption depuis les matches
- [x] Gestion d'erreurs robuste (continue si CSV introuvable)

#### WM-2.4 : Job SourcingJob ✅
- [x] Récupération des produits sans options de sourcing
- [x] Utilisation du SourcingMatcher pour trouver des options
- [x] Création des options en base de données
- [x] Logging complet et gestion d'erreurs
- [x] Statistiques de traitement

#### WM-2.5 : API Endpoints Module B ✅
- [x] `POST /api/v1/jobs/sourcing/run` - Lancer le job de sourcing
- [x] `GET /api/v1/products/{product_id}/sourcing_options` - Récupérer les options d'un produit
- [x] Modèles Pydantic pour les réponses
- [x] Documentation OpenAPI complète
- [x] Tests unitaires

**Statut : ✅ TERMINÉ (Production Ready V1)**

**Définition de "Terminé"** : ✅
- ✅ Modèle SourcingOption créé avec migration Alembic
- ✅ Configuration fournisseurs (YAML + CSV de démo)
- ✅ Service de matching par mots-clés fonctionnel
- ✅ Job de sourcing créant automatiquement les options
- ✅ API fonctionnelle avec gestion d'erreurs
- ✅ Tests unitaires complets
- ✅ Documentation mise à jour

#### WM-2.6 : Workflows n8n
- [ ] `workflows/b/find-suppliers.json` - Recherche auto
- [ ] `workflows/b/verify-supplier.json` - Vérification manuelle

**Définition de "Terminé"** :
- Fournisseurs trouvés automatiquement pour chaque produit
- Options de sourcing stockées et évaluées
- API fonctionnelle
- Workflows n8n opérationnels

---

## 📊 Epic WM-3 : Module C - Scoring

**Description** : Implémenter le système de scoring intelligent des produits.

**Durée estimée** : 2-3 semaines

**Prérequis** : WM-1 et WM-2 terminés (données produits + sourcing)

### Tâches détaillées

#### WM-3.1 : Modèle de données ProductScore
- [ ] Créer la table `product_scores`
- [ ] Définir les scores :
  - [ ] Score global
  - [ ] Rentabilité
  - [ ] Compétition
  - [ ] Tendance
  - [ ] Sourcing
  - [ ] Taille de marché
- [ ] Créer les modèles backend

#### WM-3.2 : Calcul de rentabilité
- [ ] Formule : (Prix de vente - Coût sourcing - Frais Amazon) / Coût sourcing
- [ ] Prendre en compte les frais de port
- [ ] Calculer la marge brute
- [ ] Calculer la marge nette estimée

#### WM-3.3 : Analyse de compétition
- [ ] Analyser le nombre de vendeurs
- [ ] Analyser la saturation des reviews
- [ ] Analyser la diversité des prix
- [ ] Score : 0-100 (100 = faible compétition)

#### WM-3.4 : Détection de tendances
- [ ] Analyser l'évolution du BSR
- [ ] Analyser l'évolution des reviews
- [ ] Analyser les saisonnalités
- [ ] Score : 0-100 (100 = tendance forte)

#### WM-3.5 : Score de sourcing
- [ ] Basé sur les options de sourcing disponibles
- [ ] Prendre en compte le prix, MOQ, délai
- [ ] Score : 0-100

#### WM-3.6 : Score global pondéré
- [ ] Définir les poids de chaque score
- [ ] Implémenter le calcul global
- [ ] Permettre la configuration des poids

#### WM-3.7 : API Endpoints Module C
- [ ] `POST /api/v1/scoring/calculate/:productId` - Calculer
- [ ] `GET /api/v1/scoring/scores` - Lister avec filtres
- [ ] `GET /api/v1/scoring/scores/:id` - Détails
- [ ] `GET /api/v1/scoring/config` - Configurer les poids
- [ ] Tests unitaires

#### WM-3.8 : Jobs automatiques
- [ ] Job déclenché après découverte produit
- [ ] Job de recalcul périodique

#### WM-3.9 : Workflow n8n
- [ ] `workflows/c/calculate-score.json` - Calcul automatique

**Définition de "Terminé"** :
- Scoring automatique pour chaque produit
- Scores détaillés stockés
- API fonctionnelle
- Workflow n8n opérationnel

---

## 📝 Epic WM-4 : Module D - Création de listings

**Description** : Générer des listings Amazon optimisés à partir de templates.

**Durée estimée** : 2-3 semaines

**Prérequis** : WM-1 terminé (avoir des produits avec données)

### Tâches détaillées

#### WM-4.1 : Modèle de données ListingTemplate
- [ ] Créer la table `listing_templates`
- [ ] Support templates brandable et non-brandable
- [ ] Stocker les templates (titre, bullets, description)
- [ ] Créer les modèles backend

#### WM-4.2 : Système de templates
- [ ] Créer l'éditeur de templates (API ou interface)
- [ ] Support de variables ({{product_name}}, {{features}}, etc.)
- [ ] Validation des templates
- [ ] CRUD complet

#### WM-4.3 : Génération de contenu
- [ ] Parser les templates avec variables
- [ ] Générer le titre optimisé SEO
- [ ] Générer les bullet points (5)
- [ ] Générer la description longue
- [ ] Extraire les keywords pertinents

#### WM-4.4 : Optimisation SEO
- [ ] Recherche de keywords pertinents
- [ ] Intégration keywords dans titre/bullets/description
- [ ] Respect des limites Amazon (caractères)

#### WM-4.5 : Gestion d'images
- [ ] Récupérer les images produits
- [ ] Redimensionner si nécessaire
- [ ] Optimiser pour Amazon
- [ ] Générer les variantes (si nécessaire)

#### WM-4.6 : API Endpoints Module D
- [ ] `GET /api/v1/listings/templates` - Lister templates
- [ ] `POST /api/v1/listings/templates` - Créer template
- [ ] `PUT /api/v1/listings/templates/:id` - Modifier
- [ ] `DELETE /api/v1/listings/templates/:id` - Supprimer
- [ ] `POST /api/v1/listings/generate` - Générer listing
- [ ] `GET /api/v1/listings/generated/:id` - Voir listing généré
- [ ] Tests unitaires

#### WM-4.7 : Jobs automatiques
- [ ] Job de génération après validation produit

#### WM-4.8 : Workflow n8n
- [ ] `workflows/d/generate-listing.json` - Génération auto

**Définition de "Terminé"** :
- Templates créables et modifiables
- Listings générés automatiquement
- Contenu optimisé SEO
- API fonctionnelle

---

## 📦 Epic WM-5 : Module E - Gestion des bundles

**Description** : Créer et gérer des bundles de produits.

**Durée estimée** : 1-2 semaines

**Prérequis** : WM-1 terminé (avoir des produits)

### Tâches détaillées

#### WM-5.1 : Modèle de données Bundle
- [ ] Créer la table `bundles`
- [ ] Table de liaison many-to-many `bundle_products`
- [ ] Créer les modèles backend

#### WM-5.2 : Création de bundles
- [ ] Interface de sélection de produits
- [ ] Calcul automatique du prix optimal
- [ ] Calcul du pourcentage de réduction
- [ ] Validation (cohérence produits)

#### WM-5.3 : Calcul de prix
- [ ] Prix = Somme des produits individuels
- [ ] Prix bundle = Prix - Réduction configurable
- [ ] Afficher l'économie pour le client

#### WM-5.4 : API Endpoints Module E
- [ ] `GET /api/v1/bundles` - Lister
- [ ] `POST /api/v1/bundles` - Créer
- [ ] `GET /api/v1/bundles/:id` - Détails
- [ ] `PUT /api/v1/bundles/:id` - Modifier
- [ ] `DELETE /api/v1/bundles/:id` - Supprimer
- [ ] Tests unitaires

#### WM-5.5 : Workflow n8n
- [ ] `workflows/e/create-bundle.json` - Création assistée

**Définition de "Terminé"** :
- Bundles créables et modifiables
- Calcul de prix automatique
- API fonctionnelle

---

## 🛒 Epic WM-6 : Module F - Publication Amazon

**Description** : Publier les listings sur Amazon via API Seller Central.

**Durée estimée** : 3-4 semaines

**Prérequis** : WM-4 et WM-5 terminés (listings générés + bundles)

### Tâches détaillées

#### WM-6.1 : Modèle de données MarketplaceListing
- [ ] Créer la table `marketplace_listings`
- [ ] Relations avec products, bundles, templates
- [ ] Suivi du statut (draft, pending, live, etc.)
- [ ] Créer les modèles backend

#### WM-6.2 : Intégration Amazon Seller Central API
- [ ] Obtenir les credentials API Amazon
- [ ] Créer le client API (SP-API)
- [ ] Comprendre le modèle de données Amazon
- [ ] Implémenter l'authentification OAuth

#### WM-6.3 : Upload de produits
- [ ] Mapper les données locales → format Amazon
- [ ] Upload via API (CreateProduct ou Feeds)
- [ ] Gérer les erreurs de validation
- [ ] Suivre le statut d'upload

#### WM-6.4 : Upload d'images
- [ ] Upload images vers Amazon S3 (ou API)
- [ ] Associer images aux listings
- [ ] Gérer les variantes d'images

#### WM-6.5 : Gestion des stocks
- [ ] Synchroniser les stocks
- [ ] Mettre à jour les quantités
- [ ] Gérer les ruptures de stock

#### WM-6.6 : Synchronisation des prix
- [ ] Mettre à jour les prix
- [ ] Gérer les promotions
- [ ] Synchronisation périodique

#### WM-6.7 : Gestion des commandes
- [ ] Récupérer les commandes Amazon
- [ ] Stocker localement
- [ ] Notifications nouvelles commandes

#### WM-6.8 : API Endpoints Module F
- [ ] `POST /api/v1/amazon/publish` - Publier listing
- [ ] `GET /api/v1/amazon/listings` - Lister listings publiés
- [ ] `GET /api/v1/amazon/listings/:id` - Détails
- [ ] `PUT /api/v1/amazon/listings/:id/sync` - Synchroniser
- [ ] `GET /api/v1/amazon/orders` - Récupérer commandes
- [ ] Tests unitaires

#### WM-6.9 : Jobs automatiques
- [ ] Job horaire : Sync stocks et prix
- [ ] Job quotidien : Récupération commandes
- [ ] Job de retry pour uploads échoués

#### WM-6.10 : Workflows n8n
- [ ] `workflows/f/publish-to-amazon.json` - Publication
- [ ] `workflows/f/sync-listings.json` - Synchronisation

**Définition de "Terminé"** :
- Listings publiés automatiquement sur Amazon
- Synchronisation stocks/prix fonctionnelle
- Commandes récupérées automatiquement
- API fonctionnelle

---

## 🤖 Epic WM-7 : Module G - SAV automatisé KeyBuzz

**Description** : Automatiser le service après-vente via KeyBuzz avec boucle de feedback.

**Durée estimée** : 3-4 semaines

**Prérequis** : WM-6 terminé (produits publiés sur Amazon)

### Tâches détaillées

#### WM-7.1 : Modèles de données (KBProductKnowledge, ProductFeedback)
- [ ] Créer la table `kb_product_knowledge`
- [ ] Créer la table `product_feedback`
- [ ] Relations avec products et listings
- [ ] Créer les modèles backend

#### WM-7.2 : Intégration KeyBuzz API
- [ ] Obtenir les credentials KeyBuzz
- [ ] Créer le client API KeyBuzz
- [ ] Comprendre le modèle de données KeyBuzz
- [ ] Implémenter l'authentification

#### WM-7.3 : Gestion des connaissances produit
- [ ] Récupérer les connaissances depuis KeyBuzz
- [ ] Stocker localement
- [ ] CRUD des connaissances
- [ ] Catégorisation (FAQ, troubleshooting, specs)

#### WM-7.4 : Monitoring des tickets
- [ ] Surveiller les nouveaux tickets KeyBuzz
- [ ] Classifier les tickets (type, urgence)
- [ ] Déclencher les réponses automatiques

#### WM-7.5 : Réponses automatiques
- [ ] Matching ticket ↔ connaissances
- [ ] Générer réponse automatique
- [ ] Score de confiance de la réponse
- [ ] Envoi de réponse si confiance > seuil

#### WM-7.6 : Escalade vers humain
- [ ] Définir les critères d'escalade
- [ ] Notifier l'équipe si nécessaire
- [ ] Traçabilité de l'escalade

#### WM-7.7 : Boucle de feedback
- [ ] Collecter les feedbacks clients (Amazon reviews, KeyBuzz)
- [ ] Analyser le sentiment
- [ ] Extraire les insights
- [ ] Mettre à jour les connaissances
- [ ] Améliorer les réponses automatiques

#### WM-7.8 : API Endpoints Module G
- [ ] `GET /api/v1/keybuzz/knowledge` - Lister connaissances
- [ ] `POST /api/v1/keybuzz/knowledge` - Ajouter
- [ ] `PUT /api/v1/keybuzz/knowledge/:id` - Modifier
- [ ] `GET /api/v1/keybuzz/tickets` - Lister tickets
- [ ] `GET /api/v1/keybuzz/tickets/:id` - Détails
- [ ] `POST /api/v1/keybuzz/feedback` - Enregistrer feedback
- [ ] Tests unitaires

#### WM-7.9 : Jobs automatiques
- [ ] Job continu : Monitoring tickets
- [ ] Job horaire : Traitement réponses auto
- [ ] Job quotidien : Analyse feedbacks et mise à jour connaissances

#### WM-7.10 : Workflows n8n
- [ ] `workflows/g/monitor-keybuzz.json` - Monitoring
- [ ] `workflows/g/auto-respond.json` - Réponses auto
- [ ] `workflows/g/feedback-loop.json` - Boucle feedback

**Définition de "Terminé"** :
- Tickets KeyBuzz surveillés automatiquement
- Réponses automatiques fonctionnelles
- Boucle de feedback opérationnelle
- Connaissances mises à jour automatiquement
- API fonctionnelle

---

## 📊 Vue d'ensemble des dépendances

```
WM-0 (Infra) 
    ↓
WM-1 (Recherche produits)
    ↓
WM-2 (Sourcing) ────┐
    ↓                │
WM-3 (Scoring) ←────┘
    ↓
WM-4 (Listings)
    ↓
WM-5 (Bundles)
    ↓
WM-6 (Publication Amazon)
    ↓
WM-7 (SAV KeyBuzz)
```

---

## 🚀 Ordre de développement recommandé

1. **WM-0** : Infrastructure (Blocage si non fait)
2. **WM-1** : Recherche produits (Fondation)
3. **WM-2** : Sourcing (Parallèle possible avec WM-3)
4. **WM-3** : Scoring (Besoin de WM-1 + WM-2)
5. **WM-4** : Listings (Besoin de WM-1)
6. **WM-5** : Bundles (Besoin de WM-1, peut être en parallèle de WM-4)
7. **WM-6** : Publication (Besoin de WM-4 + WM-5)
8. **WM-7** : SAV (Besoin de WM-6, produits publiés)

---

## 📝 Notes pour les développeurs

### Par où commencer ?

1. **Lire** : `README_project_overview.md` pour la vision globale
2. **Lire** : `architecture_v1.md` pour l'architecture technique
3. **Commencer** : Par l'epic WM-0 (Infrastructure)
4. **Suivre** : L'ordre des epics (WM-0 → WM-7)

### Créer les tâches dans Linear

- Créer un epic pour chaque WM-X
- Créer une tâche pour chaque sous-point (WM-X.Y)
- Ajouter les labels : `backend`, `frontend`, `n8n`, `database`, etc.
- Estimer la complexité (Story Points)
- Assigner les priorités

### Définition de "Done"

Chaque epic a sa propre définition de "Done" listée à la fin.

---

*Document à maintenir à jour au fur et à mesure du développement*

