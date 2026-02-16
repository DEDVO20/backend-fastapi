"""add_capacitacion_scope_and_attendance_window

Revision ID: c2f7b8e4a1d9
Revises: b7d4c2a91f33
Create Date: 2026-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2f7b8e4a1d9"
down_revision: Union[str, Sequence[str], None] = "b7d4c2a91f33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("capacitaciones", sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=True))
    op.add_column("capacitaciones", sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True))
    op.add_column("capacitaciones", sa.Column("fecha_cierre_asistencia", sa.DateTime(timezone=True), nullable=True))
    op.add_column("capacitaciones", sa.Column("area_id", sa.UUID(), nullable=True))
    op.add_column(
        "capacitaciones",
        sa.Column("aplica_todas_areas", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_foreign_key(
        "capacitaciones_area_id_fkey",
        "capacitaciones",
        "areas",
        ["area_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.create_index("idx_capacitaciones_area_id", "capacitaciones", ["area_id"], unique=False)
    op.alter_column("capacitaciones", "aplica_todas_areas", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_capacitaciones_area_id", table_name="capacitaciones")
    op.drop_constraint("capacitaciones_area_id_fkey", "capacitaciones", type_="foreignkey")
    op.drop_column("capacitaciones", "aplica_todas_areas")
    op.drop_column("capacitaciones", "area_id")
    op.drop_column("capacitaciones", "fecha_cierre_asistencia")
    op.drop_column("capacitaciones", "fecha_fin")
    op.drop_column("capacitaciones", "fecha_inicio")
