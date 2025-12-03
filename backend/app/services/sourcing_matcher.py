"""
Service de matching de sourcing - Module B.

Trouve des options de sourcing pour les produits candidats en parcourant
les catalogues des fournisseurs.
"""
import csv
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
from decimal import Decimal

from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.services.supplier_config import get_supplier_config_service, SupplierConfig

logger = logging.getLogger(__name__)


class SourcingMatcher:
    """
    Service pour matcher des produits candidats avec des options de sourcing.

    Utilise les catalogues des fournisseurs (CSV, etc.) pour trouver
    des options d'approvisionnement correspondantes.
    """

    def __init__(self):
        """Initialise le matcher avec le service de configuration des fournisseurs."""
        self.supplier_service = get_supplier_config_service()
        # Cache des catalogues CSV chargés
        self._csv_cache: Dict[str, List[Dict]] = {}

    def _normalize_keywords(self, text: Optional[str]) -> List[str]:
        """
        Normalise un texte en liste de mots-clés.

        Args:
            text: Texte à normaliser.

        Returns:
            Liste de mots-clés (lowercase, sans ponctuation).
        """
        if not text:
            return []

        # Nettoyer le texte (lowercase, suppression accents basique)
        text = text.lower()
        # Remplacer certains caractères spéciaux
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split sur espaces
        words = text.split()

        # Filtrer les mots vides et trop courts (moins de 3 caractères)
        keywords = [w for w in words if len(w) >= 3]

        # Filtrer les stopwords communs (liste minimale)
        stopwords = {'the', 'and', 'or', 'but', 'for', 'with', 'from', 'into', 'onto'}
        keywords = [w for w in keywords if w not in stopwords]

        return keywords

    def _load_csv_catalog(self, csv_path: str) -> List[Dict]:
        """
        Charge un catalogue CSV en mémoire (avec cache).

        Args:
            csv_path: Chemin vers le fichier CSV (relatif ou absolu).

        Returns:
            Liste de dictionnaires représentant les lignes du CSV.
        """
        # Vérifier le cache
        if csv_path in self._csv_cache:
            return self._csv_cache[csv_path]

        # Résoudre le chemin
        if Path(csv_path).is_absolute():
            full_path = Path(csv_path)
        else:
            # Chemin relatif depuis la racine du projet
            base_path = Path(__file__).parent.parent.parent.parent
            full_path = base_path / csv_path

        if not full_path.exists():
            logger.warning(f"Fichier CSV introuvable: {full_path}")
            return []

        try:
            catalog = []
            with open(full_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Nettoyer les valeurs (strip whitespace)
                    cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
                    catalog.append(cleaned_row)

            # Mettre en cache
            self._csv_cache[csv_path] = catalog
            logger.debug(f"Catalogue CSV chargé: {len(catalog)} produits depuis {full_path}")
            return catalog

        except Exception as e:
            logger.error(f"Erreur lors du chargement du CSV {full_path}: {str(e)}", exc_info=True)
            return []

    def _match_keywords(
        self, product_keywords: List[str], catalog_item_name: str, catalog_keywords: str
    ) -> bool:
        """
        Vérifie si les mots-clés du produit correspondent à un item du catalogue.

        Args:
            product_keywords: Mots-clés extraits du produit.
            catalog_item_name: Nom de l'item dans le catalogue.
            catalog_keywords: Mots-clés de l'item dans le catalogue.

        Returns:
            True si au moins 2 mots-clés significatifs matchent.
        """
        if not product_keywords:
            return False

        # Normaliser les mots-clés du catalogue
        catalog_text = f"{catalog_item_name} {catalog_keywords}".lower()
        catalog_keywords_list = self._normalize_keywords(catalog_text)

        # Compter les matches
        matches = 0
        for keyword in product_keywords:
            if keyword in catalog_keywords_list:
                matches += 1

        # Match si au moins 2 mots-clés significatifs
        # (ou 1 si le produit a très peu de mots-clés)
        min_matches = 2 if len(product_keywords) > 3 else 1
        return matches >= min_matches

    def _parse_csv_value(self, value: str, value_type: str) -> Optional:
        """
        Parse une valeur du CSV selon son type attendu.

        Args:
            value: Valeur brute du CSV.
            value_type: Type attendu ('int', 'float', 'bool', 'str').

        Returns:
            Valeur parsée ou None si erreur.
        """
        if not value or value.strip() == "":
            return None

        try:
            if value_type == "int":
                return int(float(value.strip()))
            elif value_type == "float":
                return float(value.strip())
            elif value_type == "bool":
                val = value.strip().lower()
                return val in ("1", "true", "yes", "oui", "o")
            else:
                return value.strip()
        except (ValueError, AttributeError):
            logger.debug(f"Impossible de parser '{value}' comme {value_type}")
            return None

    def _build_sourcing_option(
        self,
        candidate: ProductCandidate,
        supplier: SupplierConfig,
        csv_row: Dict,
    ) -> SourcingOption:
        """
        Construit une instance SourcingOption à partir d'une ligne CSV.

        Args:
            candidate: Produit candidat.
            supplier: Configuration du fournisseur.
            csv_row: Ligne du CSV du catalogue.

        Returns:
            Instance SourcingOption (non persistée).
        """
        # Parser les valeurs du CSV
        unit_cost = self._parse_csv_value(csv_row.get("unit_cost", ""), "float")
        moq = self._parse_csv_value(csv_row.get("moq", ""), "int")
        lead_time_days = self._parse_csv_value(csv_row.get("lead_time_days", ""), "int")
        brandable_csv = self._parse_csv_value(csv_row.get("brandable", ""), "bool")
        bundle_capable_csv = self._parse_csv_value(csv_row.get("bundle_capable", ""), "bool")

        # Priorité : valeur CSV > valeur fournisseur
        brandable = brandable_csv if brandable_csv is not None else supplier.brandable
        bundle_capable = (
            bundle_capable_csv if bundle_capable_csv is not None else supplier.bundle_capable
        )

        # Construire les notes
        notes = f"Matched by CSV supplier: {supplier.name}"
        if csv_row.get("name"):
            notes += f" - {csv_row['name']}"

        return SourcingOption(
            product_candidate_id=candidate.id,
            supplier_name=supplier.name,
            sourcing_type=supplier.sourcing_type,
            unit_cost=Decimal(str(unit_cost)) if unit_cost else None,
            shipping_cost_unit=Decimal("0"),  # Default pour V1
            moq=moq,
            lead_time_days=lead_time_days,
            brandable=bool(brandable),
            bundle_capable=bool(bundle_capable),
            notes=notes,
            raw_supplier_data=csv_row,
        )

    def find_sourcing_options_for_candidate(
        self, candidate: ProductCandidate
    ) -> List[SourcingOption]:
        """
        Trouve les options de sourcing pour un produit candidat.

        Parcourt les catalogues des fournisseurs actifs et matche
        les produits selon les mots-clés du titre et de la catégorie.

        Args:
            candidate: Produit candidat pour lequel chercher des options.

        Returns:
            Liste d'instances SourcingOption (non persistées en base).
        """
        options = []

        if not candidate.title:
            logger.debug(f"Produit {candidate.asin} sans titre, impossible de matcher")
            return options

        # Extraire les mots-clés du produit
        product_text = f"{candidate.title} {candidate.category or ''}"
        product_keywords = self._normalize_keywords(product_text)

        if not product_keywords:
            logger.debug(f"Aucun mot-clé significatif pour le produit {candidate.asin}")
            return options

        logger.debug(
            f"Recherche d'options de sourcing pour {candidate.asin} "
            f"(mots-clés: {product_keywords[:5]})"
        )

        # Parcourir les fournisseurs actifs
        suppliers = self.supplier_service.get_active_suppliers()

        for supplier in suppliers:
            if supplier.type != "csv_catalog":
                logger.debug(f"Type de fournisseur {supplier.type} non supporté pour {supplier.name}")
                continue

            if not supplier.path:
                logger.warning(f"Fournisseur {supplier.name} sans chemin de catalogue")
                continue

            try:
                # Charger le catalogue CSV
                catalog = self._load_csv_catalog(supplier.path)

                # Parcourir chaque ligne du catalogue
                for csv_row in catalog:
                    item_name = csv_row.get("name", "")
                    item_keywords = csv_row.get("keywords", "")

                    # Matcher les mots-clés
                    if self._match_keywords(product_keywords, item_name, item_keywords):
                        # Créer une option de sourcing
                        option = self._build_sourcing_option(candidate, supplier, csv_row)
                        options.append(option)
                        logger.debug(
                            f"Match trouvé: {candidate.asin} ↔ {supplier.name} "
                            f"({csv_row.get('sku', 'N/A')})"
                        )

            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement du fournisseur {supplier.name}: {str(e)}",
                    exc_info=True,
                )
                # Continue avec le fournisseur suivant

        # Si aucune option trouvée, créer une option par défaut
        if not options:
            logger.debug(
                f"Aucun match trouvé pour {candidate.asin}, création d'une option de sourcing par défaut"
            )
            default_option = self._create_default_sourcing_option(candidate)
            if default_option:
                options.append(default_option)

        logger.info(
            f"Trouvé {len(options)} option(s) de sourcing pour le produit {candidate.asin}"
        )
        return options

    def _create_default_sourcing_option(
        self, candidate: ProductCandidate
    ) -> Optional[SourcingOption]:
        """
        Crée une option de sourcing par défaut pour un produit sans match.

        Cette option utilise des valeurs estimées basées sur le produit lui-même.

        Args:
            candidate: Produit candidat.

        Returns:
            Instance SourcingOption par défaut ou None si le produit n'a pas assez de données.
        """
        # Calculer un prix d'achat estimé basé sur le prix de vente moyen
        # Estimation : coût ≈ 40-50% du prix de vente (marge grossière)
        estimated_unit_cost = None
        if candidate.avg_price:
            # Coût estimé : 40% du prix de vente
            estimated_unit_cost = Decimal(str(float(candidate.avg_price) * 0.4)).quantize(
                Decimal("0.01")
            )

        # Si on n'a pas de prix, utiliser une valeur par défaut basée sur la catégorie
        if not estimated_unit_cost:
            # Valeurs par défaut par catégorie
            default_costs = {
                "Electronics & Photo": Decimal("20.00"),
                "Home & Kitchen": Decimal("15.00"),
                "Sports & Outdoors": Decimal("18.00"),
                "Tools & Home Improvement": Decimal("25.00"),
                "Beauty & Personal Care": Decimal("10.00"),
                "Toys & Games": Decimal("12.00"),
            }
            category = candidate.category or "Home & Kitchen"
            estimated_unit_cost = default_costs.get(category, Decimal("15.00"))

        # Déterminer si le produit est brandable (basé sur la catégorie)
        brandable_categories = {
            "Electronics & Photo",
            "Beauty & Personal Care",
            "Sports & Outdoors",
        }
        is_brandable = candidate.category in brandable_categories

        # Créer l'option par défaut
        return SourcingOption(
            product_candidate_id=candidate.id,
            supplier_name="Default Generic Supplier",
            sourcing_type="EU_wholesale",
            unit_cost=estimated_unit_cost,
            shipping_cost_unit=Decimal("2.00"),  # Coût de transport par défaut
            moq=10,  # Quantité minimale de commande
            lead_time_days=14,  # Délai de livraison
            brandable=is_brandable,
            bundle_capable=False,
            notes=f"Option de sourcing par défaut générée automatiquement pour {candidate.asin}",
            raw_supplier_data={
                "source": "default",
                "estimated_from_price": str(candidate.avg_price) if candidate.avg_price else None,
                "category": candidate.category,
            },
        )

