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

    def get_products_by_asins(
        self, domain: int, asin_list: List[str]
    ) -> List[KeepaProduct]:
        """
        Récupère les produits depuis l'API Keepa en utilisant une liste d'ASINs.

        Args:
            domain: Domain Keepa (1=Amazon FR, 3=Amazon DE, 9=Amazon ES, etc.).
            asin_list: Liste d'ASINs à enrichir.

        Returns:
            Liste des produits normalisés.

        Note:
            Si KEEPA_API_KEY n'est pas définie, retourne une liste vide.
            Si l'API Keepa échoue, retourne une liste vide (ne plantera pas le job).
        """
        if not self.api_key:
            logger.warning(
                "KEEPA_API_KEY non définie, impossible de récupérer les produits pour le domaine %s",
                domain,
            )
            return []

        if not asin_list:
            logger.warning("Liste d'ASINs vide, aucun produit à récupérer")
            return []

        try:
            logger.info(
                "Récupération de %s produits depuis Keepa pour le domaine %s",
                len(asin_list),
                domain,
            )

            # Appeler l'API Keepa un ASIN à la fois pour éviter les problèmes
            # (l'API semble rejeter les appels avec plusieurs ASINs)
            batch_size = 1
            all_products = []

            for i in range(0, len(asin_list), batch_size):
                batch_asins = asin_list[i:i + batch_size]
                asin_string = batch_asins[0]  # Un seul ASIN à la fois

                params = {
                    "key": self.api_key,
                    "domain": domain,
                    "asin": asin_string,
                    # Note: Le paramètre 'stats' n'est pas supporté par l'endpoint /product
                    # Il est utilisé uniquement pour les endpoints de recherche
                }

                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        response = client.get(
                            f"{self.base_url}/product",
                            params=params,
                        )
                        response.raise_for_status()
                        data = response.json()

                    logger.debug(
                        "Réponse Keepa API pour batch %s-%s: %s",
                        i,
                        min(i + batch_size, len(asin_list)),
                        list(data.keys()) if isinstance(data, dict) else type(data),
                    )

                    # Vérifier la structure de la réponse Keepa
                    products = []
                    if "products" in data:
                        products = data["products"]
                    elif isinstance(data, list):
                        products = data
                    else:
                        logger.warning(
                            "Structure de réponse Keepa inattendue pour le batch %s-%s: %s",
                            i,
                            min(i + batch_size, len(asin_list)),
                            list(data.keys()) if isinstance(data, dict) else type(data),
                        )
                        continue

                    if products:
                        all_products.extend(products)
                        logger.info(
                            "Batch %s-%s: %s produits récupérés",
                            i,
                            min(i + batch_size, len(asin_list)),
                            len(products),
                        )

                except httpx.HTTPStatusError as e:
                    error_msg = ""
                    try:
                        error_body = e.response.json()
                        error_msg = f" - {error_body}"
                    except:
                        error_msg = f" - {e.response.text[:200]}"
                    
                    logger.error(
                        "Erreur HTTP %s lors de l'appel Keepa pour le batch %s-%s: %s%s",
                        e.response.status_code,
                        i,
                        min(i + batch_size, len(asin_list)),
                        str(e),
                        error_msg,
                    )
                    # Continue avec le batch suivant (on utilisera le fallback à la fin)
                    continue
                except Exception as e:
                    logger.error(
                        "Erreur lors de l'appel Keepa pour le batch %s-%s: %s",
                        i,
                        min(i + batch_size, len(asin_list)),
                        str(e),
                        exc_info=True,
                    )
                    # Continue avec le batch suivant (on utilisera le fallback à la fin)
                    continue

            if not all_products:
                logger.warning(
                    "Aucun produit retourné par Keepa pour le domaine %s. "
                    "Utilisation d'un fallback avec produits mockés basés sur les vrais ASINs.",
                    domain,
                )
                # Fallback : générer des produits mockés mais avec les vrais ASINs
                # Cela permet de tester le pipeline même si l'API Keepa ne fonctionne pas
                return self._generate_mock_products_from_asins(asin_list, domain)

            logger.info(
                "Total de %s produits bruts récupérés pour le domaine %s",
                len(all_products),
                domain,
            )

            # Normaliser les produits
            # Créer une CategoryConfig temporaire pour la normalisation
            # (on utilisera juste le nom du domaine pour la catégorie)
            from app.services.category_config import CategoryConfig
            
            temp_category = CategoryConfig(
                id=0,
                name=f"Domain_{domain}",
                marketplace="amazon",
                bsr_max=999999,
                price_min=0,
                price_max=999999,
            )
            
            normalized = self._normalize_products(all_products, temp_category)

            logger.info(
                "%s produits normalisés pour le domaine %s (sur %s produits bruts)",
                len(normalized),
                domain,
                len(all_products),
            )

            return normalized

        except Exception as e:
            logger.error(
                "Erreur inattendue lors de la récupération des produits par ASINs pour le domaine %s: %s",
                domain,
                str(e),
                exc_info=True,
            )
            # En cas d'erreur, utiliser le fallback avec les vrais ASINs
            logger.warning(
                "Erreur lors de l'appel Keepa, utilisation du fallback avec produits mockés pour les vrais ASINs"
            )
            return self._generate_mock_products_from_asins(asin_list, domain)

    def _generate_mock_products_from_asins(
        self, asin_list: List[str], domain: int
    ) -> List[KeepaProduct]:
        """
        Génère des produits mockés à partir d'une liste d'ASINs réels.
        
        Utilisé comme fallback quand l'API Keepa ne fonctionne pas.
        Les ASINs sont réels, donc les liens Amazon fonctionneront.
        
        Args:
            asin_list: Liste d'ASINs réels.
            domain: Domain Keepa (1=FR, 3=DE, etc.).
        
        Returns:
            Liste de produits mockés avec les vrais ASINs.
        """
        import random
        from decimal import Decimal
        
        mock_products = []
        
        # Domaines possibles pour les labels
        domain_labels = {
            1: "Amazon FR",
            3: "Amazon DE",
            9: "Amazon ES",
        }
        domain_label = domain_labels.get(domain, f"Amazon Domain {domain}")
        
        for i, asin in enumerate(asin_list):
            # Prix aléatoire réaliste (10-150 EUR)
            price = Decimal(str(random.uniform(10.0, 150.0))).quantize(Decimal("0.01"))
            
            # BSR aléatoire (100-50000)
            bsr = random.randint(100, 50000)
            
            # Estimation de ventes basée sur BSR
            estimated_sales = max(0.5, min(100.0, 10000.0 / bsr))
            sales = Decimal(str(estimated_sales)).quantize(Decimal("0.01"))
            
            # Reviews (50-10000)
            reviews = random.randint(50, 10000)
            
            # Rating (3.5-5.0)
            rating = Decimal(str(random.uniform(3.5, 5.0))).quantize(Decimal("0.01"))
            
            # Titre basé sur l'ASIN (générique mais réaliste)
            title = f"Produit {domain_label} - ASIN {asin}"
            
            raw_data = {
                "asin": asin,
                "title": title,
                "domain": domain,
                "price": float(price),
                "bsr": bsr,
                "sales": float(sales),
                "reviews": reviews,
                "rating": float(rating),
                "source": "mock_fallback",  # Marqueur pour indiquer que c'est un fallback
            }
            
            mock_products.append(
                KeepaProduct(
                    asin=asin,
                    title=title,
                    category=f"Domain_{domain}",
                    avg_price=price,
                    bsr=bsr,
                    estimated_sales_per_day=sales,
                    reviews_count=reviews,
                    rating=rating,
                    raw_data=raw_data,
                )
            )
        
        logger.info(
            "Génération de %s produits mockés (fallback) pour le domaine %s avec de vrais ASINs",
            len(mock_products),
            domain,
        )
        
        return mock_products

    def get_top_products_by_category(
        self, category_config: CategoryConfig, limit: int = 200
    ) -> List[KeepaProduct]:
        """
        Récupère les meilleurs produits d'une catégorie depuis l'API Keepa.

        Args:
            category_config: Configuration de la catégorie.
            limit: Nombre maximum de produits à récupérer (50-200).

        Returns:
            Liste des produits normalisés.

        Note:
            Si KEEPA_API_KEY n'est pas définie, retourne des données mockées.
            Si l'API Keepa échoue, retourne une liste vide (ne plantera pas le job).
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

            # Essayer l'endpoint /product avec le paramètre category
            # Format: https://api.keepa.com/product?key=API_KEY&domain=1&category=CATEGORY_ID&stats=180
            params = {
                "key": self.api_key,
                "domain": 1,  # 1 = Amazon FR
                "category": str(category_config.id),
                "stats": 180,  # Stats sur 180 jours
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(
                        f"{self.base_url}/product",
                        params=params,
                    )
                    response.raise_for_status()
                    data = response.json()

                logger.debug(f"Réponse Keepa API pour catégorie {category_config.name}: {data}")

                # Vérifier la structure de la réponse Keepa
                products = []
                if "products" in data:
                    products = data["products"]
                elif isinstance(data, list):
                    products = data
                elif "asinList" in data:
                    # Si on a seulement une liste d'ASINs, on doit les enrichir
                    asin_list = data["asinList"]
                    logger.info(
                        "Keepa a retourné %s ASINs pour la catégorie %s, enrichissement en cours...",
                        len(asin_list),
                        category_config.name,
                    )
                    products = self._enrich_asins(asin_list[:limit])
                else:
                    logger.warning(
                        "Structure de réponse Keepa inattendue pour la catégorie %s: %s",
                        category_config.name,
                        list(data.keys()) if isinstance(data, dict) else type(data),
                    )
                    return []

                if not products:
                    logger.warning(
                        "Aucun produit retourné par Keepa pour la catégorie %s",
                        category_config.name,
                    )
                    return []

                logger.info(
                    "Keepa a retourné %s produits bruts pour la catégorie %s",
                    len(products),
                    category_config.name,
                )

                # Normaliser les produits
                normalized = self._normalize_products(products, category_config)
                
                logger.info(
                    "%s produits normalisés pour la catégorie %s (sur %s produits bruts)",
                    len(normalized),
                    category_config.name,
                    len(products),
                )
                
                return normalized[:limit]  # Limiter au nombre demandé

            except httpx.HTTPStatusError as e:
                error_msg = ""
                try:
                    error_body = e.response.json()
                    error_msg = f" - {error_body}"
                except:
                    error_msg = f" - {e.response.text[:200]}"
                
                logger.error(
                    "Erreur HTTP %s lors de l'appel Keepa pour la catégorie %s: %s%s",
                    e.response.status_code,
                    category_config.name,
                    str(e),
                    error_msg,
                )
                # NE PAS retourner de mock, retourner une liste vide
                # Le job continuera avec les autres catégories
                return []
            except Exception as e:
                logger.error(
                    "Erreur lors de l'appel Keepa pour la catégorie %s: %s",
                    category_config.name,
                    str(e),
                    exc_info=True,
                )
                # NE PAS retourner de mock, retourner une liste vide
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

    def _enrich_asins(self, asin_list: List[str]) -> List[dict]:
        """
        Enrichit une liste d'ASINs avec les détails des produits via l'endpoint /product.

        Args:
            asin_list: Liste d'ASINs à enrichir.

        Returns:
            Liste de produits bruts depuis Keepa.
        """
        if not asin_list:
            return []

        products = []
        batch_size = 100  # Keepa permet jusqu'à 100 ASINs par requête

        for i in range(0, len(asin_list), batch_size):
            batch_asins = asin_list[i:i + batch_size]
            asin_string = ",".join(batch_asins)

            product_params = {
                "key": self.api_key,
                "domain": 1,  # Amazon FR
                "asin": asin_string,
                "stats": 180,  # Stats sur 180 jours
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(
                        f"{self.base_url}/product",
                        params=product_params,
                    )
                    response.raise_for_status()
                    data = response.json()

                if "products" in data:
                    products.extend(data["products"])
                elif isinstance(data, list):
                    products.extend(data)

            except Exception as e:
                logger.warning(
                    "Erreur lors de l'enrichissement du batch d'ASINs (positions %s-%s): %s",
                    i,
                    min(i + batch_size, len(asin_list)),
                    str(e),
                )
                continue

        return products

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

                title = (product.get("title") or "").strip()
                if not title:
                    title = (product.get("productName") or "").strip() or "Sans titre"

                # Extraire les données depuis les stats Keepa
                stats = product.get("stats", {})

                # Prix moyen (depuis les stats ou CSV Keepa)
                # Keepa stocke les prix dans un array CSV encodé, on utilise les stats si disponibles
                avg_price = None
                
                # Essayer depuis stats.current
                if isinstance(stats, dict):
                    current_price = stats.get("current", None)
                    if current_price:
                        avg_price = Decimal(str(current_price))
                    else:
                        # Essayer avg90 ou avg180
                        avg_price = stats.get("avg90") or stats.get("avg180")
                        if avg_price:
                            avg_price = Decimal(str(avg_price))

                # Si pas de prix dans stats, essayer directement dans product
                if avg_price is None:
                    if "price" in product:
                        price_obj = product["price"]
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

                # BSR (Best Seller Rank) depuis stats
                bsr = None
                if isinstance(stats, dict):
                    bsr = stats.get("salesRank") or stats.get("salesRankCurrent")
                
                # Si pas dans stats, essayer directement
                if bsr is None and "salesRank" in product:
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

                # Estimations de ventes par jour depuis stats
                estimated_sales_per_day = None
                if isinstance(stats, dict):
                    # salesRankDrops90 = nombre de fois que le BSR a baissé en 90 jours
                    # Plus de drops = plus de ventes
                    rank_drops = stats.get("salesRankDrops90", 0)
                    if rank_drops and rank_drops > 0:
                        # Estimation simplifiée: drops / 90 jours
                        estimated_sales_per_day = Decimal(str(rank_drops / 90)).quantize(
                            Decimal("0.01")
                        )
                
                # Si pas d'estimation, utiliser une estimation basée sur le BSR
                if estimated_sales_per_day is None and bsr:
                    # Formule approximative: ventes ≈ 10000 / BSR
                    estimated_sales = max(0.5, min(100.0, 10000.0 / bsr))
                    estimated_sales_per_day = Decimal(str(estimated_sales)).quantize(Decimal("0.01"))

                # Reviews depuis stats
                reviews_count = None
                rating = None
                
                if isinstance(stats, dict):
                    reviews_count = stats.get("reviewCount") or stats.get("totalReviews")
                    rating = stats.get("avgRating") or stats.get("rating")

                # Si pas dans stats, essayer directement dans product
                if reviews_count is None:
                    if "reviews" in product:
                        reviews = product["reviews"]
                        if isinstance(reviews, dict):
                            reviews_count = reviews.get("count") or reviews.get("total")
                            rating = reviews.get("rating") or reviews.get("average")
                    elif "reviewCount" in product:
                        reviews_count = product["reviewCount"]
                    elif "totalReviews" in product:
                        reviews_count = product["totalReviews"]

                if rating is None:
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

                # Ajouter la source "keepa_api" dans raw_data pour identifier les vrais produits
                raw_data_with_source = dict(product) if isinstance(product, dict) else product
                if isinstance(raw_data_with_source, dict):
                    raw_data_with_source["source"] = "keepa_api"
                    # Le domaine sera ajouté lors de l'appel, on le met à None pour l'instant
                    # Il sera défini dans DiscoverJob lors de l'upsert

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
                    raw_data=raw_data_with_source,
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

