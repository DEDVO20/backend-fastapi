"""backfill nombre in riesgos

Revision ID: c3f8a1d2e4b7
Revises: b91f4a2d6c3e
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3f8a1d2e4b7"
down_revision: Union[str, Sequence[str], None] = "b91f4a2d6c3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE riesgos
            SET nombre = LEFT(
                COALESCE(NULLIF(BTRIM(descripcion), ''), codigo),
                200
            )
            WHERE nombre IS NULL OR BTRIM(nombre) = ''
            """
        )
    )


def downgrade() -> None:
    # No reversible de forma segura sin perder datos ingresados manualmente.
    pass
