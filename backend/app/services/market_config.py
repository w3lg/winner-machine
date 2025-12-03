"""
Service de gestion de la configuration des marchés Amazon et leurs listes d'ASINs.
"""
import logging
import yaml
from pathlib import Path
from typing import List, Optional, Dict

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MarketConfig(BaseModel):
    """Configuration d'un marché Amazon."""

    domain: int  # Domain Keepa (1=FR, 3=DE, 9=ES, etc.)
    label: str  # Nom du marché (ex: "France")
    active: bool = True
    asins: List[str] = []  # Liste d'ASINs pour ce marché


class MarketConfigService:
    """Service pour charger et gérer la configuration des marchés."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialise le service avec le chemin vers le fichier de config.

        Args:
            config_path: Chemin vers le fichier YAML. Si None, utilise le chemin par défaut.
        """
        if config_path is None:
            # Chemin par défaut : depuis la racine de l'app
            base_path = Path(__file__).parent.parent.parent
            config_path = base_path / "app" / "config" / "markets_asins.yml"
        self.config_path = config_path
        self._markets: Optional[Dict[str, MarketConfig]] = None

    def load_markets(self) -> Dict[str, MarketConfig]:
        """
        Charge les marchés depuis le fichier YAML.

        Returns:
            Dictionnaire {code_market: MarketConfig}.
        """
        if self._markets is not None:
            return self._markets

        if not self.config_path.exists():
            logger.warning(
                f"Fichier de configuration des marchés non trouvé: {self.config_path}. "
                "Aucun marché ne sera disponible."
            )
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            markets = {}
            for market_code, market_data in data.get("markets", {}).items():
                try:
                    market_config = MarketConfig(**market_data)
                    markets[market_code] = market_config
                    logger.debug(
                        f"Marché chargé: {market_code} ({market_config.label}) - "
                        f"{len(market_config.asins)} ASINs"
                    )
                except Exception as e:
                    logger.error(
                        f"Erreur lors du chargement du marché {market_code}: {str(e)}"
                    )
                    continue

            self._markets = markets
            logger.info(
                f"Chargement de {len(markets)} marché(s) depuis {self.config_path}"
            )
            return markets

        except yaml.YAMLError as e:
            logger.error(f"Erreur de parsing YAML dans {self.config_path}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(
                f"Erreur lors du chargement de la configuration des marchés: {str(e)}",
                exc_info=True,
            )
            return {}

    def get_all_markets(self) -> Dict[str, MarketConfig]:
        """
        Retourne tous les marchés chargés.

        Returns:
            Dictionnaire {code_market: MarketConfig}.
        """
        return self.load_markets()

    def get_active_markets(self) -> Dict[str, MarketConfig]:
        """
        Retourne uniquement les marchés actifs.

        Returns:
            Dictionnaire {code_market: MarketConfig} pour les marchés actifs.
        """
        all_markets = self.load_markets()
        return {
            code: market
            for code, market in all_markets.items()
            if market.active
        }

    def get_market_by_code(self, market_code: str) -> Optional[MarketConfig]:
        """
        Retourne un marché par son code.

        Args:
            market_code: Code du marché (ex: "amazon_fr").

        Returns:
            Configuration du marché ou None si non trouvée.
        """
        markets = self.load_markets()
        return markets.get(market_code)


# Instance singleton
_market_config_service: Optional[MarketConfigService] = None


def get_market_config_service() -> MarketConfigService:
    """
    Retourne l'instance singleton du service de configuration des marchés.

    Returns:
        Instance de MarketConfigService.
    """
    global _market_config_service
    if _market_config_service is None:
        _market_config_service = MarketConfigService()
    return _market_config_service

