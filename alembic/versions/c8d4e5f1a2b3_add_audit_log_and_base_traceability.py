"""add audit_log table and base traceability columns

Revision ID: c8d4e5f1a2b3
Revises: f4a2b1c9d8e7
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c8d4e5f1a2b3"
down_revision: Union[str, Sequence[str], None] = "f4a2b1c9d8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_SKIP_TABLES = {"alembic_version", "audit_log"}


def _column_names(bind, table_name: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # F0.2: tabla de auditoría
    if "audit_log" not in inspector.get_table_names():
        op.create_table(
            "audit_log",
            sa.Column("tabla", sa.String(length=100), nullable=False),
            sa.Column("registro_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("accion", sa.String(length=20), nullable=False),
            sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("cambios_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_audit_log_tabla", "audit_log", ["tabla"], unique=False)
        op.create_index("idx_audit_log_registro_id", "audit_log", ["registro_id"], unique=False)
        op.create_index("idx_audit_log_fecha", "audit_log", ["fecha"], unique=False)

    # F0.1: agregar columnas heredadas de BaseModel donde faltan
    for table_name in inspector.get_table_names():
        if table_name in _SKIP_TABLES:
            continue

        cols = _column_names(bind, table_name)

        if "activo" not in cols:
            op.add_column(
                table_name,
                sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            )
            op.alter_column(table_name, "activo", server_default=None)

        if "creado_por" not in cols:
            op.add_column(
                table_name,
                sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                f"fk_{table_name}_creado_por_usuarios",
                table_name,
                "usuarios",
                ["creado_por"],
                ["id"],
                onupdate="CASCADE",
                ondelete="SET NULL",
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Downgrade conservador: se elimina sólo audit_log para no borrar
    # columnas preexistentes en tablas históricas.
    if "audit_log" in inspector.get_table_names():
        op.drop_index("idx_audit_log_fecha", table_name="audit_log")
        op.drop_index("idx_audit_log_registro_id", table_name="audit_log")
        op.drop_index("idx_audit_log_tabla", table_name="audit_log")
        op.drop_table("audit_log")
