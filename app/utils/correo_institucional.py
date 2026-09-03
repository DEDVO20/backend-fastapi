"""Validación de correos institucionales para usuarios nuevos."""
from typing import List

from ..config import settings


def dominios_institucionales() -> List[str]:
    """Dominios permitidos para cuentas nuevas (OTP)."""
    return [
        dominio.strip().lower().lstrip("@")
        for dominio in settings.CORREOS_INSTITUCIONALES.split(",")
        if dominio.strip()
    ]


def es_correo_institucional(email: str) -> bool:
    if not email or "@" not in str(email):
        return False
    dominio = str(email).rsplit("@", 1)[-1].strip().lower()
    return dominio in set(dominios_institucionales())


def mensaje_correo_institucional() -> str:
    lista = ", ".join(f"@{dominio}" for dominio in dominios_institucionales())
    return (
        "Los usuarios nuevos deben usar un correo permitido "
        f"({lista})."
    )
