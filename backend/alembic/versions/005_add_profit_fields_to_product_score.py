"""Add profit fields to ProductScore

Revision ID: 005_add_profit_fields
Revises: 004_listing_template_and_bundle
Create Date: 2025-12-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Numeric

# revision identifiers, used by Alembic.
revision = '005_add_profit_fields'
down_revision = '004_listing_template_and_bundle'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajouter les champs profit au modèle ProductScore."""
    op.add_column(
        'product_scores',
        sa.Column('gross_profit', Numeric(10, 2), nullable=True, comment='Marge brute (EUR)')
    )
    op.add_column(
        'product_scores',
        sa.Column('gross_margin_percent', Numeric(5, 2), nullable=True, comment='Marge brute en pourcentage')
    )
    op.add_column(
        'product_scores',
        sa.Column('net_profit_estimated', Numeric(10, 2), nullable=True, comment='Profit net estimé après IS/CFE (EUR)')
    )


def downgrade() -> None:
    """Supprimer les champs profit du modèle ProductScore."""
    op.drop_column('product_scores', 'net_profit_estimated')
    op.drop_column('product_scores', 'gross_margin_percent')
    op.drop_column('product_scores', 'gross_profit')



