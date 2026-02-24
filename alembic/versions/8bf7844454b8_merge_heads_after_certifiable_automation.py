"""merge heads after certifiable automation

Revision ID: 8bf7844454b8
Revises: 7c955ef9043f, a9c4f1b2d3e4
Create Date: 2026-02-23 20:06:52.729708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bf7844454b8'
down_revision: Union[str, Sequence[str], None] = ('7c955ef9043f', 'a9c4f1b2d3e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
