"""
Client pour l'API Keepa - Récupération de données produits Amazon.
"""
import logging
from typing import List, Optional
from decimal import Decimal
import httpx
from datetime import datetime

from app.core.config import get_settings
from app.services.category_config import CategoryConfig

logger = logging.getLogger(__name__)


class KeepaProduct:
    """Produit normalisé depuis Keepa."""

    def __init__(
        self,
        asin: str,
        title: str,
        category: str,
        avg_price: Optional[Decimal],
        bsr: Optional[int],
        estimated_sales_per_day: Optional[Decimal],
        reviews_count: Optional[int],
        rating: Optional[Decimal],
        raw_data: dict,
    ):
        self.asin = asin
        self.title = title
        self.category = category
        self.avg_price = avg_price
        self.bsr = bsr
        self.estimated_sales_per_day = estimated_sales_per_day
        self.reviews_count = reviews_count
        self.rating = rating
        self.raw_data = raw_data


class KeepaClient:
    """Client pour interagir avec l'API Keepa."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le client Keepa.

        Args:
            api_key: Clé API Keepa. Si None, lit depuis les settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.KEEPA_API_KEY
        self.base_url = "https://api.keepa.com"
        self.timeout = 30.0  # Timeout en secondes pour les requêtes HTTP

    def get_top_products_by_category(
        self, category_config: CategoryConfig, limit: int = 200
    ) -> List[KeepaProduct]:
        """
        Récupère les meilleurs produits d'une catégorie depuis l'API Keepa.

        Args:
            category_config: Configuration de la catégorie.
            limit: Nombre maximum de produits à récupérer (20-200).

        Returns:
            Liste des produits normalisés.

        Note:
            Si KEEPA_API_KEY n'est pas définie, retourne des données mockées.
        """
        if not self.api_key:
            logger.warning(
                "KEEPA_API_KEY non définie, utilisation des données mockées pour la catégorie %s",
                category_config.name,
            )
            return self._mock_products(category_config, limit)

        try:
            logger.info(
                "Appel API Keepa pour la catégorie %s (ID: %s, limit: %s)",
                category_config.name,
                category_config.id,
                limit,
            )

            # Appel à l'API Keepa
            # Endpoint: https://api.keepa.com/product
            # domain=1 = Amazon FR
            # stats=180 = statistiques sur 180 jours (6 mois)
            params = {
                "key": self.api_key,
                "domain": 1,  # 1 = Amazon FR
                "category": str(category_config.id),
                "stats": 180,  # 6 mois de statistiques
                "rating": 3.0,  # Note minimum
                "last": limit,  # Nombre de produits à récupérer
            }

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/product",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            # Vérifier si la réponse est valide
            if "products" not in data:
                logger.warning(
                    "Réponse Keepa invalide pour la catégorie %s: pas de champ 'products'",
                    category_config.name,
                )
                return []

            products = data.get("products", [])
            if not products:
                logger.info(
                    "Aucun produit retourné par Keepa pour la catégorie %s",
                    category_config.name,
                )
                return []

            logger.info(
                "Keepa a retourné %s produits pour la catégorie %s",
                len(products),
                category_config.name,
            )

            # Normaliser les produits
            normalized = self._normalize_products(products, category_config)
            return normalized

        except httpx.HTTPStatusError as e:
            logger.error(
                "Erreur HTTP Keepa pour la catégorie %s: %s %s",
                category_config.name,
                e.response.status_code,
                e.response.text[:200],
            )
            return []
        except httpx.RequestError as e:
            logger.error(
                "Erreur de requête Keepa pour la catégorie %s: %s",
                category_config.name,
                str(e),
            )
            return []
        except Exception as e:
            logger.error(
                "Erreur inattendue lors de l'appel Keepa pour la catégorie %s: %s",
                category_config.name,
                str(e),
                exc_info=True,
            )
            return []

    def _mock_products(
        self, category_config: CategoryConfig, limit: int
    ) -> List[KeepaProduct]:
        """
        Génère des produits mockés pour le développement.

        Args:
            category_config: Configuration de la catégorie.
            limit: Nombre de produits à générer.

        Returns:
            Liste de produits mockés.
        """
        import random
        from decimal import Decimal

        mock_products = []
        base_asins = [
            "B08XYZ1234",
            "B09ABC5678",
            "B10DEF9012",
            "B11GHI3456",
            "B12JKL7890",
        ]

        for i in range(min(limit, 5)):  # Générer 5 produits mock max
            # ASINs Amazon sont toujours de 10 caractères exactement
            asin = base_asins[i % len(base_asins)]
            price = Decimal(
                str(
                    random.uniform(
                        category_config.price_min, category_config.price_max
                    )
                )
            ).quantize(Decimal("0.01"))
            bsr = random.randint(1000, category_config.bsr_max)
            sales = Decimal(str(random.uniform(5, 50))).quantize(Decimal("0.01"))
            reviews = random.randint(50, 5000)
            rating = Decimal(str(random.uniform(3.5, 4.8))).quantize(Decimal("0.01"))

            raw_data = {
                "asin": asin,
                "title": f"Produit exemple {i+1} - {category_config.name}",
                "category": category_config.name,
                "price": float(price),
                "bsr": bsr,
                "sales": float(sales),
                "reviews": reviews,
                "rating": float(rating),
            }

            mock_products.append(
                KeepaProduct(
                    asin=asin,
                    title=raw_data["title"],
                    category=category_config.name,
                    avg_price=price,
                    bsr=bsr,
                    estimated_sales_per_day=sales,
                    reviews_count=reviews,
                    rating=rating,
                    raw_data=raw_data,
                )
            )

        return mock_products

    def _normalize_products(
        self, products: List[dict], category_config: CategoryConfig
    ) -> List[KeepaProduct]:
        """
        Normalise les données brutes de l'API Keepa.

        Args:
            products: Liste de produits bruts depuis l'API Keepa.
            category_config: Configuration de la catégorie.

        Returns:
            Liste de produits normalisés.
        """
        normalized = []

        for product in products:
            try:
                asin = product.get("asin", "").strip()
                if not asin or len(asin) != 10:
                    logger.warning("ASIN invalide ou manquant, produit ignoré: %s", product)
                    continue

                title = product.get("title", "Sans titre").strip()

                # Prix moyen (90 derniers jours) - Keepa utilise parfois "stats" ou "csv"
                avg_price = None
                if "price" in product:
                    price_obj = product["price"]
                    # Prendre le prix Amazon ou le prix moyen
                    if isinstance(price_obj, dict):
                        avg_price = price_obj.get("amazon") or price_obj.get("current")
                    elif isinstance(price_obj, (int, float)):
                        avg_price = price_obj
                
                # Convertir en Decimal si nécessaire
                if avg_price is not None:
                    try:
                        avg_price = Decimal(str(avg_price))
                        # Vérifier si le prix est dans la plage configurée
                        if (
                            category_config.price_min
                            and avg_price < category_config.price_min
                        ) or (
                            category_config.price_max
                            and avg_price > category_config.price_max
                        ):
                            logger.debug(
                                "Prix %s hors plage [%s-%s] pour %s, ignoré",
                                avg_price,
                                category_config.price_min,
                                category_config.price_max,
                                asin,
                            )
                            continue
                    except (ValueError, TypeError):
                        avg_price = None

                # BSR (Best Seller Rank)
                bsr = None
                if "salesRank" in product:
                    sales_rank = product["salesRank"]
                    if isinstance(sales_rank, dict):
                        bsr = sales_rank.get("current") or sales_rank.get("latest")
                    elif isinstance(sales_rank, (int, float)):
                        bsr = int(sales_rank)
                
                # Vérifier si BSR est dans la plage configurée
                if bsr is not None and category_config.bsr_max:
                    if bsr > category_config.bsr_max:
                        logger.debug(
                            "BSR %s > %s pour %s, ignoré",
                            bsr,
                            category_config.bsr_max,
                            asin,
                        )
                        continue

                # Estimations de ventes par jour
                # Keepa peut fournir salesRankDrops90 ou d'autres métriques
                estimated_sales_per_day = None
                if "stats" in product:
                    stats = product["stats"]
                    if isinstance(stats, dict):
                        # salesRankDrops90 peut donner une idée des ventes
                        rank_drops = stats.get("salesRankDrops90", 0)
                        if rank_drops > 0:
                            # Estimation approximative: plus de drops = plus de ventes
                            # Formule simple: rank_drops / 90 jours
                            estimated_sales_per_day = Decimal(str(rank_drops / 90)).quantize(
                                Decimal("0.01")
                            )

                # Reviews
                reviews_count = None
                rating = None
                if "reviews" in product:
                    reviews = product["reviews"]
                    if isinstance(reviews, dict):
                        reviews_count = reviews.get("count") or reviews.get("total")
                        rating = reviews.get("rating") or reviews.get("average")
                elif "reviewCount" in product:
                    reviews_count = product["reviewCount"]
                elif "totalReviews" in product:
                    reviews_count = product["totalReviews"]

                if "rating" in product:
                    rating = product["rating"]
                elif "avgRating" in product:
                    rating = product["avgRating"]

                # Convertir rating en Decimal
                if rating is not None:
                    try:
                        rating = Decimal(str(rating)).quantize(Decimal("0.01"))
                    except (ValueError, TypeError):
                        rating = None

                # Créer le produit normalisé
                normalized_product = KeepaProduct(
                    asin=asin,
                    title=title,
                    category=category_config.name,
                    avg_price=avg_price,
                    bsr=bsr,
                    estimated_sales_per_day=estimated_sales_per_day,
                    reviews_count=reviews_count,
                    rating=rating,
                    raw_data=product,
                )

                normalized.append(normalized_product)

            except Exception as e:
                logger.warning(
                    "Erreur lors de la normalisation d'un produit Keepa: %s",
                    str(e),
                    exc_info=True,
                )
                continue

        logger.info(
            "%s produits normalisés sur %s reçus pour la catégorie %s",
            len(normalized),
            len(products),
            category_config.name,
        )

        return normalized

