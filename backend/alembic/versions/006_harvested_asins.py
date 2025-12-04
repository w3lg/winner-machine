"""Create harvested_asins table

Revision ID: 006_harvested_asins
Revises: 005_add_profit_fields_to_product_score
Create Date: 2025-12-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime

# revision identifiers, used by Alembic.
revision = '006_harvested_asins'
down_revision = '005_add_profit_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Créer la table harvested_asins."""
    op.create_table(
        'harvested_asins',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('asin', String(10), nullable=False, unique=True),
        sa.Column('marketplace', String(50), nullable=False, server_default='amazon_fr'),
        sa.Column('source', String(100), nullable=False),
        sa.Column('created_at', DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, server_default=sa.func.now()),
    )
    # Créer les index
    op.create_index('ix_harvested_asins_asin', 'harvested_asins', ['asin'], unique=True)
    op.create_index('ix_harvested_asins_marketplace', 'harvested_asins', ['marketplace'])
    op.create_index('ix_harvested_asins_source', 'harvested_asins', ['source'])
    op.create_index('idx_harvested_asins_marketplace_source', 'harvested_asins', ['marketplace', 'source'])


def downgrade() -> None:
    """Supprimer la table harvested_asins."""
    op.drop_index('idx_harvested_asins_marketplace_source', table_name='harvested_asins')
    op.drop_index('ix_harvested_asins_source', table_name='harvested_asins')
    op.drop_index('ix_harvested_asins_marketplace', table_name='harvested_asins')
    op.drop_index('ix_harvested_asins_asin', table_name='harvested_asins')
    op.drop_table('harvested_asins')

