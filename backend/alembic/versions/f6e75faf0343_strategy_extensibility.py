"""strategy_extensibility

Revision ID: f6e75faf0343
Revises: cc7962a16cae
Create Date: 2026-07-14 11:57:46.121747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6e75faf0343'
down_revision: Union[str, Sequence[str], None] = 'cc7962a16cae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('explainability_snapshot', schema=None) as batch_op:
        batch_op.add_column(sa.Column('strategy_id', sa.String(), server_default='pms_default', nullable=False))
        batch_op.drop_constraint('uq_explainability_snapshot_symbol_score', type_='unique')
        batch_op.create_unique_constraint('uq_explainability_snapshot_symbol_score', ['snapshot_id', 'symbol', 'score_type', 'strategy_id'])

    with op.batch_alter_table('score_snapshot', schema=None) as batch_op:
        batch_op.add_column(sa.Column('strategy_id', sa.String(), server_default='pms_default', nullable=False))
        batch_op.add_column(sa.Column('custom_metrics', sa.Text(), nullable=True))
        batch_op.drop_constraint('uq_score_snapshot_symbol', type_='unique')
        batch_op.create_unique_constraint('uq_score_snapshot_symbol', ['snapshot_id', 'symbol', 'strategy_id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('score_snapshot', schema=None) as batch_op:
        batch_op.drop_constraint('uq_score_snapshot_symbol', type_='unique')
        batch_op.create_unique_constraint('uq_score_snapshot_symbol', ['snapshot_id', 'symbol'])
        batch_op.drop_column('custom_metrics')
        batch_op.drop_column('strategy_id')

    with op.batch_alter_table('explainability_snapshot', schema=None) as batch_op:
        batch_op.drop_constraint('uq_explainability_snapshot_symbol_score', type_='unique')
        batch_op.create_unique_constraint('uq_explainability_snapshot_symbol_score', ['snapshot_id', 'symbol', 'score_type'])
        batch_op.drop_column('strategy_id')
