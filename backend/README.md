# Winner Machine Backend

Backend API pour Winner Machine v1 - FastAPI + PostgreSQL

## 📋 Prérequis

- Docker et Docker Compose
- Python 3.11+ (pour développement local sans Docker)

## 🚀 Démarrage rapide avec Docker

### 1. Configuration

Créez un fichier `.env` à la racine du projet (`infra/.env`) avec les variables nécessaires :

```bash
cp infra/.env.example infra/.env
# Éditez infra/.env et remplissez les valeurs
```

Ou utilisez les valeurs par défaut du `docker-compose.yml`.

### 2. Lancer les services

Depuis le dossier `infra/` :

```bash
cd infra
docker-compose up -d
```

Cela démarre :
- **PostgreSQL** sur le port 5432
- **Backend FastAPI** sur le port 8000
- **n8n** sur le port 5678

### 3. Vérifier que tout fonctionne

```bash
# Health check
curl http://localhost:8000/health

# Documentation API (si DEBUG=true)
open http://localhost:8000/docs
```

### 4. Migrations de base de données

Les migrations Alembic sont gérées automatiquement, mais vous pouvez aussi les lancer manuellement :

```bash
# Entrer dans le container
docker-compose exec app bash

# Créer une nouvelle migration
alembic revision --autogenerate -m "Description de la migration"

# Appliquer les migrations
alembic upgrade head
```

## 🛠️ Développement local (sans Docker)

### 1. Installation des dépendances

```bash
# Installer Poetry si ce n'est pas déjà fait
pip install poetry

# Installer les dépendances
poetry install
```

### 2. Configuration

Créez un fichier `.env` à la racine de `backend/` :

```bash
cp .env.example .env
# Éditez .env avec vos valeurs
```

### 3. Base de données locale

Assurez-vous qu'une instance PostgreSQL est en cours d'exécution et accessible avec les credentials du `.env`.

### 4. Migrations

```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head
```

### 5. Lancer l'application

```bash
# Avec Poetry
poetry run uvicorn app.main:app --reload

# Ou directement avec Python
uvicorn app.main:app --reload
```

L'API sera accessible sur http://localhost:8000

## 📁 Structure du projet

```
backend/
├── app/
│   ├── api/           # Routes API (à venir)
│   ├── core/          # Configuration et utilitaires de base
│   ├── models/        # Modèles SQLAlchemy
│   ├── services/      # Logique métier
│   ├── jobs/          # Jobs/tâches planifiées
│   ├── config/        # Configuration supplémentaire
│   └── main.py        # Point d'entrée FastAPI
├── alembic/           # Migrations de base de données
├── tests/             # Tests
├── pyproject.toml     # Dépendances Python
├── Dockerfile         # Image Docker
└── README.md          # Ce fichier
```

## 🔧 Commandes utiles

### Docker

```bash
# Voir les logs
docker-compose logs -f app

# Redémarrer un service
docker-compose restart app

# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v
```

### Alembic (migrations)

```bash
# Créer une migration
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1

# Voir l'historique
alembic history
```

## 🧪 Tests

```bash
# Lancer les tests
poetry run pytest

# Avec couverture
poetry run pytest --cov=app
```

## 📝 Notes

- Le backend écoute sur le port **8000** (pas 3000 comme mentionné initialement dans l'archi)
- Les migrations Alembic doivent être créées et appliquées avant de démarrer l'app
- Les variables d'environnement sont chargées depuis `.env` via `pydantic-settings`

## 🔗 Documentation

- Documentation API interactive : http://localhost:8000/docs (si DEBUG=true)
- Documentation ReDoc : http://localhost:8000/redoc (si DEBUG=true)

