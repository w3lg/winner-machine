"""
Modèle SourcingOption - Options de sourcing pour les produits candidats.

Représente les différentes options de sourcing (fournisseurs) disponibles pour un ProductCandidate.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Numeric, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class SourcingOption(Base):
    """
    Option de sourcing pour un produit candidat.

    Représente une option d'approvisionnement depuis un fournisseur,
    avec les détails de coût, délai, MOQ, etc.
    """

    __tablename__ = "sourcing_options"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Foreign key vers ProductCandidate
    product_candidate_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("product_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence au produit candidat",
    )

    # Informations fournisseur
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Nom du fournisseur",
    )

    sourcing_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type de sourcing: import_CN, EU_wholesale, existing_stock, etc.",
    )

    # Coûts
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Coût unitaire du produit (EUR)",
    )

    shipping_cost_unit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Coût de transport par unité (EUR)",
    )

    # Conditions d'approvisionnement
    moq: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Minimum Order Quantity (quantité minimale de commande)",
    )

    lead_time_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Délai de livraison en jours",
    )

    # Options produit
    brandable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Le produit peut-il être brandé ?",
    )

    bundle_capable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Le produit peut-il être vendu en bundle ?",
    )

    # Informations supplémentaires
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Notes additionnelles sur cette option de sourcing",
    )

    raw_supplier_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Données brutes du fournisseur (JSON)",
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

    # Relation SQLAlchemy (optionnel, pour faciliter les requêtes)
    # product_candidate: Mapped["ProductCandidate"] = relationship("ProductCandidate", back_populates="sourcing_options")

    def __repr__(self) -> str:
        return (
            f"<SourcingOption(supplier={self.supplier_name}, "
            f"type={self.sourcing_type}, cost={self.unit_cost})>"
        )

