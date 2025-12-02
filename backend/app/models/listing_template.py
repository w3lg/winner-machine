"""
Modèle ListingTemplate - Templates de listings produits pour Amazon.

Représente une fiche produit générée pour un ProductCandidate,
avec le contenu complet (titre, bullets, description, etc.).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, Text, JSON, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ListingTemplate(Base):
    """
    Template de listing produit pour Amazon.

    Contient toutes les informations nécessaires pour créer une annonce
    sur Amazon, que le produit soit brandable ou non.
    """

    __tablename__ = "listing_templates"

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

    sourcing_option_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("sourcing_options.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Référence à l'option de sourcing utilisée",
    )

    # Type de listing
    brandable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Le produit est-il brandable ?",
    )

    reference_asin: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="ASIN de référence pour non-brandable (produit existant à cloner)",
    )

    strategy: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="clone_best",
        comment="Stratégie: clone_best, improve_existing, brand_new",
    )

    # Contenu de la fiche
    brand_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nom de la marque (si brandable)",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Titre du produit (200 caractères max pour Amazon)",
    )

    bullets: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Liste des bullet points (array de strings)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description détaillée du produit",
    )

    search_terms: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Mots-clés de recherche (séparés par des espaces)",
    )

    faq: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="FAQ (liste de {question, answer})",
    )

    # Métadonnées
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
        comment="Statut: draft, ready, exported, published",
    )

    marketplace: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="amazon_fr",
        comment="Marketplace cible (amazon_fr, amazon_com, etc.)",
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

    # Contraintes
    __table_args__ = (
        CheckConstraint(
            "strategy IN ('clone_best', 'improve_existing', 'brand_new')",
            name="check_valid_strategy",
        ),
        CheckConstraint(
            "status IN ('draft', 'ready', 'exported', 'published')",
            name="check_valid_status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ListingTemplate(product={self.product_candidate_id}, "
            f"brandable={self.brandable}, status={self.status})>"
        )

