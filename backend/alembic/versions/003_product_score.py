"""Add ProductScore table

Revision ID: 003_product_score
Revises: 002_sourcing_option
Create Date: 2025-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Numeric, DateTime, CheckConstraint

# revision identifiers, used by Alembic.
revision = '003_product_score'
down_revision = '002_sourcing_option'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Créer la table product_scores."""
    op.create_table(
        'product_scores',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('product_candidate_id', UUID(as_uuid=True), nullable=False),
        sa.Column('sourcing_option_id', UUID(as_uuid=True), nullable=False),
        sa.Column('selling_price_target', Numeric(10, 2), nullable=False),
        sa.Column('amazon_fees_estimate', Numeric(10, 2), nullable=True),
        sa.Column('logistics_cost_estimate', Numeric(10, 2), nullable=True),
        sa.Column('margin_absolute', Numeric(10, 2), nullable=True),
        sa.Column('margin_percent', Numeric(5, 2), nullable=True),
        sa.Column('estimated_sales_per_day', Numeric(10, 2), nullable=True),
        sa.Column('risk_factor', Numeric(3, 2), nullable=False, server_default='0.0'),
        sa.Column('global_score', Numeric(10, 2), nullable=True),
        sa.Column('decision', String(20), nullable=False, server_default='B_review'),
        sa.Column('created_at', DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Créer les foreign keys
    op.create_foreign_key(
        'fk_product_scores_product_candidate_id',
        'product_scores',
        'product_candidates',
        ['product_candidate_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_product_scores_sourcing_option_id',
        'product_scores',
        'sourcing_options',
        ['sourcing_option_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Créer les index
    op.create_index(
        'ix_product_scores_product_candidate_id',
        'product_scores',
        ['product_candidate_id']
    )
    
    op.create_index(
        'ix_product_scores_sourcing_option_id',
        'product_scores',
        ['sourcing_option_id']
    )
    
    op.create_index(
        'ix_product_scores_decision',
        'product_scores',
        ['decision']
    )
    
    # Créer la contrainte CHECK pour decision
    op.create_check_constraint(
        'check_valid_decision',
        'product_scores',
        "decision IN ('A_launch', 'B_review', 'C_drop')"
    )


def downgrade() -> None:
    """Supprimer la table product_scores."""
    op.drop_table('product_scores')

