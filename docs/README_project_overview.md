# Winner Machine v1 - Vue d'ensemble du projet

## 📋 Introduction

**Winner Machine v1** est une plateforme complète de recherche, analyse et commercialisation de produits gagnants sur Amazon France. Le système automatise l'ensemble du processus, de la découverte de produits prometteurs jusqu'à la gestion du service client après-vente.

## 🎯 Vision et objectifs

### Objectif principal

Construire une machine complète qui permet de :
1. **Rechercher** des produits gagnants sur Amazon FR avec des critères intelligents
2. **Sourcer** ces produits auprès de fournisseurs fiables
3. **Scorer** les produits selon des critères business (rentabilité, compétition, tendances)
4. **Créer** des listings Amazon optimisés (brandable ou non)
5. **Gérer** des bundles de produits
6. **Publier** automatiquement sur Amazon
7. **Automatiser** le SAV via KeyBuzz avec une boucle de feedback continue

### Valeur ajoutée

- Automatisation complète du processus de sélection de produits
- Décisions data-driven avec scoring intelligent
- Intégration native avec Amazon et KeyBuzz
- Workflows n8n pour l'automatisation des processus métier

## 🏗️ Architecture générale

### Infrastructure V1

Pour cette première version, tout tourne sur un **serveur unique** :

- **Serveur** : `marcus`
- **IP** : `135.181.253.60`
- **SSH** : Port 22
- **Domaines** :
  - `https://marcus.wlg.fr` → Backend / Interface par défaut
  - `https://n8n.w3lg.fr` → n8n (automation workflows)
- **Certificats** : Let's Encrypt via nginx + certbot

### Modules fonctionnels (A → G)

Le système est découpé en **7 modules** interconnectés :

- **Module A** : Recherche de produits (Product Discovery) ✅ **TERMINÉ (Production Ready V1)**
  
  **Fonctionnalités implémentées** :
  - Découverte automatique de produits via l'API Keepa (Amazon FR)
  - Configuration de catégories via YAML (BSR, prix, etc.)
  - Stockage des produits candidats en base (`ProductCandidate`)
  - Endpoint HTTP `POST /api/v1/jobs/discover/run` pour lancer la découverte
  - Job avec logging complet et gestion d'erreurs robuste
  - Workflow n8n configuré (cron quotidien à 03:00)
  - Mode mock intégré (développement sans clé API)
  - Tests unitaires complets
  
  **Utilisation** :
  - **Manuel** : `curl -X POST http://localhost:8000/api/v1/jobs/discover/run`
  - **Automatique** : Workflow n8n importé et activé
  
  **Documentation** :
  - Détails techniques : `docs/architecture_v1.md` (section Module A)
  - Implémentation : `MODULE_A_IMPLEMENTE.md`
  - Workflows n8n : `N8N_WORKFLOWS.md`

- **Module B** : Sourcing ✅ **TERMINÉ**
  
  **Fonctionnalités implémentées** :
  - Matching de produits candidats avec catalogues fournisseurs (CSV)
  - Configuration des fournisseurs via YAML (`suppliers.yml`)
  - Service de matching par mots-clés (titre, catégorie)
  - Job de sourcing pour créer automatiquement les options
  - Stockage des options de sourcing en base (`SourcingOption`)
  - Endpoints HTTP pour lancer le job et récupérer les options
  
  **Utilisation** :
  - **Manuel** : `curl -X POST http://localhost:8000/api/v1/jobs/sourcing/run`
  - **Récupérer options** : `curl http://localhost:8000/api/v1/products/{id}/sourcing_options`
  
  **Documentation** :
  - Détails techniques : `docs/architecture_v1.md` (section Module B)

- **Module C** : Scoring
- **Module D** : Création de listings
- **Module E** : Gestion des bundles
- **Module F** : Publication Amazon
- **Module G** : SAV automatisé avec KeyBuzz

> 📖 Voir `architecture_v1.md` pour les détails techniques de chaque module.

## 📊 Modèle de données

### Entités principales

Le système manipule les entités suivantes :

- **ProductCandidate** : Produit candidat découvert
- **SourcingOption** : Option de sourcing pour un produit
- **ProductScore** : Score calculé pour un produit
- **ListingTemplate** : Template de listing Amazon
- **Bundle** : Bundle de produits
- **MarketplaceListing** : Listing publié sur Amazon
- **KBProductKnowledge** : Connaissances produit issues de KeyBuzz
- **ProductFeedback** : Feedback client

> 📖 Voir `architecture_v1.md` pour le schéma de base de données complet.

## 🚀 Roadmap de développement

Le développement est organisé en **8 epics** (WM-0 à WM-7) :

- **WM-0** : Infrastructure & Setup
- **WM-1** : Module A - Recherche de produits
- **WM-2** : Module B - Sourcing
- **WM-3** : Module C - Scoring
- **WM-4** : Module D - Création de listings
- **WM-5** : Module E - Gestion des bundles
- **WM-6** : Module F - Publication Amazon
- **WM-7** : Module G - SAV automatisé KeyBuzz

> 📖 Voir `linear_epics.md` pour le détail des tâches par epic.

## 👥 Pour qui ?

### Nouveau développeur

1. Lire ce document (README_project_overview.md) pour comprendre la vision
2. Consulter `architecture_v1.md` pour l'architecture technique
3. Suivre `linear_epics.md` pour savoir par où commencer
4. Se connecter au serveur `marcus` et explorer l'environnement

### Associé / Investisseur

Ce document donne une vue d'ensemble business et technique du projet sans entrer dans les détails d'implémentation.

## 🔗 Ressources

- **Documentation technique** : `docs/architecture_v1.md`
- **Plan de développement** : `docs/linear_epics.md`
- **Repository GitHub** : https://github.com/w3lg/winner-machine
- **Serveur** : https://marcus.wlg.fr
- **n8n** : https://n8n.w3lg.fr

## 📝 Notes importantes

- **Version V1** : Tout est centralisé sur un seul serveur pour simplifier le déploiement initial
- **Évolutivité** : L'architecture est pensée pour pouvoir évoluer vers une architecture distribuée en V2
- **Modularité** : Chaque module peut être développé et testé indépendamment

---

*Dernière mise à jour : Décembre 2025*

