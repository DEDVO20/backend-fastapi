"""enrich_etapas_proceso_iso9001

Revision ID: ef91c2b7a4d1
Revises: a3b7d9e1f2c4
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ef91c2b7a4d1'
down_revision: Union[str, Sequence[str], None] = 'a3b7d9e1f2c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('etapa_procesos', sa.Column('es_critica', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('etapa_procesos', sa.Column('tipo_etapa', sa.String(length=50), nullable=False, server_default='transformacion'))
    op.add_column('etapa_procesos', sa.Column('etapa_phva', sa.String(length=20), nullable=True))
    op.add_column('etapa_procesos', sa.Column('entradas', sa.Text(), nullable=True))
    op.add_column('etapa_procesos', sa.Column('salidas', sa.Text(), nullable=True))
    op.add_column('etapa_procesos', sa.Column('controles', sa.Text(), nullable=True))
    op.add_column('etapa_procesos', sa.Column('registros_requeridos', sa.Text(), nullable=True))

    op.alter_column('etapa_procesos', 'es_critica', server_default=None)
    op.alter_column('etapa_procesos', 'tipo_etapa', server_default=None)

    op.add_column('hallazgo_auditorias', sa.Column('etapa_proceso_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_hallazgo_auditorias_etapa_proceso_id',
        'hallazgo_auditorias',
        'etapa_procesos',
        ['etapa_proceso_id'],
        ['id'],
        onupdate='CASCADE',
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_hallazgo_auditorias_etapa_proceso_id', 'hallazgo_auditorias', type_='foreignkey')
    op.drop_column('hallazgo_auditorias', 'etapa_proceso_id')

    op.drop_column('etapa_procesos', 'registros_requeridos')
    op.drop_column('etapa_procesos', 'controles')
    op.drop_column('etapa_procesos', 'salidas')
    op.drop_column('etapa_procesos', 'entradas')
    op.drop_column('etapa_procesos', 'etapa_phva')
    op.drop_column('etapa_procesos', 'tipo_etapa')
    op.drop_column('etapa_procesos', 'es_critica')
