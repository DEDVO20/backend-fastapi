"""add brechas_competencia table

Revision ID: e7c1a4b5d9f2
Revises: d2a9f3c4b6e1
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e7c1a4b5d9f2"
down_revision: Union[str, Sequence[str], None] = "d2a9f3c4b6e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "brechas_competencia" not in inspector.get_table_names():
        op.create_table(
            "brechas_competencia",
            sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("competencia_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("nivel_requerido", sa.String(length=50), nullable=False),
            sa.Column("nivel_actual", sa.String(length=50), nullable=False),
            sa.Column("estado", sa.String(length=50), nullable=False, server_default="pendiente"),
            sa.Column("capacitacion_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("fecha_deteccion", sa.DateTime(timezone=True), nullable=False),
            sa.Column("fecha_resolucion", sa.DateTime(timezone=True), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["competencia_id"], ["competencias.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["capacitacion_id"], ["capacitaciones.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.alter_column("brechas_competencia", "estado", server_default=None)
        op.alter_column("brechas_competencia", "activo", server_default=None)
        op.create_index("idx_brechas_competencia_usuario", "brechas_competencia", ["usuario_id"], unique=False)
        op.create_index("idx_brechas_competencia_competencia", "brechas_competencia", ["competencia_id"], unique=False)
        op.create_index("idx_brechas_competencia_estado", "brechas_competencia", ["estado"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "brechas_competencia" in inspector.get_table_names():
        op.drop_index("idx_brechas_competencia_estado", table_name="brechas_competencia")
        op.drop_index("idx_brechas_competencia_competencia", table_name="brechas_competencia")
        op.drop_index("idx_brechas_competencia_usuario", table_name="brechas_competencia")
        op.drop_table("brechas_competencia")
