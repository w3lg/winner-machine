"""
Configuration de la base de données SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# Créer l'engine SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Utiliser NullPool pour éviter les problèmes avec les migrations
    echo=settings.DEBUG,  # Afficher les requêtes SQL en mode debug
)

# Créer la session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency pour obtenir une session de base de données.

    Yields:
        Session SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

