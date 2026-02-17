"""add_proceso_id_to_auditorias

Revision ID: 1fa89d2c6e10
Revises: f18a2c7d9b44
Create Date: 2026-02-17 13:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1fa89d2c6e10"
down_revision: Union[str, Sequence[str], None] = "f18a2c7d9b44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _fk_exists(inspector, table_name: str, fk_name: str) -> bool:
    return any(fk["name"] == fk_name for fk in inspector.get_foreign_keys(table_name))


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _column_exists(inspector, "auditorias", "proceso_id"):
        op.add_column("auditorias", sa.Column("proceso_id", sa.UUID(), nullable=True))

    inspector = sa.inspect(bind)
    if not _fk_exists(inspector, "auditorias", "auditorias_proceso_id_fkey"):
        op.create_foreign_key(
            "auditorias_proceso_id_fkey",
            "auditorias",
            "procesos",
            ["proceso_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )

    inspector = sa.inspect(bind)
    if not _index_exists(inspector, "auditorias", "idx_auditorias_proceso_id"):
        op.create_index("idx_auditorias_proceso_id", "auditorias", ["proceso_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _index_exists(inspector, "auditorias", "idx_auditorias_proceso_id"):
        op.drop_index("idx_auditorias_proceso_id", table_name="auditorias")

    inspector = sa.inspect(bind)
    if _fk_exists(inspector, "auditorias", "auditorias_proceso_id_fkey"):
        op.drop_constraint("auditorias_proceso_id_fkey", "auditorias", type_="foreignkey")

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "auditorias", "proceso_id"):
        op.drop_column("auditorias", "proceso_id")
