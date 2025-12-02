"""
Modèle Bundle - Bundles de produits.

Représente des combinaisons de produits (pack multi-pièces, avec accessoire, etc.).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Bundle(Base):
    """
    Bundle de produits.

    Représente une combinaison de produits (ex: pack x2, avec accessoire, etc.).
    Structure simple pour V1, logique complexe à venir dans les versions suivantes.
    """

    __tablename__ = "bundles"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Foreign key vers le produit principal
    product_candidate_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("product_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Référence au produit candidat principal",
    )

    # Type de bundle
    bundle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type de bundle: pack_x2, with_accessory, premium, etc.",
    )

    # Composants du bundle (JSON array)
    components: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Liste des composants [{sku, asin, quantity, name}]",
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes additionnelles sur le bundle",
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

    def __repr__(self) -> str:
        return (
            f"<Bundle(product={self.product_candidate_id}, "
            f"type={self.bundle_type})>"
        )

