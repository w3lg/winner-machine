"""
Client scraper Amazon FR maison - Scraping direct sans dépendance externe.

Scrape les pages Amazon pour extraire des ASINs.
"""
import logging
import re
from typing import List, Optional
import httpx
from urllib.parse import quote

logger = logging.getLogger(__name__)


class ScraperClient:
    """Client pour scraper Amazon et extraire des ASINs."""

    def __init__(self, timeout: float = 10.0):
        """
        Initialise le client scraper.

        Args:
            timeout: Timeout pour les requêtes HTTP en secondes.
        """
        self.timeout = timeout
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def fetch_html(self, url: str) -> str:
        """
        Récupère le HTML d'une URL.

        Args:
            url: URL à scraper.

        Returns:
            Contenu HTML en string.

        Raises:
            Exception si la requête échoue.
        """
        logger.info(f"Scraping de l'URL: {url}")
        try:
            with httpx.Client(timeout=self.timeout, headers=self.default_headers, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                
                logger.info(f"Réponse HTTP {response.status_code} pour {url}, taille: {len(response.text)} caractères")
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP {e.response.status_code} lors du scraping de {url}: {e.response.text[:200]}")
            raise
        except httpx.TimeoutException:
            logger.error(f"Timeout lors du scraping de {url}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du scraping de {url}: {str(e)}", exc_info=True)
            raise

    def extract_asins_from_html(self, html: str) -> List[str]:
        """
        Extrait les ASINs depuis le HTML d'une page Amazon.

        Utilise plusieurs patterns regex pour trouver les ASINs :
        - /dp/B0XXXXXXXX
        - data-asin="B0XXXXXXXX"
        - ASINs en format B0XXXXXXXX dans le texte

        Args:
            html: Contenu HTML de la page Amazon.

        Returns:
            Liste d'ASINs uniques (format B0XXXXXXXX, 10 caractères).
        """
        asins_set = set()

        # Pattern 1: /dp/B0XXXXXXXX ou /gp/product/B0XXXXXXXX
        pattern_dp = re.compile(r'/dp/(B0[A-Z0-9]{8})', re.IGNORECASE)
        matches = pattern_dp.findall(html)
        for match in matches:
            asin = match.upper()
            if len(asin) == 10 and asin.startswith('B0'):
                asins_set.add(asin)

        # Pattern 2: data-asin="B0XXXXXXXX"
        pattern_data_asin = re.compile(r'data-asin=["\'](B0[A-Z0-9]{8})["\']', re.IGNORECASE)
        matches = pattern_data_asin.findall(html)
        for match in matches:
            asin = match.upper()
            if len(asin) == 10 and asin.startswith('B0'):
                asins_set.add(asin)

        # Pattern 3: ASINs dans les attributs data-* ou autres attributs
        pattern_asin_generic = re.compile(r'(?:asin|productId|product-id)["\']?\s*[:=]\s*["\']?(B0[A-Z0-9]{8})["\']?', re.IGNORECASE)
        matches = pattern_asin_generic.findall(html)
        for match in matches:
            asin = match.upper()
            if len(asin) == 10 and asin.startswith('B0'):
                asins_set.add(asin)

        # Pattern 4: ASINs isolés (plus risqué, mais peut trouver des ASINs dans le texte)
        # On cherche des séquences B0 suivies de 8 caractères alphanumériques
        pattern_isolated = re.compile(r'\b(B0[A-Z0-9]{8})\b', re.IGNORECASE)
        matches = pattern_isolated.findall(html)
        for match in matches:
            asin = match.upper()
            # Validation : doit commencer par B0 et avoir 10 caractères
            if len(asin) == 10 and asin.startswith('B0'):
                # Vérifier que ce n'est pas dans une URL ou autre contexte indésirable
                asins_set.add(asin)

        # Convertir en liste triée pour la déduplication
        asins_list = sorted(list(asins_set))

        logger.info(f"Extraction de {len(asins_list)} ASINs uniques depuis le HTML")
        
        if asins_list:
            logger.debug(f"Premiers ASINs extraits: {asins_list[:10]}")

        return asins_list

    def scrape_best_sellers_fr(self, limit: int = 100) -> List[str]:
        """
        Scrape la page Amazon Best Sellers FR et extrait les ASINs.

        Args:
            limit: Nombre maximum d'ASINs à retourner.

        Returns:
            Liste d'ASINs (limité à `limit`).
        """
        url = "https://www.amazon.fr/gp/bestsellers"
        logger.info(f"Scraping des Best Sellers Amazon FR: {url} (limit: {limit})")

        try:
            html = self.fetch_html(url)
            asins = self.extract_asins_from_html(html)

            # Limiter le nombre d'ASINs
            limited_asins = asins[:limit]
            logger.info(f"Scraping réussi: {len(limited_asins)} ASINs extraits (sur {len(asins)} trouvés)")

            return limited_asins

        except Exception as e:
            logger.error(f"Erreur lors du scraping des Best Sellers: {str(e)}", exc_info=True)
            return []

    def scrape_search(self, keyword: str, limit: int = 100) -> List[str]:
        """
        Scrape une page de recherche Amazon FR et extrait les ASINs.

        Args:
            keyword: Mot-clé de recherche.
            limit: Nombre maximum d'ASINs à retourner.

        Returns:
            Liste d'ASINs (limité à `limit`).
        """
        # Encoder le mot-clé pour l'URL
        encoded_keyword = quote(keyword)
        url = f"https://www.amazon.fr/s?k={encoded_keyword}"
        logger.info(f"Scraping de la recherche Amazon FR: {url} (keyword: {keyword}, limit: {limit})")

        try:
            html = self.fetch_html(url)
            asins = self.extract_asins_from_html(html)

            # Limiter le nombre d'ASINs
            limited_asins = asins[:limit]
            logger.info(f"Scraping réussi: {len(limited_asins)} ASINs extraits (sur {len(asins)} trouvés)")

            return limited_asins

        except Exception as e:
            logger.error(f"Erreur lors du scraping de la recherche: {str(e)}", exc_info=True)
            return []

