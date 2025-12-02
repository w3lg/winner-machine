"""Add SourcingOption table

Revision ID: 002_sourcing_option
Revises: 001_initial_product_candidate
Create Date: 2025-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import String, Numeric, Integer, DateTime, Boolean

# revision identifiers, used by Alembic.
revision = '002_sourcing_option'
down_revision = '001_initial_product_candidate'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Créer la table sourcing_options."""
    op.create_table(
        'sourcing_options',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('product_candidate_id', UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_name', String(255), nullable=False),
        sa.Column('sourcing_type', String(50), nullable=False),
        sa.Column('unit_cost', Numeric(10, 2), nullable=True),
        sa.Column('shipping_cost_unit', Numeric(10, 2), nullable=True),
        sa.Column('moq', Integer, nullable=True),
        sa.Column('lead_time_days', Integer, nullable=True),
        sa.Column('brandable', Boolean, nullable=False, server_default='false'),
        sa.Column('bundle_capable', Boolean, nullable=False, server_default='false'),
        sa.Column('notes', String(500), nullable=True),
        sa.Column('raw_supplier_data', JSON, nullable=True),
        sa.Column('created_at', DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Créer la foreign key
    op.create_foreign_key(
        'fk_sourcing_options_product_candidate_id',
        'sourcing_options',
        'product_candidates',
        ['product_candidate_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Créer les index
    op.create_index('ix_sourcing_options_product_candidate_id', 'sourcing_options', ['product_candidate_id'])
    op.create_index('ix_sourcing_options_supplier_name', 'sourcing_options', ['supplier_name'])
    op.create_index('ix_sourcing_options_sourcing_type', 'sourcing_options', ['sourcing_type'])


def downgrade() -> None:
    """Supprimer la table sourcing_options."""
    op.drop_table('sourcing_options')

