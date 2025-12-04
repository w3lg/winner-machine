"""
Configuration de l'application Winner Machine.

Gère la lecture des variables d'environnement et la configuration de l'application.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application via variables d'environnement."""

    # Application
    APP_ENV: str = "dev"  # dev, staging, prod
    
    # Ces valeurs peuvent être surchargées via variables d'environnement
    DEBUG: Optional[bool] = None  # Auto-déterminé depuis APP_ENV si None
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    API_V1_PREFIX: str = "/api/v1"
    
    @property
    def ENVIRONMENT(self) -> str:
        """Retourne l'environnement basé sur APP_ENV."""
        env_map = {
            "dev": "development",
            "staging": "staging",
            "prod": "production",
        }
        return env_map.get(self.APP_ENV.lower(), "development")
    
    @property
    def is_debug(self) -> bool:
        """Retourne True si en mode debug."""
        if self.DEBUG is not None:
            return self.DEBUG
        # Auto-déterminé depuis APP_ENV
        return not self.is_production

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "winner_machine"
    POSTGRES_PASSWORD: str = "winner_machine_dev"
    POSTGRES_DB: str = "winner_machine"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construit l'URL de connexion à la base de données."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # API Keys
    KEEPA_API_KEY: Optional[str] = None
    AMAZON_SP_API_CLIENT_ID: Optional[str] = None
    AMAZON_SP_API_CLIENT_SECRET: Optional[str] = None
    KEYBUZZ_API_KEY: Optional[str] = None
    APIFY_API_KEY: Optional[str] = None
    
    # Amazon Selling Partner API (SP-API) Configuration
    SPAPI_LWA_CLIENT_ID: Optional[str] = None
    SPAPI_LWA_CLIENT_SECRET: Optional[str] = None
    SPAPI_LWA_REFRESH_TOKEN: Optional[str] = None
    SPAPI_ROLE_ARN: Optional[str] = None
    SPAPI_SELLER_ID: Optional[str] = None
    SPAPI_REGION: str = "eu-west-1"
    SPAPI_MARKETPLACE_ID_FR: str = "A13V1IB3VIYZZH"
    
    # Listing & Branding
    DEFAULT_BRAND_NAME: str = "YOUR_BRAND"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    @property
    def is_production(self) -> bool:
        """Retourne True si on est en production."""
        return self.APP_ENV.lower() == "prod"

    @property
    def is_development(self) -> bool:
        """Retourne True si on est en développement."""
        return self.APP_ENV.lower() == "dev"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Retourne une instance singleton des settings."""
    return Settings()

