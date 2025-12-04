"""
Job de scoring - Module C.

Calcule les scores de rentabilité pour toutes les combinaisons
ProductCandidate + SourcingOption qui n'ont pas encore de score.
"""
import logging
from typing import Dict, List
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, not_

from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore
from app.services.scoring_service import get_scoring_service

logger = logging.getLogger(__name__)


class ScoringJob:
    """Job pour calculer les scores de rentabilité des produits."""

    def __init__(self, db: Session):
        """
        Initialise le job.

        Args:
            db: Session SQLAlchemy pour la base de données.
        """
        self.db = db
        self.scoring_service = get_scoring_service()

    def run(self, force: bool = False) -> Dict[str, int]:
        """
        Lance le job de scoring.

        Args:
            force: Si True, recalcule les scores pour TOUS les couples (remplace les anciens).
                   Si False, ne traite que les couples sans score (comportement par défaut).

        Returns:
            Dictionnaire avec les statistiques :
            - pairs_scored: nombre de couples scorés
            - products_marked_selected: nombre de produits marqués "selected"
            - products_marked_scored: nombre de produits marqués "scored"
            - products_marked_rejected: nombre de produits marqués "rejected"
        """
        logger.info(f"=== Démarrage du job de scoring (force={force}) ===")

        # Récupérer les couples éligibles
        if force:
            pairs_to_score = self._get_all_pairs()
            # Supprimer les scores existants pour ces couples
            self._delete_existing_scores_for_pairs(pairs_to_score)
        else:
            pairs_to_score = self._get_eligible_pairs()

        if not pairs_to_score:
            logger.warning("Aucun couple (produit, option) éligible pour le scoring. Le job ne fera rien.")
            return {
                "pairs_scored": 0,
                "products_marked_selected": 0,
                "products_marked_scored": 0,
                "products_marked_rejected": 0,
            }

        logger.info(f"Nombre de couples à scorer: {len(pairs_to_score)}")

        stats = {
            "pairs_scored": 0,
            "products_marked_selected": 0,
            "products_marked_scored": 0,
            "products_marked_rejected": 0,
        }

        # Dictionnaire pour stocker les décisions par produit
        product_decisions: Dict[str, List[str]] = defaultdict(list)

        # Calculer les scores pour chaque couple
        for candidate, option in pairs_to_score:
            try:
                logger.debug(
                    f"Calcul du score pour {candidate.asin} + {option.supplier_name} "
                    f"(option ID: {option.id})"
                )

                # Calculer le score
                product_score = self.scoring_service.score_product_option(candidate, option)

                # Ajouter à la session
                self.db.add(product_score)
                stats["pairs_scored"] += 1

                # Stocker la décision pour ce produit
                product_decisions[str(candidate.id)].append(product_score.decision)

                logger.debug(
                    f"Score calculé: decision={product_score.decision}, "
                    f"global_score={product_score.global_score}, "
                    f"margin_percent={product_score.margin_percent}"
                )

            except Exception as e:
                logger.error(
                    f"Erreur lors du scoring de {candidate.asin} + {option.supplier_name}: {str(e)}",
                    exc_info=True,
                )
                # Continue avec le couple suivant
                continue

        # Commit les scores
        try:
            self.db.commit()
            logger.info(f"✅ {stats['pairs_scored']} score(s) créé(s) en base")
        except Exception as e:
            logger.error(f"Erreur lors du commit des scores: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

        # Mettre à jour le statut des produits selon leurs meilleures décisions
        products_to_update = {}
        for product_id_str, decisions in product_decisions.items():
            from uuid import UUID as UUIDType
            product_id = UUIDType(product_id_str)
            products_to_update[product_id] = self._determine_best_status(decisions)

        # Mettre à jour les statuts
        for product_id, new_status in products_to_update.items():
            try:
                candidate = self.db.query(ProductCandidate).filter(
                    ProductCandidate.id == product_id
                ).first()

                if candidate:
                    old_status = candidate.status
                    candidate.status = new_status
                    logger.debug(
                        f"Statut du produit {candidate.asin} mis à jour: "
                        f"{old_status} → {new_status}"
                    )

                    if new_status == "selected":
                        stats["products_marked_selected"] += 1
                    elif new_status == "scored":
                        stats["products_marked_scored"] += 1
                    elif new_status == "rejected":
                        stats["products_marked_rejected"] += 1

            except Exception as e:
                logger.error(
                    f"Erreur lors de la mise à jour du statut pour le produit {product_id}: {str(e)}",
                    exc_info=True,
                )
                continue

        # Commit les mises à jour de statut
        try:
            self.db.commit()
            logger.info("✅ Statuts des produits mis à jour")
        except Exception as e:
            logger.error(f"Erreur lors du commit des statuts: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

        logger.info("=== Job de scoring terminé avec succès ===")
        logger.info(
            f"Statistiques: {stats['pairs_scored']} couples scorés, "
            f"{stats['products_marked_selected']} produits sélectionnés, "
            f"{stats['products_marked_scored']} produits scorés, "
            f"{stats['products_marked_rejected']} produits rejetés"
        )

        return stats

    def _get_eligible_pairs(self) -> List[tuple]:
        """
        Récupère les couples (ProductCandidate, SourcingOption) qui n'ont pas encore de score.

        Returns:
            Liste de tuples (ProductCandidate, SourcingOption).
        """
        # Récupérer tous les couples qui ont déjà un score
        scored_pairs = (
            self.db.query(
                ProductScore.product_candidate_id,
                ProductScore.sourcing_option_id,
            )
            .distinct()
            .all()
        )
        scored_pairs_set = {(row[0], row[1]) for row in scored_pairs}

        # Récupérer tous les couples (candidate, option)
        all_options = self.db.query(SourcingOption).all()

        # Construire la liste des couples éligibles
        eligible_pairs = []
        for option in all_options:
            candidate = self.db.query(ProductCandidate).filter(
                ProductCandidate.id == option.product_candidate_id
            ).first()

            if candidate and (candidate.id, option.id) not in scored_pairs_set:
                eligible_pairs.append((candidate, option))

        return eligible_pairs

    def _determine_best_status(self, decisions: List[str]) -> str:
        """
        Détermine le meilleur statut pour un produit selon ses décisions de score.

        Args:
            decisions: Liste des décisions (A_launch, B_review, C_drop).

        Returns:
            Statut final: "selected", "scored", ou "rejected".
        """
        if "A_launch" in decisions:
            return "selected"
        elif "B_review" in decisions:
            return "scored"
        else:
            return "rejected"

    def _get_all_pairs(self) -> List[tuple]:
        """
        Récupère TOUS les couples (ProductCandidate, SourcingOption).

        Returns:
            Liste de tuples (ProductCandidate, SourcingOption).
        """
        all_options = self.db.query(SourcingOption).all()
        
        pairs = []
        for option in all_options:
            candidate = self.db.query(ProductCandidate).filter(
                ProductCandidate.id == option.product_candidate_id
            ).first()
            
            if candidate:
                pairs.append((candidate, option))
        
        return pairs

    def _delete_existing_scores_for_pairs(self, pairs: List[tuple]):
        """
        Supprime les scores existants pour les couples donnés.

        Args:
            pairs: Liste de tuples (ProductCandidate, SourcingOption).
        """
        if not pairs:
            return
        
        # Extraire les IDs de candidats et d'options
        candidate_ids = [pair[0].id for pair in pairs]
        option_ids = [pair[1].id for pair in pairs]
        
        deleted_count = (
            self.db.query(ProductScore)
            .filter(
                and_(
                    ProductScore.product_candidate_id.in_(candidate_ids),
                    ProductScore.sourcing_option_id.in_(option_ids)
                )
            )
            .delete(synchronize_session=False)
        )
        
        # Pas de commit ici - sera fait dans run()
        logger.info(f"Suppression de {deleted_count} score(s) existant(s) pour {len(pairs)} couple(s) (commit différé)")

