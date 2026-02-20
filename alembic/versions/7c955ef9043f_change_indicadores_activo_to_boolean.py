"""change_indicadores_activo_to_boolean

Revision ID: 7c955ef9043f
Revises: f50e73029ab7
Create Date: 2026-02-19 19:57:52.212024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c955ef9043f'
down_revision: Union[str, Sequence[str], None] = 'f50e73029ab7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"]: c for c in inspector.get_columns("indicadores")}
    activo_col = cols.get("activo")

    if activo_col is None:
        return

    if not isinstance(activo_col["type"], sa.Boolean):
        # Cast explícito para PostgreSQL: 0 -> false, distinto de 0 -> true.
        op.execute(
            sa.text(
                """
                ALTER TABLE indicadores
                ALTER COLUMN activo TYPE BOOLEAN
                USING (activo <> 0)
                """
            )
        )
        op.alter_column("indicadores", "activo", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"]: c for c in inspector.get_columns("indicadores")}
    activo_col = cols.get("activo")

    if activo_col is None:
        return

    if not isinstance(activo_col["type"], sa.INTEGER):
        op.execute(
            sa.text(
                """
                ALTER TABLE indicadores
                ALTER COLUMN activo TYPE INTEGER
                USING (CASE WHEN activo THEN 1 ELSE 0 END)
                """
            )
        )
        op.alter_column("indicadores", "activo", nullable=False)
