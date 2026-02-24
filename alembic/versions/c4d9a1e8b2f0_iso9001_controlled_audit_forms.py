"""iso9001 controlled audit forms

Revision ID: c4d9a1e8b2f0
Revises: 8bf7844454b8
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c4d9a1e8b2f0"
down_revision: Union[str, Sequence[str], None] = "8bf7844454b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    formularios_cols = {c["name"] for c in inspector.get_columns("formularios_dinamicos")}
    if "estado_workflow" not in formularios_cols:
        op.add_column("formularios_dinamicos", sa.Column("estado_workflow", sa.String(length=30), nullable=False, server_default="borrador"))
        op.alter_column("formularios_dinamicos", "estado_workflow", server_default=None)
    if "vigente_desde" not in formularios_cols:
        op.add_column("formularios_dinamicos", sa.Column("vigente_desde", sa.DateTime(timezone=True), nullable=True))
    if "vigente_hasta" not in formularios_cols:
        op.add_column("formularios_dinamicos", sa.Column("vigente_hasta", sa.DateTime(timezone=True), nullable=True))
    if "aprobado_por" not in formularios_cols:
        op.add_column("formularios_dinamicos", sa.Column("aprobado_por", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_formularios_aprobado_por",
            "formularios_dinamicos",
            "usuarios",
            ["aprobado_por"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    if "fecha_aprobacion" not in formularios_cols:
        op.add_column("formularios_dinamicos", sa.Column("fecha_aprobacion", sa.DateTime(timezone=True), nullable=True))
    if "parent_formulario_id" not in formularios_cols:
        op.add_column("formularios_dinamicos", sa.Column("parent_formulario_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_formularios_parent",
            "formularios_dinamicos",
            "formularios_dinamicos",
            ["parent_formulario_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )

    campos_cols = {c["name"] for c in inspector.get_columns("campo_formularios")}
    if "seccion_iso" not in campos_cols:
        op.add_column("campo_formularios", sa.Column("seccion_iso", sa.String(length=100), nullable=True))
    if "clausula_iso" not in campos_cols:
        op.add_column("campo_formularios", sa.Column("clausula_iso", sa.String(length=50), nullable=True))
    if "subclausula_iso" not in campos_cols:
        op.add_column("campo_formularios", sa.Column("subclausula_iso", sa.String(length=50), nullable=True))
    if "evidencia_requerida" not in campos_cols:
        op.add_column("campo_formularios", sa.Column("evidencia_requerida", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        op.alter_column("campo_formularios", "evidencia_requerida", server_default=None)

    respuestas_cols = {c["name"] for c in inspector.get_columns("respuesta_formularios")}
    if "evidencia_hash" not in respuestas_cols:
        op.add_column("respuesta_formularios", sa.Column("evidencia_hash", sa.String(length=128), nullable=True))
    if "evidencia_fecha" not in respuestas_cols:
        op.add_column("respuesta_formularios", sa.Column("evidencia_fecha", sa.DateTime(timezone=True), nullable=True))
    if "evidencia_usuario_id" not in respuestas_cols:
        op.add_column("respuesta_formularios", sa.Column("evidencia_usuario_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_respuesta_evidencia_usuario",
            "respuesta_formularios",
            "usuarios",
            ["evidencia_usuario_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )

    auditorias_cols = {c["name"] for c in inspector.get_columns("auditorias")}
    if "formulario_checklist_id" not in auditorias_cols:
        op.add_column("auditorias", sa.Column("formulario_checklist_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_auditorias_formulario_checklist",
            "auditorias",
            "formularios_dinamicos",
            ["formulario_checklist_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    if "formulario_checklist_version" not in auditorias_cols:
        op.add_column("auditorias", sa.Column("formulario_checklist_version", sa.Integer(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    auditorias_cols = {c["name"] for c in inspector.get_columns("auditorias")}
    auditorias_fks = {fk.get("name") for fk in inspector.get_foreign_keys("auditorias")}
    if "formulario_checklist_version" in auditorias_cols:
        op.drop_column("auditorias", "formulario_checklist_version")
    if "fk_auditorias_formulario_checklist" in auditorias_fks:
        op.drop_constraint("fk_auditorias_formulario_checklist", "auditorias", type_="foreignkey")
    if "formulario_checklist_id" in auditorias_cols:
        op.drop_column("auditorias", "formulario_checklist_id")

    respuestas_cols = {c["name"] for c in inspector.get_columns("respuesta_formularios")}
    respuestas_fks = {fk.get("name") for fk in inspector.get_foreign_keys("respuesta_formularios")}
    if "fk_respuesta_evidencia_usuario" in respuestas_fks:
        op.drop_constraint("fk_respuesta_evidencia_usuario", "respuesta_formularios", type_="foreignkey")
    if "evidencia_usuario_id" in respuestas_cols:
        op.drop_column("respuesta_formularios", "evidencia_usuario_id")
    if "evidencia_fecha" in respuestas_cols:
        op.drop_column("respuesta_formularios", "evidencia_fecha")
    if "evidencia_hash" in respuestas_cols:
        op.drop_column("respuesta_formularios", "evidencia_hash")

    campos_cols = {c["name"] for c in inspector.get_columns("campo_formularios")}
    if "evidencia_requerida" in campos_cols:
        op.drop_column("campo_formularios", "evidencia_requerida")
    if "subclausula_iso" in campos_cols:
        op.drop_column("campo_formularios", "subclausula_iso")
    if "clausula_iso" in campos_cols:
        op.drop_column("campo_formularios", "clausula_iso")
    if "seccion_iso" in campos_cols:
        op.drop_column("campo_formularios", "seccion_iso")

    formularios_cols = {c["name"] for c in inspector.get_columns("formularios_dinamicos")}
    formularios_fks = {fk.get("name") for fk in inspector.get_foreign_keys("formularios_dinamicos")}
    if "fk_formularios_parent" in formularios_fks:
        op.drop_constraint("fk_formularios_parent", "formularios_dinamicos", type_="foreignkey")
    if "parent_formulario_id" in formularios_cols:
        op.drop_column("formularios_dinamicos", "parent_formulario_id")
    if "fecha_aprobacion" in formularios_cols:
        op.drop_column("formularios_dinamicos", "fecha_aprobacion")
    if "fk_formularios_aprobado_por" in formularios_fks:
        op.drop_constraint("fk_formularios_aprobado_por", "formularios_dinamicos", type_="foreignkey")
    if "aprobado_por" in formularios_cols:
        op.drop_column("formularios_dinamicos", "aprobado_por")
    if "vigente_hasta" in formularios_cols:
        op.drop_column("formularios_dinamicos", "vigente_hasta")
    if "vigente_desde" in formularios_cols:
        op.drop_column("formularios_dinamicos", "vigente_desde")
    if "estado_workflow" in formularios_cols:
        op.drop_column("formularios_dinamicos", "estado_workflow")
