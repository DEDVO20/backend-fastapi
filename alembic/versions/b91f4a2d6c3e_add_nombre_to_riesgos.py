"""add nombre to riesgos

Revision ID: b91f4a2d6c3e
Revises: c4d9a1e8b2f0
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b91f4a2d6c3e"
down_revision: Union[str, Sequence[str], None] = "c4d9a1e8b2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    riesgo_cols = {c["name"] for c in inspector.get_columns("riesgos")}
    if "nombre" not in riesgo_cols:
        op.add_column("riesgos", sa.Column("nombre", sa.String(length=200), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    riesgo_cols = {c["name"] for c in inspector.get_columns("riesgos")}
    if "nombre" in riesgo_cols:
        op.drop_column("riesgos", "nombre")
