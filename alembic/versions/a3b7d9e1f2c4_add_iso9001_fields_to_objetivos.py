"""Add ISO 9001 fields to objetivos_calidad

Revision ID: a3b7d9e1f2c4
Revises: 1fa89d2c6e10
Create Date: 2026-02-17

ISO 9001:2015 Cláusula 6.2 - Campos adicionales para objetivos de calidad:
- meta: descripción de la meta medible
- indicador: cómo se evaluarán los resultados
- valor_meta: valor numérico objetivo
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b7d9e1f2c4'
down_revision: Union[str, Sequence[str], None] = '1fa89d2c6e10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('objetivos_calidad', sa.Column('meta', sa.Text(), nullable=True))
    op.add_column('objetivos_calidad', sa.Column('indicador', sa.String(255), nullable=True))
    op.add_column('objetivos_calidad', sa.Column('valor_meta', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('objetivos_calidad', 'valor_meta')
    op.drop_column('objetivos_calidad', 'indicador')
    op.drop_column('objetivos_calidad', 'meta')
