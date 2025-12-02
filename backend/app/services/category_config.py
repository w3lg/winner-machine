"""
Service de gestion de la configuration des catégories Amazon.

Charge et parse le fichier YAML de configuration des catégories.
"""
import yaml
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel


class CategoryConfig(BaseModel):
    """Configuration d'une catégorie Amazon."""

    id: int
    name: str
    marketplace: str
    bsr_max: int
    price_min: float
    price_max: float
    active: bool = True


class CategoryConfigService:
    """Service pour charger et gérer la configuration des catégories."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialise le service avec le chemin vers le fichier de config.

        Args:
            config_path: Chemin vers le fichier YAML. Si None, utilise le chemin par défaut.
        """
        if config_path is None:
            # Chemin par défaut : depuis la racine de l'app
            base_path = Path(__file__).parent.parent.parent
            config_path = base_path / "app" / "config" / "category_config.yml"
        self.config_path = config_path
        self._categories: Optional[List[CategoryConfig]] = None

    def load_categories(self) -> List[CategoryConfig]:
        """
        Charge les catégories depuis le fichier YAML.

        Returns:
            Liste des configurations de catégories.
        """
        if self._categories is not None:
            return self._categories

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        categories = []
        for cat_data in data.get("categories", []):
            if cat_data.get("active", True):
                categories.append(CategoryConfig(**cat_data))

        self._categories = categories
        return categories

    def get_active_categories(self) -> List[CategoryConfig]:
        """
        Retourne uniquement les catégories actives.

        Returns:
            Liste des catégories actives.
        """
        return [cat for cat in self.load_categories() if cat.active]

    def get_category_by_id(self, category_id: int) -> Optional[CategoryConfig]:
        """
        Retourne une catégorie par son ID.

        Args:
            category_id: ID de la catégorie Keepa.

        Returns:
            Configuration de la catégorie ou None si non trouvée.
        """
        for cat in self.load_categories():
            if cat.id == category_id:
                return cat
        return None


# Instance singleton
_category_config_service: Optional[CategoryConfigService] = None


def get_category_config_service() -> CategoryConfigService:
    """
    Retourne une instance singleton du service de configuration.

    Returns:
        Instance de CategoryConfigService.
    """
    global _category_config_service
    if _category_config_service is None:
        _category_config_service = CategoryConfigService()
    return _category_config_service

