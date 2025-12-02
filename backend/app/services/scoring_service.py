"""
Service de scoring pour les produits et options de sourcing.

Calcule les scores de rentabilité (marges, frais, risque) et détermine
la décision finale (A_launch, B_review, C_drop).
"""
import logging
import yaml
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore

logger = logging.getLogger(__name__)


class ScoringService:
    """Service pour calculer les scores de rentabilité des produits."""

    def __init__(self, fees_config_path: Optional[Path] = None, scoring_rules_path: Optional[Path] = None):
        """
        Initialise le service avec les chemins vers les fichiers de config.

        Args:
            fees_config_path: Chemin vers fees.yml. Si None, utilise le chemin par défaut.
            scoring_rules_path: Chemin vers scoring_rules.yml. Si None, utilise le chemin par défaut.
        """
        base_path = Path(__file__).parent.parent.parent

        if fees_config_path is None:
            fees_config_path = base_path / "app" / "config" / "fees.yml"
        self.fees_config_path = fees_config_path

        if scoring_rules_path is None:
            scoring_rules_path = base_path / "app" / "config" / "scoring_rules.yml"
        self.scoring_rules_path = scoring_rules_path

        self._fees_config: Optional[dict] = None
        self._scoring_rules: Optional[dict] = None

    def _load_fees_config(self) -> dict:
        """Charge la configuration des frais depuis fees.yml."""
        if self._fees_config is not None:
            return self._fees_config

        try:
            with open(self.fees_config_path, "r", encoding="utf-8") as f:
                self._fees_config = yaml.safe_load(f) or {}
            return self._fees_config
        except Exception as e:
            logger.error(f"Erreur lors du chargement de fees.yml: {e}", exc_info=True)
            # Valeurs par défaut
            self._fees_config = {
                "commission_rates": {"default": 0.15},
                "fba_fees": {"standard": 4.50},
                "logistics": {"default_shipping_per_unit": 2.00},
            }
            return self._fees_config

    def _load_scoring_rules(self) -> dict:
        """Charge les règles de scoring depuis scoring_rules.yml."""
        if self._scoring_rules is not None:
            return self._scoring_rules

        try:
            with open(self.scoring_rules_path, "r", encoding="utf-8") as f:
                self._scoring_rules = yaml.safe_load(f) or {}
            return self._scoring_rules
        except Exception as e:
            logger.error(f"Erreur lors du chargement de scoring_rules.yml: {e}", exc_info=True)
            # Valeurs par défaut
            self._scoring_rules = {
                "min_margin_percent": 20,
                "min_global_score_A": 100,
                "min_global_score_B": 20,
                "risk_factors": {"default": 0.1},
            }
            return self._scoring_rules

    def score_product_option(
        self,
        candidate: ProductCandidate,
        option: SourcingOption,
    ) -> ProductScore:
        """
        Calcule le score de rentabilité pour une combinaison produit + option de sourcing.

        Args:
            candidate: Produit candidat.
            option: Option de sourcing.

        Returns:
            ProductScore avec tous les calculs effectués.
        """
        fees_config = self._load_fees_config()
        scoring_rules = self._load_scoring_rules()

        # 1. Déterminer le prix de vente cible
        selling_price_target = candidate.avg_price
        if selling_price_target is None:
            # Fallback: 2x le coût unitaire si disponible
            if option.unit_cost:
                selling_price_target = option.unit_cost * Decimal("2.0")
            else:
                # Pas de prix cible possible
                selling_price_target = Decimal("0")
                logger.warning(
                    f"Pas de prix moyen pour {candidate.asin} et pas de unit_cost pour {option.supplier_name}. "
                    "Prix cible = 0"
                )

        # 2. Taux de commission Amazon (par catégorie ou défaut)
        commission_rate = Decimal(str(fees_config.get("commission_rates", {}).get("default", 0.15)))

        # 3. Frais Amazon (commission + FBA)
        commission_fee = selling_price_target * commission_rate if selling_price_target > 0 else Decimal("0")
        fba_fee = Decimal(str(fees_config.get("fba_fees", {}).get("standard", 4.50)))
        amazon_fees_estimate = commission_fee + fba_fee

        # 4. Coûts logistiques
        if option.shipping_cost_unit:
            logistics_cost_estimate = option.shipping_cost_unit
        else:
            logistics_cost_estimate = Decimal(
                str(fees_config.get("logistics", {}).get("default_shipping_per_unit", 2.00))
            )

        # 5. Coût unitaire du produit
        unit_cost = option.unit_cost or Decimal("0")

        # 6. Marge absolue
        margin_absolute = (
            selling_price_target
            - amazon_fees_estimate
            - logistics_cost_estimate
            - unit_cost
        )

        # 7. Marge en pourcentage
        margin_percent = None
        if selling_price_target > 0:
            margin_percent = (margin_absolute / selling_price_target) * Decimal("100")

        # 8. Estimations de ventes par jour
        estimated_sales_per_day = candidate.estimated_sales_per_day or Decimal("1")

        # 9. Facteur de risque (pour l'instant, défaut)
        risk_factor = Decimal(str(scoring_rules.get("risk_factors", {}).get("default", 0.1)))

        # 10. Score global
        global_score = None
        if margin_percent is not None:
            # Score = marge% * ventes/jour * (1 - risque)
            global_score = margin_percent * estimated_sales_per_day * (Decimal("1") - risk_factor)

        # 11. Décision finale
        min_margin = Decimal(str(scoring_rules.get("min_margin_percent", 20)))
        min_score_A = Decimal(str(scoring_rules.get("min_global_score_A", 100)))
        min_score_B = Decimal(str(scoring_rules.get("min_global_score_B", 20)))

        if margin_percent is None or margin_percent < min_margin:
            decision = "C_drop"
        elif global_score is not None and global_score >= min_score_A:
            decision = "A_launch"
        elif global_score is not None and global_score >= min_score_B:
            decision = "B_review"
        else:
            decision = "C_drop"

        # Créer et retourner le ProductScore (non persisté)
        product_score = ProductScore(
            product_candidate_id=candidate.id,
            sourcing_option_id=option.id,
            selling_price_target=selling_price_target,
            amazon_fees_estimate=amazon_fees_estimate,
            logistics_cost_estimate=logistics_cost_estimate,
            margin_absolute=margin_absolute,
            margin_percent=margin_percent,
            estimated_sales_per_day=estimated_sales_per_day,
            risk_factor=risk_factor,
            global_score=global_score,
            decision=decision,
        )

        logger.debug(
            f"Score calculé pour {candidate.asin} + {option.supplier_name}: "
            f"decision={decision}, score={global_score}, marge%={margin_percent}"
        )

        return product_score


# Instance singleton
_scoring_service: Optional[ScoringService] = None


def get_scoring_service() -> ScoringService:
    """
    Retourne une instance singleton du service de scoring.

    Returns:
        Instance de ScoringService.
    """
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service

