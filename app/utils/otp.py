"""Generación y verificación de códigos OTP."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..config import settings


def generar_codigo_otp(longitud: int = 6) -> str:
    """Código numérico de `longitud` dígitos."""
    tope = 10 ** longitud
    return f"{secrets.randbelow(tope):0{longitud}d}"


def hash_otp(codigo: str, usuario_id: str) -> str:
    mensaje = f"{usuario_id}:{codigo.strip()}".encode("utf-8")
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        mensaje,
        hashlib.sha256,
    ).hexdigest()


def verificar_otp(codigo: str, usuario_id: str, otp_hash: Optional[str]) -> bool:
    if not otp_hash or not codigo:
        return False
    esperado = hash_otp(codigo, usuario_id)
    return hmac.compare_digest(esperado, otp_hash)


def otp_expira_en() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)


def otp_esta_expirado(expira_en: Optional[datetime]) -> bool:
    if expira_en is None:
        return True
    ahora = datetime.now(timezone.utc)
    if expira_en.tzinfo is None:
        expira_en = expira_en.replace(tzinfo=timezone.utc)
    return ahora >= expira_en


def enmascarar_correo(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, dominio = email.split("@", 1)
    visible = local[0] + "***" if local else "***"
    return f"{visible}@{dominio}"
