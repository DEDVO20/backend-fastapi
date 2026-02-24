"""certifiable competency-risk automation

Revision ID: a9c4f1b2d3e4
Revises: f50e73029ab7
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a9c4f1b2d3e4"
down_revision: Union[str, Sequence[str], None] = "f50e73029ab7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "etapa_competencias" not in inspector.get_table_names():
        op.create_table(
            "etapa_competencias",
            sa.Column("etapa_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("competencia_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("nivel_requerido", sa.String(length=50), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["etapa_id"], ["etapa_procesos.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["competencia_id"], ["competencias.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("etapa_id", "competencia_id", name="uq_etapa_competencias"),
        )
        op.alter_column("etapa_competencias", "activo", server_default=None)
        op.create_index("idx_etapa_competencias_etapa", "etapa_competencias", ["etapa_id"], unique=False)
        op.create_index("idx_etapa_competencias_competencia", "etapa_competencias", ["competencia_id"], unique=False)

    if "riesgo_competencias_criticas" not in inspector.get_table_names():
        op.create_table(
            "riesgo_competencias_criticas",
            sa.Column("riesgo_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("competencia_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("nivel_minimo", sa.String(length=50), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["riesgo_id"], ["riesgos.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["competencia_id"], ["competencias.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.alter_column("riesgo_competencias_criticas", "activo", server_default=None)
        op.create_index("idx_riesgo_comp_crit_riesgo", "riesgo_competencias_criticas", ["riesgo_id"], unique=False)
        op.create_index("idx_riesgo_comp_crit_competencia", "riesgo_competencias_criticas", ["competencia_id"], unique=False)
        op.create_index("idx_riesgo_comp_crit_nivel", "riesgo_competencias_criticas", ["nivel_minimo"], unique=False)

    riesgo_cols = {c["name"] for c in inspector.get_columns("riesgos")}
    if "nivel_residual" not in riesgo_cols:
        op.add_column("riesgos", sa.Column("nivel_residual", sa.Integer(), nullable=True))

    brecha_cols = {c["name"] for c in inspector.get_columns("brechas_competencia")}
    if "etapa_id" not in brecha_cols:
        op.add_column("brechas_competencia", sa.Column("etapa_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_brecha_etapa_id",
            "brechas_competencia",
            "etapa_procesos",
            ["etapa_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    if "riesgo_id" not in brecha_cols:
        op.add_column("brechas_competencia", sa.Column("riesgo_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_brecha_riesgo_id",
            "brechas_competencia",
            "riesgos",
            ["riesgo_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    if "nivel_riesgo" not in brecha_cols:
        op.add_column("brechas_competencia", sa.Column("nivel_riesgo", sa.String(length=50), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE brechas_competencia
            SET estado = CASE
                WHEN estado = 'pendiente' THEN 'abierta'
                WHEN estado = 'resuelta' THEN 'cerrada'
                ELSE estado
            END
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "brechas_competencia" in inspector.get_table_names():
        brecha_cols = {c["name"] for c in inspector.get_columns("brechas_competencia")}
        fk_names = {fk.get("name") for fk in inspector.get_foreign_keys("brechas_competencia")}

        if "nivel_riesgo" in brecha_cols:
            op.drop_column("brechas_competencia", "nivel_riesgo")
        if "fk_brecha_riesgo_id" in fk_names:
            op.drop_constraint("fk_brecha_riesgo_id", "brechas_competencia", type_="foreignkey")
        if "riesgo_id" in brecha_cols:
            op.drop_column("brechas_competencia", "riesgo_id")
        if "fk_brecha_etapa_id" in fk_names:
            op.drop_constraint("fk_brecha_etapa_id", "brechas_competencia", type_="foreignkey")
        if "etapa_id" in brecha_cols:
            op.drop_column("brechas_competencia", "etapa_id")

    riesgo_cols = {c["name"] for c in inspector.get_columns("riesgos")}
    if "nivel_residual" in riesgo_cols:
        op.drop_column("riesgos", "nivel_residual")

    if "riesgo_competencias_criticas" in inspector.get_table_names():
        op.drop_index("idx_riesgo_comp_crit_nivel", table_name="riesgo_competencias_criticas")
        op.drop_index("idx_riesgo_comp_crit_competencia", table_name="riesgo_competencias_criticas")
        op.drop_index("idx_riesgo_comp_crit_riesgo", table_name="riesgo_competencias_criticas")
        op.drop_table("riesgo_competencias_criticas")

    if "etapa_competencias" in inspector.get_table_names():
        op.drop_index("idx_etapa_competencias_competencia", table_name="etapa_competencias")
        op.drop_index("idx_etapa_competencias_etapa", table_name="etapa_competencias")
        op.drop_table("etapa_competencias")
