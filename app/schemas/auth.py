"""
Schemas para autenticación
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request para login"""
    nombre_usuario: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., min_length=6, description="Contraseña")


class TokenResponse(BaseModel):
    """Response con token de acceso"""
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    usuario: dict = Field(..., description="Datos básicos del usuario")


class UsuarioAuth(BaseModel):
    """Datos del usuario para retornar en auth"""
    id: str
    nombre_usuario: str
    email: str
    nombre_completo: str
    cargo: str = None
    activo: bool
