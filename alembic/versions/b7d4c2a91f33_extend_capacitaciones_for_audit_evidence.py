"""extend_capacitaciones_for_audit_evidence

Revision ID: b7d4c2a91f33
Revises: 9c1f3a7b0e12
Create Date: 2026-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7d4c2a91f33"
down_revision: Union[str, Sequence[str], None] = "9c1f3a7b0e12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("capacitaciones", sa.Column("proceso_id", sa.UUID(), nullable=True))
    op.add_column("capacitaciones", sa.Column("relacionada_con_hallazgo_id", sa.UUID(), nullable=True))
    op.add_column("capacitaciones", sa.Column("relacionada_con_riesgo_id", sa.UUID(), nullable=True))
    op.add_column("capacitaciones", sa.Column("archivo_evidencia", sa.Text(), nullable=True))

    op.create_foreign_key(
        "capacitaciones_proceso_id_fkey",
        "capacitaciones",
        "procesos",
        ["proceso_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "capacitaciones_hallazgo_id_fkey",
        "capacitaciones",
        "hallazgo_auditorias",
        ["relacionada_con_hallazgo_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "capacitaciones_riesgo_id_fkey",
        "capacitaciones",
        "riesgos",
        ["relacionada_con_riesgo_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )

    op.add_column("asistencia_capacitaciones", sa.Column("fecha_asistencia", sa.DateTime(timezone=True), nullable=True))
    op.add_column("asistencia_capacitaciones", sa.Column("evaluacion_aprobada", sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("asistencia_capacitaciones", "evaluacion_aprobada")
    op.drop_column("asistencia_capacitaciones", "fecha_asistencia")

    op.drop_constraint("capacitaciones_riesgo_id_fkey", "capacitaciones", type_="foreignkey")
    op.drop_constraint("capacitaciones_hallazgo_id_fkey", "capacitaciones", type_="foreignkey")
    op.drop_constraint("capacitaciones_proceso_id_fkey", "capacitaciones", type_="foreignkey")

    op.drop_column("capacitaciones", "archivo_evidencia")
    op.drop_column("capacitaciones", "relacionada_con_riesgo_id")
    op.drop_column("capacitaciones", "relacionada_con_hallazgo_id")
    op.drop_column("capacitaciones", "proceso_id")
