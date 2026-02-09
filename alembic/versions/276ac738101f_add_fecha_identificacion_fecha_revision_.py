"""add_fecha_identificacion_fecha_revision_tratamiento_to_riesgos

Revision ID: 276ac738101f
Revises: add_iso9001_fields
Create Date: 2026-02-09 15:10:28.863957

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '276ac738101f'
down_revision: Union[str, Sequence[str], None] = 'add_iso9001_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add fecha_identificacion, fecha_revision, and tratamiento columns to riesgos table
    op.add_column('riesgos', sa.Column('fecha_identificacion', sa.Date(), nullable=True))
    op.add_column('riesgos', sa.Column('fecha_revision', sa.Date(), nullable=True))
    op.add_column('riesgos', sa.Column('tratamiento', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the columns
    op.drop_column('riesgos', 'tratamiento')
    op.drop_column('riesgos', 'fecha_revision')
    op.drop_column('riesgos', 'fecha_identificacion')
