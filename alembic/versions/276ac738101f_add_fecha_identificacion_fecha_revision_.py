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
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
