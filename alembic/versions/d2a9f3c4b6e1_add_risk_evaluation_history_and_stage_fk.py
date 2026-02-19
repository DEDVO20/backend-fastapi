"""add risk evaluation history and etapa_proceso_id in riesgos

Revision ID: d2a9f3c4b6e1
Revises: c8d4e5f1a2b3
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d2a9f3c4b6e1"
down_revision: Union[str, Sequence[str], None] = "c8d4e5f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    riesgo_cols = {c["name"] for c in inspector.get_columns("riesgos")}
    if "etapa_proceso_id" not in riesgo_cols:
        op.add_column("riesgos", sa.Column("etapa_proceso_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_riesgos_etapa_proceso_id",
            "riesgos",
            "etapa_procesos",
            ["etapa_proceso_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
        op.create_index("riesgos_etapa_proceso_id", "riesgos", ["etapa_proceso_id"], unique=False)

    if "evaluacion_riesgo_historial" not in inspector.get_table_names():
        op.create_table(
            "evaluacion_riesgo_historial",
            sa.Column("riesgo_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("probabilidad_anterior", sa.Integer(), nullable=True),
            sa.Column("impacto_anterior", sa.Integer(), nullable=True),
            sa.Column("nivel_anterior", sa.String(length=50), nullable=True),
            sa.Column("probabilidad_nueva", sa.Integer(), nullable=False),
            sa.Column("impacto_nueva", sa.Integer(), nullable=False),
            sa.Column("nivel_nuevo", sa.String(length=50), nullable=False),
            sa.Column("justificacion", sa.Text(), nullable=True),
            sa.Column("evaluado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("fecha_evaluacion", sa.DateTime(timezone=True), nullable=False),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["evaluado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["riesgo_id"], ["riesgos.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.alter_column("evaluacion_riesgo_historial", "activo", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "evaluacion_riesgo_historial" in inspector.get_table_names():
        op.drop_table("evaluacion_riesgo_historial")

    riesgo_cols = {c["name"] for c in inspector.get_columns("riesgos")}
    if "etapa_proceso_id" in riesgo_cols:
        indexes = {idx.get("name") for idx in inspector.get_indexes("riesgos")}
        if "riesgos_etapa_proceso_id" in indexes:
            op.drop_index("riesgos_etapa_proceso_id", table_name="riesgos")

        fks = {fk.get("name") for fk in inspector.get_foreign_keys("riesgos")}
        if "fk_riesgos_etapa_proceso_id" in fks:
            op.drop_constraint("fk_riesgos_etapa_proceso_id", "riesgos", type_="foreignkey")

        op.drop_column("riesgos", "etapa_proceso_id")
