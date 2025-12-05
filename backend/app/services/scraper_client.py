"""
Client scraper Amazon FR maison - Scraping direct sans dépendance externe.

Scrape les pages Amazon pour extraire des ASINs et des prix.
"""
import logging
import re
from typing import List, Optional
from decimal import Decimal
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

    def scrape_price_for_product(self, asin: str) -> Optional[Decimal]:
        """
        Scrape le prix d'un produit depuis sa page Amazon FR.

        Args:
            asin: ASIN du produit.

        Returns:
            Prix en Decimal (EUR) ou None si non trouvé/erreur.
        """
        url = f"https://www.amazon.fr/dp/{asin}"
        logger.info(f"Scraping du prix pour ASIN {asin}: {url}")

        try:
            html = self.fetch_html(url)

            # Essayer plusieurs sélecteurs pour le prix (par ordre de priorité)
            price_patterns = [
                # #priceblock_ourprice (format: <span id="priceblock_ourprice">29,99 €</span>)
                (r'<span[^>]*id=["\']priceblock_ourprice["\'][^>]*>([^<]+)', "priceblock_ourprice"),
                # #priceblock_dealprice (format: <span id="priceblock_dealprice">29,99 €</span>)
                (r'<span[^>]*id=["\']priceblock_dealprice["\'][^>]*>([^<]+)', "priceblock_dealprice"),
                # .a-offscreen (format: <span class="a-offscreen">29,99 €</span>)
                (r'<span[^>]*class=["\'][^"\']*a-offscreen[^"\']*["\'][^>]*>([^<]+)', "a-offscreen"),
                # Prix dans data-a-color="price" (format: <span data-a-color="price">29,99</span>)
                (r'data-a-color=["\']price["\'][^>]*>([^<]+)', "data-a-color=price"),
                # Prix dans span class "a-price-whole" (format: <span class="a-price-whole">29</span>)
                (r'<span[^>]*class=["\'][^"\']*a-price-whole[^"\']*["\'][^>]*>([^<]+)', "a-price-whole"),
                # Prix dans span class avec "a-price" (format: <span class="a-price">29,99</span>)
                (r'<span[^>]*class=["\'][^"\']*a-price[^"\']*["\'][^>]*>([^<]+)', "a-price"),
                # Prix dans format JSON-LD (structured data)
                (r'"price":\s*["\']?([\d,]+\.?\d*)[^"\']*["\']?', "json-ld"),
                # Prix générique dans format "XX,XX EUR" ou "XX.XX EUR"
                (r'(\d+[,\.]\d{2})\s*(?:€|EUR|euros?)', "generic-price"),
            ]

            for pattern, selector_name in price_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    price_str = match.strip()
                    # Nettoyer le prix : extraire les chiffres, points et virgules
                    # Format attendu : "29,99 €" ou "29.99" ou "29,99EUR"
                    price_clean = re.sub(r'[^\d,.]', '', price_str)
                    # Remplacer la virgule par un point pour conversion
                    price_clean = price_clean.replace(',', '.')
                    
                    # Vérifier qu'on a au moins un chiffre et un point/virgule
                    if not re.match(r'^\d+[.,]\d+$', price_clean):
                        # Essayer de trouver un format avec seulement des chiffres (prix entier)
                        price_clean_digits = re.sub(r'[^\d]', '', price_str)
                        if price_clean_digits and len(price_clean_digits) >= 2:
                            price_clean = price_clean_digits
                    
                    try:
                        price_value = float(price_clean)
                        # Filtrer les prix aberrants (< 1 EUR ou > 10000 EUR)
                        if 1.0 <= price_value <= 10000.0:
                            logger.info(f"Prix trouvé via {selector_name} pour {asin}: {price_value} EUR")
                            return Decimal(str(price_value))
                    except (ValueError, AttributeError):
                        continue

            logger.warning(f"Aucun prix trouvé pour {asin} sur {url}")
            return None

        except httpx.HTTPStatusError as e:
            logger.warning(f"Erreur HTTP {e.response.status_code} lors du scraping du prix pour {asin}: {str(e)}")
            return None
        except httpx.TimeoutException:
            logger.warning(f"Timeout lors du scraping du prix pour {asin}")
            return None
        except Exception as e:
            logger.warning(f"Erreur lors du scraping du prix pour {asin}: {str(e)}", exc_info=True)
            return None

