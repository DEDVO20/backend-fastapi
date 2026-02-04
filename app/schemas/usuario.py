"""
Schemas Pydantic para usuarios, áreas, roles y permisos
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Área Schemas
class AreaBase(BaseModel):
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=255)
    descripcion: Optional[str] = None


class AreaCreate(AreaBase):
    pass


class AreaUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = None

class UsuarioMinimo(BaseModel):
    id: UUID
    nombre: str
    primer_apellido: str
    correo_electronico: str
    
    model_config = ConfigDict(from_attributes=True)

class AsignacionResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    es_principal: bool
    usuario: UsuarioMinimo
    
    model_config = ConfigDict(from_attributes=True)

class AreaResponse(AreaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    asignaciones: List['AsignacionResponse'] = []
    
    model_config = ConfigDict(from_attributes=True)


# Permiso Schemas
class PermisoBase(BaseModel):
    nombre: str = Field(..., max_length=200)
    codigo: str = Field(..., max_length=200)
    descripcion: Optional[str] = None


class PermisoCreate(PermisoBase):
    pass


class PermisoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=200)
    codigo: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None


class PermisoResponse(PermisoBase):
    id: UUID
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# RolPermiso Schemas
class RolPermisoCreate(BaseModel):
    rol_id: UUID
    permiso_id: UUID


class RolPermisoResponse(BaseModel):
    id: UUID
    rol_id: UUID
    permiso_id: UUID
    permiso: Optional[PermisoResponse] = None
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Rol Schemas
class RolBase(BaseModel):
    nombre: str = Field(..., max_length=150)
    clave: str = Field(..., max_length=150)
    descripcion: Optional[str] = None


class RolCreate(RolBase):
    pass


class RolUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=150)
    clave: Optional[str] = Field(None, max_length=150)
    descripcion: Optional[str] = None


class RolResponse(RolBase):
    id: UUID
    creado_en: datetime
    permisos: List[RolPermisoResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# UsuarioRol Schemas (Moved up)
class UsuarioRolCreate(BaseModel):
    usuario_id: UUID
    rol_id: UUID


class UsuarioRolResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    rol_id: UUID
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Usuario Schemas
class UsuarioBase(BaseModel):
    documento: int
    nombre: str = Field(..., max_length=100)
    segundo_nombre: Optional[str] = Field(None, max_length=100)
    primer_apellido: str = Field(..., max_length=100)
    segundo_apellido: Optional[str] = Field(None, max_length=100)
    correo_electronico: EmailStr
    nombre_usuario: str = Field(..., max_length=150)
    area_id: Optional[UUID] = None
    activo: bool = True
    foto_url: Optional[str] = Field(None, max_length=500)


class UsuarioCreate(UsuarioBase):
    contrasena: str = Field(..., min_length=8)
    rol_ids: List[UUID] = []


class UsuarioUpdate(BaseModel):
    documento: Optional[int] = None
    nombre: Optional[str] = Field(None, max_length=100)
    segundo_nombre: Optional[str] = Field(None, max_length=100)
    primer_apellido: Optional[str] = Field(None, max_length=100)
    segundo_apellido: Optional[str] = Field(None, max_length=100)
    correo_electronico: Optional[EmailStr] = None
    nombre_usuario: Optional[str] = Field(None, max_length=150)
    area_id: Optional[UUID] = None
    activo: Optional[bool] = None
    foto_url: Optional[str] = Field(None, max_length=500)
    contrasena: Optional[str] = Field(None, min_length=8)
    rol_ids: Optional[List[UUID]] = None


class UsuarioResponse(UsuarioBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    permisos: List[str] = []
    roles: List[UsuarioRolResponse] = []
    nombre_completo: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UsuarioWithArea(UsuarioResponse):
    """Usuario con información del área"""
    area: Optional[AreaResponse] = None


# Login Schema
class LoginRequest(BaseModel):
    nombre_usuario: str
    contrasena: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


# Carga Masiva Schemas
class CargaMasivaErrorDetalle(BaseModel):
    """Detalle de un error en carga masiva"""
    fila: int
    campo: str
    valor: Optional[str] = None
    error: str


class CargaMasivaUsuarioExitoso(BaseModel):
    """Usuario creado exitosamente"""
    fila: int
    nombre_usuario: str
    nombre_completo: str
    correo_electronico: str


class CargaMasivaResultado(BaseModel):
    """Resultado de la carga masiva"""
    total_procesados: int
    exitosos: int
    errores: int
    detalles_exitosos: List[CargaMasivaUsuarioExitoso]
    detalles_errores: List[CargaMasivaErrorDetalle]
