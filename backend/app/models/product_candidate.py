"""
Modèle ProductCandidate - Produits candidats découverts via Keepa/Amazon.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, String, Numeric, Integer, DateTime, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ProductCandidate(Base):
    """Produit candidat découvert sur Amazon FR via Keepa."""

    __tablename__ = "product_candidates"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    # Identifiant Amazon (unique)
    asin: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        comment="Amazon Standard Identification Number",
    )

    # Informations produit
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Titre du produit",
    )

    category: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Catégorie Keepa du produit",
    )

    source_marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="amazon_fr",
        index=True,
        comment="Marketplace source (amazon_fr, amazon_com, etc.)",
    )

    # Métriques de marché
    avg_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Prix moyen en EUR",
    )

    bsr: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Best Seller Rank (plus bas = mieux)",
    )

    estimated_sales_per_day: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Estimation des ventes par jour",
    )

    reviews_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Nombre d'avis clients",
    )

    rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="Note moyenne (0-5)",
    )

    # Données brutes
    raw_keepa_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Données brutes de l'API Keepa (JSON)",
    )

    # Statut du produit
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new",
        index=True,
        comment="Statut: new, scored, selected, rejected, launched",
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
        return f"<ProductCandidate(asin={self.asin}, title={self.title[:50]}, status={self.status})>"

