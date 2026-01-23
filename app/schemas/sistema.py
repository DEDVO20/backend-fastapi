"""
Schemas Pydantic para sistema (tickets, notificaciones)
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# Ticket Schemas
class TicketBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    titulo: str = Field(..., max_length=200)
    descripcion: str
    categoria: str = Field(..., max_length=100)
    prioridad: str = Field(default='media', max_length=50)
    estado: str = Field(default='abierto', max_length=50)
    solicitante_id: Optional[UUID] = None
    asignado_a: Optional[UUID] = None
    fecha_limite: Optional[datetime] = None
    fecha_resolucion: Optional[datetime] = None
    solucion: Optional[str] = None
    tiempo_resolucion: Optional[int] = None
    satisfaccion_cliente: Optional[int] = Field(None, ge=1, le=5)


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    categoria: Optional[str] = Field(None, max_length=100)
    prioridad: Optional[str] = Field(None, max_length=50)
    estado: Optional[str] = Field(None, max_length=50)
    asignado_a: Optional[UUID] = None
    fecha_limite: Optional[datetime] = None
    fecha_resolucion: Optional[datetime] = None
    solucion: Optional[str] = None
    tiempo_resolucion: Optional[int] = None
    satisfaccion_cliente: Optional[int] = Field(None, ge=1, le=5)


class TicketResponse(TicketBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


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
