"""add_area_destino_to_tickets

Revision ID: 05b1c1a5e3d5
Revises: e5244117f219
Create Date: 2026-02-02 19:26:27.777508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05b1c1a5e3d5'
down_revision: Union[str, Sequence[str], None] = 'e5244117f219'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add area_destino_id column to tickets table
    op.add_column('tickets', 
        sa.Column('area_destino_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_tickets_area_destino',
        'tickets', 'areas',
        ['area_destino_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('fk_tickets_area_destino', 'tickets', type_='foreignkey')
    
    # Drop column
    op.drop_column('tickets', 'area_destino_id')
