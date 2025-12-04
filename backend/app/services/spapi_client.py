"""
Client pour l'API Amazon Selling Partner (SP-API).

Fournit des méthodes pour récupérer les prix et estimations de frais Amazon.
"""
import logging
import time
from typing import Optional, Dict, Any
from decimal import Decimal

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SPAPIClient:
    """Client pour l'API Amazon Selling Partner."""

    def __init__(self):
        """Initialise le client SP-API avec les credentials depuis la config."""
        self.settings = get_settings()
        self.base_url = "https://sellingpartnerapi-eu.amazon.com"
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

        # Vérifier si SP-API est configuré
        self.is_configured = bool(
            self.settings.SPAPI_LWA_CLIENT_ID
            and self.settings.SPAPI_LWA_CLIENT_SECRET
            and self.settings.SPAPI_LWA_REFRESH_TOKEN
        )

        if not self.is_configured:
            logger.warning(
                "SP-API non configuré : les variables d'environnement SPAPI_LWA_* ne sont pas définies. "
                "Les appels SP-API seront ignorés (fallback sur Keepa)."
            )

    def _get_access_token(self) -> Optional[str]:
        """
        Récupère un token d'accès LWA (Login With Amazon).

        Returns:
            Token d'accès ou None en cas d'erreur.
        """
        if not self.is_configured:
            return None

        # Vérifier si le token est encore valide (on le renouvelle 5 min avant expiration)
        if self.access_token and time.time() < (self.token_expires_at - 300):
            return self.access_token

        try:
            token_url = "https://api.amazon.com/auth/o2/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.settings.SPAPI_LWA_REFRESH_TOKEN,
                "client_id": self.settings.SPAPI_LWA_CLIENT_ID,
                "client_secret": self.settings.SPAPI_LWA_CLIENT_SECRET,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()

            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in

            logger.debug("Token d'accès SP-API obtenu avec succès")
            return self.access_token

        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du token SP-API: {str(e)}", exc_info=True)
            return None

    def get_pricing_for_asin(
        self, asin: str, marketplace_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère les prix pour un ASIN depuis SP-API.

        Args:
            asin: ASIN du produit.
            marketplace_id: ID du marketplace (défaut: SPAPI_MARKETPLACE_ID_FR).

        Returns:
            Dict avec les prix ou None en cas d'erreur/désactivation.
        """
        if not self.is_configured:
            logger.debug(f"SP-API non configuré, skip get_pricing_for_asin pour {asin}")
            return None

        marketplace_id = marketplace_id or self.settings.SPAPI_MARKETPLACE_ID_FR

        try:
            access_token = self._get_access_token()
            if not access_token:
                logger.warning(f"Impossible d'obtenir un token SP-API pour {asin}")
                return None

            # Endpoint SP-API Pricing - GetPricing
            url = f"{self.base_url}/pricing/v1/competitivePricing"
            params = {
                "MarketplaceId": marketplace_id,
                "Asins": asin,
                "ItemType": "Asin",
            }

            headers = {
                "x-amz-access-token": access_token,
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

            # Parser la réponse SP-API
            # Structure : {"payload": [{"ASIN": "...", "Product": {...}}]}
            payload = data.get("payload", [])
            if not payload or len(payload) == 0:
                logger.debug(f"Aucune donnée de pricing SP-API pour {asin}")
                return None

            product_data = payload[0].get("Product", {}).get("CompetitivePricing", {})
            competitive_prices = product_data.get("CompetitivePrices", {}).get("CompetitivePrice", [])

            # Extraire les prix
            buybox_price = None
            lowest_fba_price = None
            lowest_fbm_price = None
            is_amazon_seller = False

            for price_item in competitive_prices:
                price_data = price_item.get("Price", {})
                listing_price = price_data.get("ListingPrice", {}).get("Amount")
                if listing_price:
                    price_value = float(listing_price)
                    condition = price_item.get("condition", "")
                    fulfillment_channel = price_item.get("fulfillmentChannel", "")
                    belongs_to_requester = price_item.get("belongsToRequester", False)

                    # Buy Box (si Amazon vend)
                    if belongs_to_requester and condition == "New":
                        buybox_price = price_value
                        if fulfillment_channel == "Amazon":
                            is_amazon_seller = True

                    # Lowest FBA
                    if (
                        not lowest_fba_price
                        and fulfillment_channel == "Amazon"
                        and condition == "New"
                    ):
                        lowest_fba_price = price_value

                    # Lowest FBM
                    if (
                        not lowest_fbm_price
                        and fulfillment_channel == "Merchant"
                        and condition == "New"
                    ):
                        lowest_fbm_price = price_value

            result = {
                "asin": asin,
                "marketplace_id": marketplace_id,
                "buybox_price": buybox_price,
                "lowest_fba_price": lowest_fba_price,
                "lowest_fbm_price": lowest_fbm_price,
                "is_amazon_seller": is_amazon_seller,
            }

            logger.debug(f"Prix SP-API récupérés pour {asin}: {result}")
            return result

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Erreur HTTP {e.response.status_code} lors de la récupération du prix SP-API pour {asin}: {str(e)}"
            )
            return None
        except Exception as e:
            logger.warning(
                f"Erreur lors de la récupération du prix SP-API pour {asin}: {str(e)}", exc_info=True
            )
            return None

    def get_fees_estimate(
        self, asin: str, marketplace_id: Optional[str] = None, price: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère l'estimation des frais Amazon pour un ASIN et un prix donné.

        Args:
            asin: ASIN du produit.
            marketplace_id: ID du marketplace (défaut: SPAPI_MARKETPLACE_ID_FR).
            price: Prix de vente pour lequel estimer les frais.

        Returns:
            Dict avec les frais ou None en cas d'erreur/désactivation.
        """
        if not self.is_configured:
            logger.debug(f"SP-API non configuré, skip get_fees_estimate pour {asin}")
            return None

        marketplace_id = marketplace_id or self.settings.SPAPI_MARKETPLACE_ID_FR

        if price <= 0:
            logger.warning(f"Prix invalide pour get_fees_estimate: {price}")
            return None

        try:
            access_token = self._get_access_token()
            if not access_token:
                logger.warning(f"Impossible d'obtenir un token SP-API pour {asin}")
                return None

            # Endpoint SP-API Fees Estimate
            url = f"{self.base_url}/fees/v0/feesEstimate"
            params = {
                "MarketplaceId": marketplace_id,
                "ASIN": asin,
                "IdentifierType": "ASIN",
                "IsAmazonFulfilled": "true",  # FBA
                "PriceToEstimateFees": {
                    "ListingPrice": {
                        "Amount": str(price),
                        "CurrencyCode": "EUR",
                    }
                },
            }

            headers = {
                "x-amz-access-token": access_token,
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=params, headers=headers)
                response.raise_for_status()
                data = response.json()

            # Parser la réponse
            fees_estimate = data.get("FeesEstimateResult", {}).get("FeesEstimate", {})
            fee_detail_list = fees_estimate.get("FeeDetailList", [])

            total_fees = 0.0
            referral_fee = 0.0
            fulfillment_fee = 0.0

            for fee_detail in fee_detail_list:
                fee_type = fee_detail.get("FeeType", "")
                fee_amount = fee_detail.get("FinalFee", {}).get("Amount", "0")
                fee_value = float(fee_amount) if fee_amount else 0.0

                total_fees += fee_value

                if fee_type == "ReferralFee":
                    referral_fee = fee_value
                elif fee_type == "FBAFees":
                    fulfillment_fee = fee_value

            result = {
                "asin": asin,
                "price": price,
                "total_fees": round(total_fees, 2),
                "referral_fee": round(referral_fee, 2),
                "fulfillment_fee": round(fulfillment_fee, 2),
            }

            logger.debug(f"Frais SP-API estimés pour {asin} @ {price}€: {result}")
            return result

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Erreur HTTP {e.response.status_code} lors de l'estimation des frais SP-API pour {asin}: {str(e)}"
            )
            return None
        except Exception as e:
            logger.warning(
                f"Erreur lors de l'estimation des frais SP-API pour {asin}: {str(e)}", exc_info=True
            )
            return None



