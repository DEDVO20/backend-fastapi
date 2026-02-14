"""enforce_programa_integrity_for_auditorias

Revision ID: 9c1f3a7b0e12
Revises: d69e42bdb645
Create Date: 2026-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = "9c1f3a7b0e12"
down_revision: Union[str, Sequence[str], None] = "d69e42bdb645"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Backfill para auditorías legacy sin programa_id:
    # 1) Busca un programa existente del mismo año.
    # 2) Si no existe, crea uno técnico en estado aprobado.
    # 3) Asigna programa_id por año de fecha_planificada/creado_en.
    years = conn.execute(
        sa.text(
            """
            SELECT DISTINCT EXTRACT(YEAR FROM COALESCE(fecha_planificada, creado_en, NOW()))::int AS anio
            FROM auditorias
            WHERE programa_id IS NULL
            """
        )
    ).fetchall()

    for row in years:
        anio = int(row.anio)
        programa_id = conn.execute(
            sa.text(
                """
                SELECT id
                FROM programa_auditorias
                WHERE anio = :anio
                ORDER BY creado_en ASC
                LIMIT 1
                """
            ),
            {"anio": anio},
        ).scalar()

        if not programa_id:
            programa_id = uuid.uuid4()
            conn.execute(
                sa.text(
                    """
                    INSERT INTO programa_auditorias (
                        id, anio, objetivo, estado, criterio_riesgo, aprobado_por, fecha_aprobacion, creado_en, actualizado_en
                    ) VALUES (
                        :id, :anio, :objetivo, :estado, :criterio_riesgo, NULL, NOW(), NOW(), NOW()
                    )
                    """
                ),
                {
                    "id": programa_id,
                    "anio": anio,
                    "objetivo": f"Programa migrado automáticamente para auditorías existentes del año {anio}",
                    "estado": "aprobado",
                    "criterio_riesgo": "Backfill técnico por migración de integridad referencial",
                },
            )

        conn.execute(
            sa.text(
                """
                UPDATE auditorias
                SET programa_id = :programa_id
                WHERE programa_id IS NULL
                  AND EXTRACT(YEAR FROM COALESCE(fecha_planificada, creado_en, NOW()))::int = :anio
                """
            ),
            {"programa_id": programa_id, "anio": anio},
        )

    remaining_nulls = conn.execute(
        sa.text("SELECT COUNT(*) FROM auditorias WHERE programa_id IS NULL")
    ).scalar()
    if remaining_nulls and remaining_nulls > 0:
        raise RuntimeError(
            "No se pudo completar el backfill de programa_id para todas las auditorías."
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
