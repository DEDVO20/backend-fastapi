"""enforce_programa_integrity_for_auditorias

Revision ID: 9c1f3a7b0e12
Revises: d69e42bdb645
Create Date: 2026-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c1f3a7b0e12"
down_revision: Union[str, Sequence[str], None] = "d69e42bdb645"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM auditorias
                WHERE programa_id IS NULL
            ) THEN
                RAISE EXCEPTION 'No se puede aplicar migración: existen auditorías sin programa_id';
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        DECLARE
            fk_name text;
        BEGIN
            SELECT tc.constraint_name INTO fk_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = 'auditorias'
              AND tc.constraint_type = 'FOREIGN KEY'
              AND kcu.column_name = 'programa_id'
            LIMIT 1;

            IF fk_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE auditorias DROP CONSTRAINT %I', fk_name);
            END IF;
        END $$;
        """
    )

    op.alter_column("auditorias", "programa_id", existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key(
        "auditorias_programa_id_fkey",
        "auditorias",
        "programa_auditorias",
        ["programa_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="RESTRICT",
    )
    op.create_index(
        "idx_auditorias_programa_estado",
        "auditorias",
        ["programa_id", "estado"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_auditorias_programa_estado", table_name="auditorias")
    op.drop_constraint("auditorias_programa_id_fkey", "auditorias", type_="foreignkey")
    op.create_foreign_key(
        "auditorias_programa_id_fkey",
        "auditorias",
        "programa_auditorias",
        ["programa_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.alter_column("auditorias", "programa_id", existing_type=sa.UUID(), nullable=True)
