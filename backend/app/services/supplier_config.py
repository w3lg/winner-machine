"""
Service de gestion de la configuration des fournisseurs.

Charge et parse le fichier YAML de configuration des fournisseurs.
"""
import logging
import yaml
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SupplierConfig(BaseModel):
    """Configuration d'un fournisseur."""

    name: str
    type: str  # csv_catalog, api, etc.
    path: Optional[str] = None  # Chemin vers le catalogue (CSV, etc.)
    sourcing_type: str  # import_CN, EU_wholesale, existing_stock, etc.
    brandable: bool = False
    bundle_capable: bool = False
    active: bool = True


class SupplierConfigService:
    """Service pour charger et gérer la configuration des fournisseurs."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupplierConfigService, cls).__new__(cls)
            cls._instance._config_path = None
            cls._instance._suppliers: Optional[List[SupplierConfig]] = None
        return cls._instance

    def _get_config_path(self) -> Path:
        """Retourne le chemin vers le fichier de configuration."""
        if self._config_path is None:
            # Chemin par défaut : depuis la racine de l'app
            base_path = Path(__file__).parent.parent.parent
            self._config_path = base_path / "app" / "config" / "suppliers.yml"
        return self._config_path

    def load_configs(self) -> List[SupplierConfig]:
        """
        Charge les configurations des fournisseurs depuis le fichier YAML.

        Returns:
            Liste des configurations de fournisseurs.
        """
        if self._suppliers is not None:
            return self._suppliers

        config_path = self._get_config_path()

        if not config_path.exists():
            logger.warning(
                f"Fichier de configuration fournisseurs non trouvé: {config_path}. "
                "Aucun fournisseur ne sera disponible."
            )
            return []

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            suppliers = []
            for supplier_data in data.get("suppliers", []):
                try:
                    supplier = SupplierConfig(**supplier_data)
                    suppliers.append(supplier)
                    logger.debug(f"Fournisseur chargé: {supplier.name}")
                except Exception as e:
                    logger.error(
                        f"Erreur lors du chargement du fournisseur {supplier_data.get('name', 'unknown')}: {str(e)}"
                    )
                    continue

            self._suppliers = suppliers
            logger.info(f"Chargement de {len(suppliers)} fournisseur(s) depuis {config_path}")
            return suppliers

        except yaml.YAMLError as e:
            logger.error(f"Erreur de parsing YAML dans {config_path}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration fournisseurs: {str(e)}", exc_info=True)
            return []

    def get_all_suppliers(self) -> List[SupplierConfig]:
        """
        Retourne tous les fournisseurs chargés.

        Returns:
            Liste de tous les fournisseurs.
        """
        return self.load_configs()

    def get_active_suppliers(self) -> List[SupplierConfig]:
        """
        Retourne uniquement les fournisseurs actifs.

        Returns:
            Liste des fournisseurs actifs.
        """
        return [supplier for supplier in self.load_configs() if supplier.active]

    def get_supplier_by_name(self, name: str) -> Optional[SupplierConfig]:
        """
        Retourne un fournisseur par son nom.

        Args:
            name: Nom du fournisseur.

        Returns:
            Configuration du fournisseur ou None si non trouvé.
        """
        for supplier in self.load_configs():
            if supplier.name == name:
                return supplier
        return None


# Instance singleton
def get_supplier_config_service() -> SupplierConfigService:
    """
    Retourne une instance singleton du service de configuration des fournisseurs.

    Returns:
        Instance de SupplierConfigService.
    """
    return SupplierConfigService()

