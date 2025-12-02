"""Add ListingTemplate and Bundle tables

Revision ID: 004_listing_template_and_bundle
Revises: 003_product_score
Create Date: 2025-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import String, Boolean, Text, DateTime, CheckConstraint

# revision identifiers, used by Alembic.
revision = '004_listing_template_and_bundle'
down_revision = '003_product_score'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Créer les tables listing_templates et bundles."""
    
    # Table listing_templates
    op.create_table(
        'listing_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('product_candidate_id', UUID(as_uuid=True), nullable=False),
        sa.Column('sourcing_option_id', UUID(as_uuid=True), nullable=True),
        sa.Column('brandable', Boolean, nullable=False, server_default='false'),
        sa.Column('reference_asin', String(20), nullable=True),
        sa.Column('strategy', String(50), nullable=False, server_default='clone_best'),
        sa.Column('brand_name', String(255), nullable=True),
        sa.Column('title', String(500), nullable=False),
        sa.Column('bullets', JSON, nullable=True),
        sa.Column('description', Text, nullable=True),
        sa.Column('search_terms', Text, nullable=True),
        sa.Column('faq', JSON, nullable=True),
        sa.Column('status', String(20), nullable=False, server_default='draft'),
        sa.Column('marketplace', String(50), nullable=False, server_default='amazon_fr'),
        sa.Column('created_at', DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Foreign keys pour listing_templates
    op.create_foreign_key(
        'fk_listing_templates_product_candidate_id',
        'listing_templates',
        'product_candidates',
        ['product_candidate_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_listing_templates_sourcing_option_id',
        'listing_templates',
        'sourcing_options',
        ['sourcing_option_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Indexes pour listing_templates
    op.create_index(
        'ix_listing_templates_product_candidate_id',
        'listing_templates',
        ['product_candidate_id']
    )
    
    op.create_index(
        'ix_listing_templates_sourcing_option_id',
        'listing_templates',
        ['sourcing_option_id']
    )
    
    op.create_index(
        'ix_listing_templates_status',
        'listing_templates',
        ['status']
    )
    
    # Contraintes CHECK pour listing_templates
    op.create_check_constraint(
        'check_valid_strategy',
        'listing_templates',
        "strategy IN ('clone_best', 'improve_existing', 'brand_new')"
    )
    
    op.create_check_constraint(
        'check_valid_status',
        'listing_templates',
        "status IN ('draft', 'ready', 'exported', 'published')"
    )
    
    # Table bundles
    op.create_table(
        'bundles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('product_candidate_id', UUID(as_uuid=True), nullable=False),
        sa.Column('bundle_type', String(50), nullable=False),
        sa.Column('components', JSON, nullable=True),
        sa.Column('notes', Text, nullable=True),
        sa.Column('created_at', DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Foreign key pour bundles
    op.create_foreign_key(
        'fk_bundles_product_candidate_id',
        'bundles',
        'product_candidates',
        ['product_candidate_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Index pour bundles
    op.create_index(
        'ix_bundles_product_candidate_id',
        'bundles',
        ['product_candidate_id']
    )


def downgrade() -> None:
    """Supprimer les tables listing_templates et bundles."""
    op.drop_table('bundles')
    op.drop_table('listing_templates')

