"""
Schemas Pydantic para sistema (notificaciones, configuraciones)
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# Notificacion Schemas
class NotificacionBase(BaseModel):
    usuario_id: UUID
    titulo: str = Field(..., max_length=200)
    mensaje: str
    tipo: str = Field(..., max_length=50)
    leida: bool = False
    fecha_lectura: Optional[datetime] = None
    referencia_tipo: Optional[str] = Field(None, max_length=50)
    referencia_id: Optional[UUID] = None


class NotificacionCreate(NotificacionBase):
    pass


class NotificacionUpdate(BaseModel):
    leida: Optional[bool] = None
    fecha_lectura: Optional[datetime] = None


class NotificacionResponse(NotificacionBase):
    id: UUID
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Configuracion Schemas
class ConfiguracionBase(BaseModel):
    clave: str = Field(..., max_length=100)
    valor: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_dato: str = Field(default='string', max_length=50)
    categoria: Optional[str] = Field(None, max_length=100)
    activa: bool = True


class ConfiguracionCreate(ConfiguracionBase):
    pass


class ConfiguracionUpdate(BaseModel):
    valor: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_dato: Optional[str] = Field(None, max_length=50)
    categoria: Optional[str] = Field(None, max_length=100)
    activa: Optional[bool] = None


class ConfiguracionResponse(ConfiguracionBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Asignacion Schemas
from .usuario import UsuarioResponse, AreaResponse

class AsignacionCreate(BaseModel):
    area_id: UUID
    usuario_id: UUID
    es_principal: bool = False


class AsignacionResponse(BaseModel):
    id: UUID
    area_id: UUID
    usuario_id: UUID
    es_principal: bool
    creado_en: datetime
    
    # Datos anidados para facilitar el frontend
    area: Optional[AreaResponse] = None
    usuario: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)
