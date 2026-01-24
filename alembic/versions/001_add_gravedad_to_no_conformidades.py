"""Agregar columna gravedad a no_conformidades

Revision ID: 001_add_gravedad
Revises: 
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_gravedad'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columna gravedad a no_conformidades
    op.add_column('no_conformidades', 
                  sa.Column('gravedad', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Eliminar columna gravedad de no_conformidades
    op.drop_column('no_conformidades', 'gravedad')
