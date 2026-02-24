"""add document request fields to tickets

Revision ID: f4a2b1c9d8e7
Revises: ef91c2b7a4d1
Create Date: 2026-02-19 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a2b1c9d8e7'
down_revision: Union[str, Sequence[str], None] = 'ef91c2b7a4d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tickets", sa.Column("documento_publico_id", sa.UUID(), nullable=True))
    op.add_column("tickets", sa.Column("archivo_adjunto_url", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_tickets_documento_publico",
        "tickets",
        "documentos",
        ["documento_publico_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_tickets_documento_publico", "tickets", type_="foreignkey")
    op.drop_column("tickets", "archivo_adjunto_url")
    op.drop_column("tickets", "documento_publico_id")
