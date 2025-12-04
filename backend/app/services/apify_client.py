"""
Client Apify pour récupérer des ASINs depuis Amazon.
"""
import logging
from typing import List, Optional, Dict, Any
import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ApifyClient:
    """Client pour interagir avec l'API Apify."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le client Apify.

        Args:
            api_key: Clé API Apify. Si None, lit depuis les settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.APIFY_API_KEY
        self.base_url = "https://api.apify.com/v2"
        self.timeout = 300.0  # 5 minutes timeout pour les runs Apify

        if not self.api_key:
            logger.warning(
                "APIFY_API_KEY non définie, le client Apify ne pourra pas fonctionner"
            )

    def _make_request(
        self, method: str, url: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Effectue une requête HTTP vers l'API Apify.

        Args:
            method: Méthode HTTP (GET, POST, etc.)
            url: URL complète
            params: Paramètres de requête
            json_data: Données JSON pour POST/PUT

        Returns:
            Réponse JSON ou None en cas d'erreur
        """
        if not self.api_key:
            logger.warning("APIFY_API_KEY non définie, impossible de faire la requête")
            return None

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Erreur HTTP {e.response.status_code} lors de l'appel Apify: {e.response.text}"
            )
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout lors de l'appel Apify vers {url}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'appel Apify: {str(e)}", exc_info=True)
            return None

    def run_actor_sync(
        self, actor_id: str, input_data: Dict[str, Any], wait_for_finish: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Lance un actor Apify et attend la fin (mode synchrone).

        Args:
            actor_id: ID de l'actor Apify (ex: "junglee/amazon-bestsellers")
            input_data: Données d'entrée pour l'actor
            wait_for_finish: Si True, attend la fin du run

        Returns:
            Liste d'items du dataset ou None en cas d'erreur
        """
        if not self.api_key:
            logger.warning("APIFY_API_KEY non définie, impossible de lancer l'actor")
            return None

        # Lancer le run avec waitForFinish pour mode synchrone
        run_url = f"{self.base_url}/acts/{actor_id}/runs"
        
        # Préparer les données: input dans un objet séparé, waitForFinish en paramètre
        run_request = {
            "waitForFinish": 300 if wait_for_finish else 0,  # 5 minutes max d'attente
        }
        
        # Les données d'input doivent être dans le body avec input
        json_body = {
            **run_request,
            "input": input_data,
        }

        logger.info(f"Lancement de l'actor Apify: {actor_id} avec input: {input_data}")
        run_response = self._make_request("POST", run_url, json_data=json_body)

        if not run_response:
            return None

        run_data = run_response.get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")

        if not run_id:
            logger.error(f"Impossible de récupérer le run_id depuis la réponse: {run_response}")
            return None

        logger.info(f"Run Apify créé: {run_id}, dataset: {dataset_id}")

        if not wait_for_finish or not dataset_id:
            return None

        # Récupérer les items du dataset
        dataset_url = f"{self.base_url}/datasets/{dataset_id}/items"
        result = self._make_request("GET", dataset_url)

        if result and isinstance(result, dict):
            # L'API Apify retourne {"items": [...]}
            return result.get("items", [])
        elif result and isinstance(result, list):
            # Parfois l'API retourne directement une liste
            return result
        
        return []

    def get_bestsellers_asins(
        self, domain: str = "FR", limit: int = 500, category: Optional[str] = None
    ) -> List[str]:
        """
        Récupère les ASINs des best sellers Amazon via Apify.

        Args:
            domain: Domaine Amazon (FR, DE, ES, etc.)
            limit: Nombre maximum d'ASINs à récupérer
            category: Catégorie spécifique (optionnel)

        Returns:
            Liste d'ASINs uniques

        Note:
            Utilise l'actor "junglee/amazon-bestsellers" par défaut.
            Si Apify renvoie une erreur, retourne une liste vide sans planter.
        """
        if not self.api_key:
            logger.warning(
                f"APIFY_API_KEY non définie, impossible de récupérer les best sellers pour {domain}"
            )
            return []

        # Actor Apify pour les best sellers Amazon
        # Documentation: https://apify.com/junglee/amazon-bestsellers
        actor_id = "junglee/amazon-bestsellers"

        # Préparer les données d'entrée
        input_data = {
            "country": domain,
            "maxItems": limit,
        }

        if category:
            input_data["category"] = category

        try:
            logger.info(
                f"Récupération de {limit} best sellers Amazon {domain} via Apify..."
            )

            # Lancer l'actor et récupérer les résultats
            result = self.run_actor_sync(actor_id, input_data, wait_for_finish=True)

            if not result:
                logger.warning("Aucun résultat retourné par Apify")
                return []

            # Extraire les ASINs depuis les items
            asins = []
            items = result if isinstance(result, list) else []

            for item in items:
                # Chercher l'ASIN dans différents champs possibles
                asin = (
                    item.get("asin") 
                    or item.get("ASIN") 
                    or item.get("productAsin")
                    or item.get("asinCode")
                )
                if asin:
                    # Normaliser l'ASIN (enlever les espaces, mettre en majuscule)
                    asin = str(asin).strip().upper()
                    if len(asin) == 10:
                        asins.append(asin)

            # Dédupliquer et limiter
            unique_asins = list(dict.fromkeys(asins))[:limit]

            logger.info(
                f"Récupération réussie: {len(unique_asins)} ASINs uniques récupérés"
            )

            return unique_asins

        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération des best sellers via Apify: {str(e)}",
                exc_info=True,
            )
            return []

    def get_search_asins(
        self, keyword: str, domain: str = "FR", limit: int = 100
    ) -> List[str]:
        """
        Récupère les ASINs depuis une recherche Amazon via Apify.

        Args:
            keyword: Mot-clé de recherche
            domain: Domaine Amazon (FR, DE, ES, etc.)
            limit: Nombre maximum d'ASINs à récupérer

        Returns:
            Liste d'ASINs uniques

        Note:
            Pour l'instant, cette fonction retourne une liste vide.
            À implémenter quand un actor de recherche sera choisi.
        """
        logger.warning("get_search_asins() n'est pas encore implémenté")
        return []

