"""
Modèle ProductScore - Scores de rentabilité pour les options de sourcing.

Représente le score calculé pour une combinaison ProductCandidate + SourcingOption,
incluant les marges, risques, et décision finale.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ProductScore(Base):
    """
    Score de rentabilité pour une combinaison produit + option de sourcing.

    Contient tous les calculs de marge, frais Amazon, score global,
    et la décision finale (A_launch, B_review, C_drop).
    """

    __tablename__ = "product_scores"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Foreign keys
    product_candidate_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("product_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence au produit candidat",
    )

    sourcing_option_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("sourcing_options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence à l'option de sourcing",
    )

    # Prix cible et frais
    selling_price_target: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Prix de vente cible (EUR)",
    )

    amazon_fees_estimate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Estimation des frais Amazon (commission + FBA)",
    )

    logistics_cost_estimate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Estimation des coûts logistiques (EUR)",
    )

    # Marges
    margin_absolute: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Marge absolue (EUR) = prix vente - coûts - frais",
    )

    margin_percent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Marge en pourcentage (0-100)",
    )

    # Métriques de marché
    estimated_sales_per_day: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Estimation des ventes par jour",
    )

    # Risque et score
    risk_factor: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0.0"),
        comment="Facteur de risque (0.0-1.0, plus élevé = plus risqué)",
    )

    global_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Score global de rentabilité",
    )

    # Décision
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="B_review",
        index=True,
        comment="Décision: A_launch (lancer), B_review (réviser), C_drop (abandonner)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )

    # Contrainte pour les valeurs valides de decision
    __table_args__ = (
        CheckConstraint(
            "decision IN ('A_launch', 'B_review', 'C_drop')",
            name="check_valid_decision",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ProductScore(product={self.product_candidate_id}, "
            f"option={self.sourcing_option_id}, score={self.global_score}, "
            f"decision={self.decision})>"
        )

