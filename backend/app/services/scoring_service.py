"""
Service de scoring pour les produits et options de sourcing.

Calcule les scores de rentabilité (marges, frais, risque) et détermine
la décision finale (A_launch, B_review, C_drop).

Intègre SP-API pour récupérer les prix et frais réels, et utilise
un modèle de profit pour calculer les marges brutes et nettes.
"""
import logging
import yaml
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore
from app.services.spapi_client import SPAPIClient
from app.services.profit_model_service import get_profit_model_service
from app.core.config import get_settings

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
        self.spapi_client = SPAPIClient()
        self.profit_model_service = get_profit_model_service()
        self.settings = get_settings()

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
        
        # Récupérer la config du profit model pour le marketplace
        marketplace_code = candidate.source_marketplace.replace("amazon_", "")  # "amazon_fr" -> "fr"
        profit_config = self.profit_model_service.get_marketplace_config(marketplace_code)

        # ============================================================
        # 1. PRIX DE VENTE CIBLE (avec SP-API si disponible)
        # ============================================================
        selling_price_target = None
        
        # Essayer SP-API d'abord
        spapi_pricing = self.spapi_client.get_pricing_for_asin(
            candidate.asin,
            marketplace_id=self.settings.SPAPI_MARKETPLACE_ID_FR
        )
        
        if spapi_pricing:
            # Priorité : buybox_price > lowest_fba_price > lowest_fbm_price
            selling_price_target = (
                spapi_pricing.get("buybox_price") or
                spapi_pricing.get("lowest_fba_price") or
                spapi_pricing.get("lowest_fbm_price")
            )
            if selling_price_target:
                selling_price_target = Decimal(str(selling_price_target))
                logger.debug(f"Prix depuis SP-API pour {candidate.asin}: {selling_price_target} EUR")
        
        # Fallback sur Keepa avg_price
        if selling_price_target is None:
            selling_price_target = candidate.avg_price
        
        # Fallback final : 2x le coût unitaire
        if selling_price_target is None:
            if option.unit_cost:
                selling_price_target = option.unit_cost * Decimal("2.0")
            else:
                selling_price_target = Decimal("0")
                logger.warning(
                    f"Pas de prix pour {candidate.asin}, prix cible = 0"
                )

        # ============================================================
        # 2. FRAIS AMAZON (avec SP-API si disponible)
        # ============================================================
        amazon_fees_estimate = None
        
        # Essayer SP-API Fees Estimate
        if selling_price_target and selling_price_target > 0:
            spapi_fees = self.spapi_client.get_fees_estimate(
                candidate.asin,
                marketplace_id=self.settings.SPAPI_MARKETPLACE_ID_FR,
                price=float(selling_price_target)
            )
            
            if spapi_fees and spapi_fees.get("total_fees"):
                amazon_fees_estimate = Decimal(str(spapi_fees["total_fees"]))
                logger.debug(f"Frais Amazon depuis SP-API pour {candidate.asin}: {amazon_fees_estimate} EUR")
        
        # Fallback sur le modèle approximatif
        if amazon_fees_estimate is None:
            commission_rate = Decimal(str(fees_config.get("commission_rates", {}).get("default", 0.15)))
            commission_fee = selling_price_target * commission_rate if selling_price_target > 0 else Decimal("0")
            fba_fee = Decimal(str(fees_config.get("fba_fees", {}).get("standard", 4.50)))
            amazon_fees_estimate = commission_fee + fba_fee

        # ============================================================
        # 3. COÛTS LOGISTIQUES (depuis profit model ou fees config)
        # ============================================================
        if option.shipping_cost_unit:
            logistics_cost_estimate = option.shipping_cost_unit
        elif profit_config.get("enabled"):
            # Utiliser le profit model si activé
            logistics_cost_estimate = Decimal(str(profit_config.get("default_shipping_cost_per_unit", 5.0)))
        else:
            logistics_cost_estimate = Decimal(
                str(fees_config.get("logistics", {}).get("default_shipping_per_unit", 2.00))
            )

        # ============================================================
        # 4. COÛT UNITAIRE DU PRODUIT
        # ============================================================
        purchase_cost = option.unit_cost or Decimal("0")

        # ============================================================
        # 5. MARGES BRUTES (Profit Model FR)
        # ============================================================
        gross_profit = None
        gross_margin_percent = None
        
        if selling_price_target and selling_price_target > 0:
            # Marge brute = prix vente - frais Amazon - shipping - coût achat
            gross_profit = (
                selling_price_target
                - amazon_fees_estimate
                - logistics_cost_estimate
                - purchase_cost
            )
            
            # Marge brute en pourcentage
            gross_margin_percent = (gross_profit / selling_price_target) * Decimal("100")
        
        # ============================================================
        # 6. PROFIT NET ESTIMÉ (après IS/CFE)
        # ============================================================
        net_profit_estimated = None
        if gross_profit is not None and profit_config.get("enabled"):
            tax_factor = Decimal(str(profit_config.get("tax_factor_after_is_cfe", 0.7)))
            net_profit_estimated = gross_profit * tax_factor
        
        # ============================================================
        # 7. MARGES ABSOLUES ET POURCENTAGE (pour compatibilité avec l'existant)
        # ============================================================
        # Utiliser gross_profit/gross_margin_percent comme base, sinon recalculer
        if gross_profit is not None:
            margin_absolute = gross_profit
        else:
            # Fallback : calculer depuis selling_price_target
            margin_absolute = (
                selling_price_target
                - amazon_fees_estimate
                - logistics_cost_estimate
                - purchase_cost
            ) if selling_price_target else None
        
        if gross_margin_percent is not None:
            margin_percent = gross_margin_percent
        else:
            # Fallback : calculer depuis margin_absolute
            margin_percent = (
                (margin_absolute / selling_price_target) * Decimal("100")
                if margin_absolute is not None and selling_price_target and selling_price_target > 0
                else None
            )

        # ============================================================
        # 8. ESTIMATIONS DE VENTES PAR JOUR
        # ============================================================
        estimated_sales_per_day = candidate.estimated_sales_per_day or Decimal("1")

        # ============================================================
        # 9. FACTEUR DE RISQUE
        # ============================================================
        risk_factor = Decimal(str(scoring_rules.get("risk_factors", {}).get("default", 0.1)))

        # ============================================================
        # 10. SCORE GLOBAL (avec prise en compte du profit net si disponible)
        # ============================================================
        global_score = None
        if margin_percent is not None:
            # Score de base = marge% * ventes/jour * (1 - risque)
            base_score = margin_percent * estimated_sales_per_day * (Decimal("1") - risk_factor)
            
            # Si profit net disponible, augmenter le poids des produits rentables
            if net_profit_estimated is not None and net_profit_estimated > 0:
                # Bonus : +10% par EUR de profit net par jour (jusqu'à +50%)
                profit_per_day = net_profit_estimated * estimated_sales_per_day
                bonus_factor = min(Decimal("1.5"), Decimal("1.0") + (profit_per_day / Decimal("10")))
                global_score = base_score * bonus_factor
            else:
                global_score = base_score

        # ============================================================
        # 11. DÉCISION FINALE
        # ============================================================
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

        # ============================================================
        # 9. CRÉER ET RETOURNER LE ProductScore (non persisté)
        # ============================================================
        product_score = ProductScore(
            product_candidate_id=candidate.id,
            sourcing_option_id=option.id,
            selling_price_target=selling_price_target,
            amazon_fees_estimate=amazon_fees_estimate,
            logistics_cost_estimate=logistics_cost_estimate,
            margin_absolute=margin_absolute,
            margin_percent=margin_percent,
            gross_profit=gross_profit,
            gross_margin_percent=gross_margin_percent,
            net_profit_estimated=net_profit_estimated,
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

