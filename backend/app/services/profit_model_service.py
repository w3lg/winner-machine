"""
Service pour charger et gérer la configuration du modèle de profit par marketplace.
"""
import logging
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class ProfitModelService:
    """Service pour charger et gérer la configuration du modèle de profit."""

    _instance: Optional["ProfitModelService"] = None
    _profit_config: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProfitModelService, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _get_config_path(self) -> Path:
        """Retourne le chemin du fichier de configuration."""
        base_path = Path(__file__).parent.parent.parent
        return base_path / "app" / "config" / "profit_model.yml"

    def _load_config(self):
        """Charge la configuration depuis le fichier YAML."""
        config_path = self._get_config_path()
        if not config_path.exists():
            logger.warning(
                f"Fichier de configuration profit_model.yml non trouvé: {config_path}. "
                "Utilisation des valeurs par défaut."
            )
            self._profit_config = {}
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._profit_config = yaml.safe_load(f) or {}
            logger.info(f"Configuration profit_model chargée depuis {config_path}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de profit_model.yml: {e}", exc_info=True)
            self._profit_config = {}

    def get_marketplace_config(self, marketplace_code: str = "fr") -> Dict[str, Any]:
        """
        Retourne la configuration du modèle de profit pour un marketplace.

        Args:
            marketplace_code: Code du marketplace (ex: "fr", "de", "es").

        Returns:
            Dict avec la configuration ou valeurs par défaut.
        """
        if not self._profit_config:
            return self._get_default_config()

        marketplace_config = self._profit_config.get(marketplace_code, {})

        if not marketplace_config:
            logger.warning(
                f"Configuration non trouvée pour le marketplace '{marketplace_code}', "
                "utilisation des valeurs par défaut"
            )
            return self._get_default_config()

        # Merge avec les valeurs par défaut pour s'assurer que tous les champs sont présents
        default = self._get_default_config()
        default.update(marketplace_config)
        return default

    def _get_default_config(self) -> Dict[str, Any]:
        """Retourne la configuration par défaut."""
        return {
            "enabled": False,
            "tax_factor_after_is_cfe": 0.7,
            "default_shipping_cost_per_unit": 5.0,
            "tva_rate": 0.20,
        }


@lru_cache()
def get_profit_model_service() -> ProfitModelService:
    """Retourne une instance singleton du service de configuration du modèle de profit."""
    return ProfitModelService()



