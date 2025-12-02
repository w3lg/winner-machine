# Winner Machine v1

Machine complète de recherche, analyse et commercialisation de produits gagnants sur Amazon France.

## 📋 Vue d'ensemble

Winner Machine v1 automatise l'ensemble du processus de découverte, analyse et commercialisation de produits sur Amazon :
- 🔍 Recherche automatique de produits gagnants
- 🏭 Sourcing de fournisseurs
- 📊 Scoring intelligent
- 📝 Génération de listings optimisés
- 📦 Gestion de bundles
- 🛒 Publication sur Amazon
- 🤖 SAV automatisé via KeyBuzz

## 🏗️ Architecture

Le projet est découpé en **7 modules** interconnectés :

- **Module A** : Recherche de produits
- **Module B** : Sourcing
- **Module C** : Scoring
- **Module D** : Création de listings
- **Module E** : Gestion des bundles
- **Module F** : Publication Amazon
- **Module G** : SAV automatisé KeyBuzz

### Infrastructure V1

- **Serveur** : marcus (135.181.253.60)
- **Backend** : FastAPI (Python)
- **Base de données** : PostgreSQL
- **Workflows** : n8n
- **Reverse Proxy** : nginx
- **Domaines** :
  - `marcus.wlg.fr` → Backend
  - `n8n.w3lg.fr` → n8n

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Accès au serveur marcus (pour le déploiement)

### Lancer en local

```bash
# 1. Cloner le repository
git clone https://github.com/w3lg/winner-machine.git
cd winner-machine

# 2. Configurer l'environnement
cp infra/.env.example infra/.env
# Éditez infra/.env avec vos valeurs

# 3. Lancer les services
cd infra
docker-compose up -d

# 4. Vérifier
curl http://localhost:8000/health
```

Voir `backend/README.md` pour plus de détails sur le développement local.

## 📁 Structure du projet

```
winner-machine/
├── backend/              # Backend FastAPI
│   ├── app/             # Code de l'application
│   ├── alembic/         # Migrations de base de données
│   └── tests/           # Tests
├── infra/               # Infrastructure
│   ├── docker-compose.yml
│   ├── nginx/           # Configuration nginx
│   └── sql/             # Scripts SQL optionnels
├── n8n/                 # Workflows n8n
│   └── workflows/
├── docs/                # Documentation
│   ├── README_project_overview.md
│   ├── architecture_v1.md
│   └── linear_epics.md
└── README.md            # Ce fichier
```

## 📖 Documentation

- **Vue d'ensemble** : [`docs/README_project_overview.md`](docs/README_project_overview.md)
- **Architecture technique** : [`docs/architecture_v1.md`](docs/architecture_v1.md)
- **Plan de développement** : [`docs/linear_epics.md`](docs/linear_epics.md)
- **Backend** : [`backend/README.md`](backend/README.md)

## 🔧 Technologies

- **Backend** : Python 3.11+ avec FastAPI
- **Base de données** : PostgreSQL 16
- **ORM** : SQLAlchemy + Alembic
- **Workflows** : n8n
- **Containerisation** : Docker + Docker Compose
- **Reverse Proxy** : nginx

## 🛣️ Roadmap

Le développement est organisé en **8 epics** (WM-0 à WM-7) :

- **WM-0** : Infrastructure & Setup ✅
- **WM-1** : Module A - Recherche de produits
- **WM-2** : Module B - Sourcing
- **WM-3** : Module C - Scoring
- **WM-4** : Module D - Création de listings
- **WM-5** : Module E - Gestion des bundles
- **WM-6** : Module F - Publication Amazon
- **WM-7** : Module G - SAV automatisé KeyBuzz

Voir [`docs/linear_epics.md`](docs/linear_epics.md) pour le détail des tâches.

## 🔐 Sécurité

- Les fichiers de configuration locale sont dans `_local_config/` (ignorés par Git)
- Les tokens et clés API ne doivent jamais être commités
- Utilisez des variables d'environnement pour tous les secrets

## 📝 Licence

Propriétaire - w3lg

## 👥 Équipe

- **w3lg** - Développement

---

*Version 1.0.0 - Décembre 2025*

