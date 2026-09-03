"""add otp login fields to usuarios

Revision ID: e9a1c3d5f7b8
Revises: d8e4f1a2b3c5
Create Date: 2026-09-03

Los usuarios existentes quedan con requiere_otp=false (admin y cuentas actuales
siguen entrando con usuario/contraseña). Las columnas OTP se usan solo en
cuentas nuevas.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9a1c3d5f7b8"
down_revision: Union[str, Sequence[str], None] = "d8e4f1a2b3c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "usuarios" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("usuarios")}

    if "requiere_otp" not in cols:
        op.add_column(
            "usuarios",
            sa.Column(
                "requiere_otp",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
    if "otp_codigo_hash" not in cols:
        op.add_column(
            "usuarios",
            sa.Column("otp_codigo_hash", sa.String(length=128), nullable=True),
        )
    if "otp_expira_en" not in cols:
        op.add_column(
            "usuarios",
            sa.Column("otp_expira_en", sa.DateTime(timezone=True), nullable=True),
        )
    if "otp_intentos" not in cols:
        op.add_column(
            "usuarios",
            sa.Column(
                "otp_intentos",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
    if "otp_enviado_en" not in cols:
        op.add_column(
            "usuarios",
            sa.Column("otp_enviado_en", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "usuarios" not in inspector.get_table_names():
        return

    cols = {c["name"] for c in inspector.get_columns("usuarios")}
    for nombre in (
        "otp_enviado_en",
        "otp_intentos",
        "otp_expira_en",
        "otp_codigo_hash",
        "requiere_otp",
    ):
        if nombre in cols:
            op.drop_column("usuarios", nombre)
