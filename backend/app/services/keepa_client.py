"""
Client pour l'API Keepa - Récupération de données produits Amazon.
"""
from typing import List, Optional
from decimal import Decimal
import os

from app.core.config import get_settings
from app.services.category_config import CategoryConfig


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
        self.base_url = "https://keepa.com/api/1.0"

    def get_top_products_by_category(
        self, category_config: CategoryConfig, limit: int = 50
    ) -> List[KeepaProduct]:
        """
        Récupère les meilleurs produits d'une catégorie.

        Args:
            category_config: Configuration de la catégorie.
            limit: Nombre maximum de produits à récupérer.

        Returns:
            Liste des produits normalisés.

        Note:
            Actuellement, cette méthode retourne des données mockées.
            Pour utiliser la vraie API Keepa, décommenter et adapter le code ci-dessous.
        """
        if not self.api_key:
            # Mode mock si pas de clé API
            return self._mock_products(category_config, limit)

        # TODO: Implémenter l'appel réel à l'API Keepa
        # Exemple de structure pour l'API Keepa:
        # response = httpx.get(
        #     f"{self.base_url}/product",
        #     params={
        #         "key": self.api_key,
        #         "domain": 1,  # 1 = Amazon FR
        #         "category": category_config.id,
        #         "stats": 180,  # 6 mois
        #         "rating": 3,
        #     },
        # )
        # products = response.json().get("products", [])
        # return self._normalize_products(products, category_config)

        # Pour l'instant, on retourne des données mockées
        return self._mock_products(category_config, limit)

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
            products: Liste de produits bruts depuis l'API.
            category_config: Configuration de la catégorie.

        Returns:
            Liste de produits normalisés.

        Note:
            À implémenter quand l'API réelle sera connectée.
        """
        # TODO: Implémenter la normalisation des données Keepa
        normalized = []
        for product in products:
            # Parser les données Keepa et créer des KeepaProduct
            pass
        return normalized

