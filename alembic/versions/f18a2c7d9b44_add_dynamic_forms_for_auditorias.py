"""add_dynamic_forms_for_auditorias

Revision ID: f18a2c7d9b44
Revises: c2f7b8e4a1d9
Create Date: 2026-02-16 18:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f18a2c7d9b44"
down_revision: Union[str, Sequence[str], None] = "c2f7b8e4a1d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _fk_exists(inspector, table_name: str, fk_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(fk["name"] == fk_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "formularios_dinamicos"):
        op.create_table(
            "formularios_dinamicos",
            sa.Column("codigo", sa.String(length=100), nullable=False),
            sa.Column("nombre", sa.String(length=200), nullable=False),
            sa.Column("descripcion", sa.Text(), nullable=True),
            sa.Column("modulo", sa.String(length=50), nullable=False, server_default="general"),
            sa.Column("entidad_tipo", sa.String(length=50), nullable=False, server_default="general"),
            sa.Column("proceso_id", sa.UUID(), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["proceso_id"], ["procesos.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("codigo"),
        )

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "formularios_dinamicos"):
        if not _index_exists(inspector, "formularios_dinamicos", "formularios_dinamicos_codigo_idx"):
            op.create_index("formularios_dinamicos_codigo_idx", "formularios_dinamicos", ["codigo"], unique=False)
        if not _index_exists(inspector, "formularios_dinamicos", "formularios_dinamicos_modulo_idx"):
            op.create_index("formularios_dinamicos_modulo_idx", "formularios_dinamicos", ["modulo"], unique=False)
        if not _index_exists(inspector, "formularios_dinamicos", "formularios_dinamicos_entidad_tipo_idx"):
            op.create_index("formularios_dinamicos_entidad_tipo_idx", "formularios_dinamicos", ["entidad_tipo"], unique=False)

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "campo_formularios") and not _column_exists(inspector, "campo_formularios", "formulario_id"):
        op.add_column("campo_formularios", sa.Column("formulario_id", sa.UUID(), nullable=True))

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "campo_formularios"):
        if not _fk_exists(inspector, "campo_formularios", "campo_formularios_formulario_id_fkey"):
            op.create_foreign_key(
                "campo_formularios_formulario_id_fkey",
                "campo_formularios",
                "formularios_dinamicos",
                ["formulario_id"],
                ["id"],
                onupdate="CASCADE",
                ondelete="CASCADE",
            )
        if not _index_exists(inspector, "campo_formularios", "idx_campo_formularios_formulario_id"):
            op.create_index("idx_campo_formularios_formulario_id", "campo_formularios", ["formulario_id"], unique=False)

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "respuesta_formularios") and not _column_exists(inspector, "respuesta_formularios", "auditoria_id"):
        op.add_column("respuesta_formularios", sa.Column("auditoria_id", sa.UUID(), nullable=True))

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "respuesta_formularios"):
        if not _fk_exists(inspector, "respuesta_formularios", "respuesta_formularios_auditoria_id_fkey"):
            op.create_foreign_key(
                "respuesta_formularios_auditoria_id_fkey",
                "respuesta_formularios",
                "auditorias",
                ["auditoria_id"],
                ["id"],
                onupdate="CASCADE",
                ondelete="CASCADE",
            )
        if not _index_exists(inspector, "respuesta_formularios", "idx_respuesta_formularios_auditoria_id"):
            op.create_index("idx_respuesta_formularios_auditoria_id", "respuesta_formularios", ["auditoria_id"], unique=False)

        instancia_columns = {col["name"]: col for col in inspector.get_columns("respuesta_formularios")}
        instancia_col = instancia_columns.get("instancia_proceso_id")
        if instancia_col and not instancia_col.get("nullable", False):
            op.alter_column("respuesta_formularios", "instancia_proceso_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "respuesta_formularios"):
        instancia_columns = {col["name"]: col for col in inspector.get_columns("respuesta_formularios")}
        instancia_col = instancia_columns.get("instancia_proceso_id")
        if instancia_col and instancia_col.get("nullable", True):
            op.alter_column("respuesta_formularios", "instancia_proceso_id", existing_type=sa.UUID(), nullable=False)

        if _index_exists(inspector, "respuesta_formularios", "idx_respuesta_formularios_auditoria_id"):
            op.drop_index("idx_respuesta_formularios_auditoria_id", table_name="respuesta_formularios")
        if _fk_exists(inspector, "respuesta_formularios", "respuesta_formularios_auditoria_id_fkey"):
            op.drop_constraint("respuesta_formularios_auditoria_id_fkey", "respuesta_formularios", type_="foreignkey")
        if _column_exists(inspector, "respuesta_formularios", "auditoria_id"):
            op.drop_column("respuesta_formularios", "auditoria_id")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "campo_formularios"):
        if _index_exists(inspector, "campo_formularios", "idx_campo_formularios_formulario_id"):
            op.drop_index("idx_campo_formularios_formulario_id", table_name="campo_formularios")
        if _fk_exists(inspector, "campo_formularios", "campo_formularios_formulario_id_fkey"):
            op.drop_constraint("campo_formularios_formulario_id_fkey", "campo_formularios", type_="foreignkey")
        if _column_exists(inspector, "campo_formularios", "formulario_id"):
            op.drop_column("campo_formularios", "formulario_id")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "formularios_dinamicos"):
        if _index_exists(inspector, "formularios_dinamicos", "formularios_dinamicos_entidad_tipo_idx"):
            op.drop_index("formularios_dinamicos_entidad_tipo_idx", table_name="formularios_dinamicos")
        if _index_exists(inspector, "formularios_dinamicos", "formularios_dinamicos_modulo_idx"):
            op.drop_index("formularios_dinamicos_modulo_idx", table_name="formularios_dinamicos")
        if _index_exists(inspector, "formularios_dinamicos", "formularios_dinamicos_codigo_idx"):
            op.drop_index("formularios_dinamicos_codigo_idx", table_name="formularios_dinamicos")
        op.drop_table("formularios_dinamicos")
