"""
Schemas para autenticación
"""
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request para login"""
    nombre_usuario: str = Field(..., description="Nombre de usuario, correo o documento")
    password: str = Field(..., min_length=6, description="Contraseña")


class VerificarOtpRequest(BaseModel):
    otp_token: str
    codigo: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ReenviarOtpRequest(BaseModel):
    otp_token: str


class PoliticaAccesoResponse(BaseModel):
    dominios_institucionales: list[str]
    otp_expira_minutos: int


class TokenResponse(BaseModel):
    """Response con token de acceso"""
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    usuario: dict = Field(..., description="Datos básicos del usuario")
    requiere_otp: bool = False


class LoginResponse(BaseModel):
    """Login directo o desafío OTP para usuarios nuevos."""
    requiere_otp: bool = False
    access_token: Optional[str] = None
    token_type: str = "bearer"
    usuario: Optional[dict] = None
    otp_token: Optional[str] = None
    mensaje: Optional[str] = None
    correo_enmascarado: Optional[str] = None


class UsuarioAuth(BaseModel):
    """Datos del usuario para retornar en auth"""
    id: str
    nombre_usuario: str
    email: str
    nombre_completo: str
    cargo: str = None
    activo: bool
