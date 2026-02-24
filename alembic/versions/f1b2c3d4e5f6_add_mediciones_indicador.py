"""add mediciones_indicador table

Revision ID: f1b2c3d4e5f6
Revises: e7c1a4b5d9f2
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e7c1a4b5d9f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "mediciones_indicador" not in inspector.get_table_names():
        op.create_table(
            "mediciones_indicador",
            sa.Column("indicador_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("periodo", sa.String(length=20), nullable=False),
            sa.Column("valor", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("meta", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("cumple_meta", sa.Boolean(), nullable=True),
            sa.Column("observaciones", sa.Text(), nullable=True),
            sa.Column("registrado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["indicador_id"], ["indicadores.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["registrado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.alter_column("mediciones_indicador", "activo", server_default=None)
        op.create_index("idx_mediciones_indicador_id", "mediciones_indicador", ["indicador_id"], unique=False)
        op.create_index("idx_mediciones_indicador_periodo", "mediciones_indicador", ["periodo"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "mediciones_indicador" in inspector.get_table_names():
        op.drop_index("idx_mediciones_indicador_periodo", table_name="mediciones_indicador")
        op.drop_index("idx_mediciones_indicador_id", table_name="mediciones_indicador")
        op.drop_table("mediciones_indicador")
