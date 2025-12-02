"""Initial schema: ProductCandidate

Revision ID: 001_initial_product_candidate
Revises: 
Create Date: 2025-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import String, Numeric, Integer, DateTime

# revision identifiers, used by Alembic.
revision = '001_initial_product_candidate'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Créer la table product_candidates."""
    op.create_table(
        'product_candidates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('asin', String(10), nullable=False, unique=True),
        sa.Column('title', String(500), nullable=True),
        sa.Column('category', String(255), nullable=True),
        sa.Column('source_marketplace', String(50), nullable=False, server_default='amazon_fr'),
        sa.Column('avg_price', Numeric(10, 2), nullable=True),
        sa.Column('bsr', Integer, nullable=True),
        sa.Column('estimated_sales_per_day', Numeric(10, 2), nullable=True),
        sa.Column('reviews_count', Integer, nullable=True),
        sa.Column('rating', Numeric(3, 2), nullable=True),
        sa.Column('raw_keepa_data', JSON, nullable=True),
        sa.Column('status', String(50), nullable=False, server_default='new'),
        sa.Column('created_at', DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, server_default=sa.func.now()),
    )
    # Créer les index
    op.create_index('ix_product_candidates_asin', 'product_candidates', ['asin'], unique=True)
    op.create_index('ix_product_candidates_category', 'product_candidates', ['category'])
    op.create_index('ix_product_candidates_source_marketplace', 'product_candidates', ['source_marketplace'])
    op.create_index('ix_product_candidates_bsr', 'product_candidates', ['bsr'])
    op.create_index('ix_product_candidates_status', 'product_candidates', ['status'])


def downgrade() -> None:
    """Supprimer la table product_candidates."""
    op.drop_table('product_candidates')

