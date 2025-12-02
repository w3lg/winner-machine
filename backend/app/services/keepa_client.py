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

            # Appel à l'API Keepa pour récupérer les bestsellers par catégorie
            # Endpoint: https://api.keepa.com/bestsellers
            # domain=1 = Amazon FR
            params = {
                "key": self.api_key,
                "domain": 1,  # 1 = Amazon FR
                "category": str(category_config.id),
                "range": min(limit, 200),  # Nombre de produits (max 200)
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(
                        f"{self.base_url}/bestsellers",
                        params=params,
                    )
                    response.raise_for_status()
                    data = response.json()

                # Vérifier si la réponse contient des ASINs
                if "asinList" not in data or not data.get("asinList"):
                    logger.warning(
                        "Aucun ASIN retourné par Keepa bestsellers pour la catégorie %s",
                        category_config.name,
                    )
                    return []

                asin_list = data["asinList"][:limit]  # Limiter au nombre demandé
                logger.info(
                    "Keepa bestsellers a retourné %s ASINs pour la catégorie %s",
                    len(asin_list),
                    category_config.name,
                )

                # Récupérer les détails de chaque produit via l'endpoint /product
                products = []
                batch_size = 100  # Keepa permet jusqu'à 100 ASINs par requête
                
                for i in range(0, len(asin_list), batch_size):
                    batch_asins = asin_list[i:i + batch_size]
                    asin_string = ",".join(batch_asins)
                    
                    product_params = {
                        "key": self.api_key,
                        "domain": 1,
                        "asin": asin_string,
                        "stats": 180,
                    }
                    
                    with httpx.Client(timeout=self.timeout) as client:
                        batch_response = client.get(
                            f"{self.base_url}/product",
                            params=product_params,
                        )
                        batch_response.raise_for_status()
                        batch_data = batch_response.json()
                        
                        if "products" in batch_data:
                            products.extend(batch_data["products"])

                if not products:
                    logger.warning(
                        "Aucun produit détaillé retourné pour les ASINs de la catégorie %s",
                        category_config.name,
                    )
                    return []

                # Normaliser les produits
                normalized = self._normalize_products(products, category_config)
                return normalized

            except httpx.HTTPStatusError as e:
                # Si /bestsellers ne fonctionne pas, utiliser le mode mock enrichi
                logger.warning(
                    "Endpoint /bestsellers non disponible ou erreur HTTP %s pour la catégorie %s. "
                    "Utilisation du mode mock enrichi (%s produits)",
                    e.response.status_code,
                    category_config.name,
                    limit,
                )
                return self._mock_products(category_config, limit)
            except Exception as e:
                # En cas d'erreur inattendue, utiliser le mode mock
                logger.warning(
                    "Erreur lors de l'appel Keepa pour la catégorie %s: %s. "
                    "Utilisation du mode mock enrichi",
                    category_config.name,
                    str(e),
                )
                return self._mock_products(category_config, limit)

        except httpx.RequestError as e:
            logger.warning(
                "Erreur de requête Keepa pour la catégorie %s: %s. "
                "Utilisation du mode mock enrichi",
                category_config.name,
                str(e),
            )
            return self._mock_products(category_config, limit)
        except Exception as e:
            logger.warning(
                "Erreur inattendue lors de l'appel Keepa pour la catégorie %s: %s. "
                "Utilisation du mode mock enrichi",
                category_config.name,
                str(e),
                exc_info=True,
            )
            return self._mock_products(category_config, limit)

    def _mock_products(
        self, category_config: CategoryConfig, limit: int
    ) -> List[KeepaProduct]:
        """
        Génère des produits mockés pour le développement.
        
        NOTE: Cette méthode génère des produits réalistes pour simuler l'API Keepa
        jusqu'à ce qu'une méthode de recherche par catégorie soit trouvée.

        Args:
            category_config: Configuration de la catégorie.
            limit: Nombre de produits à générer (20-200).

        Returns:
            Liste de produits mockés.
        """
        import random
        import string
        from decimal import Decimal

        # Générer entre 20 et limit produits (ou limit si < 20)
        num_products = max(20, min(limit, 200))
        
        mock_products = []
        
        # Générer des ASINs uniques (format: B + 9 caractères alphanumériques)
        def generate_asin(seed: int) -> str:
            """Génère un ASIN unique basé sur un seed."""
            random.seed(seed + hash(category_config.name))
            chars = string.ascii_uppercase + string.digits
            suffix = ''.join(random.choices(chars, k=9))
            return f"B{suffix}"

        for i in range(num_products):
            asin = generate_asin(i)
            
            # Prix aléatoire dans la plage configurée
            price = Decimal(
                str(
                    random.uniform(
                        category_config.price_min, category_config.price_max
                    )
                )
            ).quantize(Decimal("0.01"))
            
            # BSR aléatoire (plus bas = mieux)
            bsr = random.randint(100, min(category_config.bsr_max, 50000))
            
            # Estimation de ventes par jour basée sur le BSR (BSR plus bas = plus de ventes)
            # Formule simplifiée: ventes ≈ 10000 / BSR
            estimated_sales = max(0.5, min(100.0, 10000.0 / bsr))
            sales = Decimal(str(estimated_sales)).quantize(Decimal("0.01"))
            
            # Reviews (entre 50 et 10000, avec distribution réaliste)
            reviews = random.randint(50, 10000)
            
            # Rating (entre 3.5 et 5.0, avec une moyenne autour de 4.2)
            rating = Decimal(str(random.uniform(3.5, 5.0))).quantize(Decimal("0.01"))
            
            # Titre réaliste basé sur la catégorie
            titles_templates = {
                "Electronics & Photo": [
                    "Câble USB-C haute qualité",
                    "Écouteurs Bluetooth sans fil",
                    "Chargeur rapide universel",
                    "Support téléphone voiture",
                    "Lampe LED rechargeable",
                ],
                "Home & Kitchen": [
                    "Serviette de bain premium",
                    "Moulin à poivre mécanique",
                    "Boîte de rangement hermétique",
                    "Torchon de cuisine absorbant",
                    "Pince à vaisselle silicone",
                ],
                "Sports & Outdoors": [
                    "Gourde isotherme 500ml",
                    "Bandeau sport anti-transpiration",
                    "Corde à sauter réglable",
                    "Sacs lestés ajustables",
                    "Élastique de résistance fitness",
                ],
                "Tools & Home Improvement": [
                    "Perceuse visseuse sans fil",
                    "Échelle pliante 4 marches",
                    "Cutter professionnel sécurisé",
                    "Scie à métaux manuelle",
                    "Ruban adhésif multi-usages",
                ],
                "Beauty & Personal Care": [
                    "Crème hydratante visage bio",
                    "Shampooing cheveux secs",
                    "Rasoir électrique rechargeable",
                    "Déodorant naturel roll-on",
                    "Masque facial purifiant",
                ],
                "Toys & Games": [
                    "Puzzle 1000 pièces",
                    "Jeu de société famille",
                    "Poupée interactive",
                    "Set construction magnétique",
                    "Jeu de cartes éducatif",
                ],
            }
            
            templates = titles_templates.get(
                category_config.name,
                [f"Produit {i+1} - {category_config.name}"]
            )
            title = f"{random.choice(templates)} - Modèle {i+1}"

            raw_data = {
                "asin": asin,
                "title": title,
                "category": category_config.name,
                "price": float(price),
                "bsr": bsr,
                "sales": float(sales),
                "reviews": reviews,
                "rating": float(rating),
                "source": "mock",
            }

            mock_products.append(
                KeepaProduct(
                    asin=asin,
                    title=title,
                    category=category_config.name,
                    avg_price=price,
                    bsr=bsr,
                    estimated_sales_per_day=sales,
                    reviews_count=reviews,
                    rating=rating,
                    raw_data=raw_data,
                )
            )

        logger.info(
            "Génération de %s produits mockés pour la catégorie %s",
            len(mock_products),
            category_config.name,
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

