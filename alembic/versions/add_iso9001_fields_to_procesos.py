"""add_iso9001_fields_to_procesos

Revision ID: add_iso9001_fields
Revises: 960576ac6530
Create Date: 2026-02-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_iso9001_fields'
down_revision = '960576ac6530'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos ISO 9001 a la tabla procesos
    op.add_column('procesos', sa.Column('entradas', sa.Text(), nullable=True))
    op.add_column('procesos', sa.Column('salidas', sa.Text(), nullable=True))
    op.add_column('procesos', sa.Column('recursos_necesarios', sa.Text(), nullable=True))
    op.add_column('procesos', sa.Column('criterios_desempeno', sa.Text(), nullable=True))
    op.add_column('procesos', sa.Column('riesgos_oportunidades', sa.Text(), nullable=True))
    
    # Agregar campos ISO 9001 a la tabla etapa_procesos
    op.add_column('etapa_procesos', sa.Column('criterios_aceptacion', sa.Text(), nullable=True))
    op.add_column('etapa_procesos', sa.Column('documentos_requeridos', sa.Text(), nullable=True))


def downgrade():
    # Eliminar campos de etapa_procesos
    op.drop_column('etapa_procesos', 'documentos_requeridos')
    op.drop_column('etapa_procesos', 'criterios_aceptacion')
    
    # Eliminar campos de procesos
    op.drop_column('procesos', 'riesgos_oportunidades')
    op.drop_column('procesos', 'criterios_desempeno')
    op.drop_column('procesos', 'recursos_necesarios')
    op.drop_column('procesos', 'salidas')
    op.drop_column('procesos', 'entradas')
