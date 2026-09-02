"""add tipo, estado and approval traceability to indicadores

Revision ID: d8e4f1a2b3c5
Revises: c3f8a1d2e4b7
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d8e4f1a2b3c5"
down_revision: Union[str, Sequence[str], None] = "c3f8a1d2e4b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "indicadores" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("indicadores")}
    fks = {fk["name"] for fk in inspector.get_foreign_keys("indicadores")}
    indexes = {idx["name"] for idx in inspector.get_indexes("indicadores")}

    if "tipo_indicador" not in cols:
        op.add_column(
            "indicadores",
            sa.Column("tipo_indicador", sa.String(length=50), nullable=False, server_default="eficacia"),
        )
        op.alter_column("indicadores", "tipo_indicador", server_default=None)

    if "estado" not in cols:
        op.add_column(
            "indicadores",
            sa.Column("estado", sa.String(length=50), nullable=False, server_default="borrador"),
        )
        op.alter_column("indicadores", "estado", server_default=None)

    if "revisado_por" not in cols:
        op.add_column(
            "indicadores",
            sa.Column("revisado_por", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if "fecha_revision" not in cols:
        op.add_column("indicadores", sa.Column("fecha_revision", sa.DateTime(timezone=True), nullable=True))
    if "aprobado_por" not in cols:
        op.add_column(
            "indicadores",
            sa.Column("aprobado_por", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if "fecha_aprobacion" not in cols:
        op.add_column("indicadores", sa.Column("fecha_aprobacion", sa.DateTime(timezone=True), nullable=True))
    if "observacion_aprobacion" not in cols:
        op.add_column("indicadores", sa.Column("observacion_aprobacion", sa.Text(), nullable=True))

    if "fk_indicadores_revisado_por" not in fks:
        op.create_foreign_key(
            "fk_indicadores_revisado_por",
            "indicadores",
            "usuarios",
            ["revisado_por"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    if "fk_indicadores_aprobado_por" not in fks:
        op.create_foreign_key(
            "fk_indicadores_aprobado_por",
            "indicadores",
            "usuarios",
            ["aprobado_por"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    if "idx_indicadores_tipo" not in indexes:
        op.create_index("idx_indicadores_tipo", "indicadores", ["tipo_indicador"], unique=False)
    if "idx_indicadores_estado" not in indexes:
        op.create_index("idx_indicadores_estado", "indicadores", ["estado"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "indicadores" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("indicadores")}
    fks = {fk["name"] for fk in inspector.get_foreign_keys("indicadores")}
    indexes = {idx["name"] for idx in inspector.get_indexes("indicadores")}

    if "idx_indicadores_estado" in indexes:
        op.drop_index("idx_indicadores_estado", table_name="indicadores")
    if "idx_indicadores_tipo" in indexes:
        op.drop_index("idx_indicadores_tipo", table_name="indicadores")
    if "fk_indicadores_aprobado_por" in fks:
        op.drop_constraint("fk_indicadores_aprobado_por", "indicadores", type_="foreignkey")
    if "fk_indicadores_revisado_por" in fks:
        op.drop_constraint("fk_indicadores_revisado_por", "indicadores", type_="foreignkey")
    for col in (
        "observacion_aprobacion",
        "fecha_aprobacion",
        "aprobado_por",
        "fecha_revision",
        "revisado_por",
        "estado",
        "tipo_indicador",
    ):
        if col in cols:
            op.drop_column("indicadores", col)
