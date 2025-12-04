"""
Modèle HarvestedAsin - ASINs récoltés depuis Apify.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Column, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class HarvestedAsin(Base):
    """ASIN récolté depuis Apify (Best Sellers, Movers & Shakers, etc.)."""

    __tablename__ = "harvested_asins"

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

    # Marketplace
    marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="amazon_fr",
        index=True,
        comment="Marketplace source (amazon_fr, amazon_de, etc.)",
    )

    # Source de récolte
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Source: apify_bestsellers, apify_movers, apify_search, etc.",
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

    # Index composite pour optimiser les requêtes
    __table_args__ = (
        Index("idx_harvested_asins_marketplace_source", "marketplace", "source"),
    )

    def __repr__(self) -> str:
        return f"<HarvestedAsin(asin={self.asin}, marketplace={self.marketplace}, source={self.source})>"

