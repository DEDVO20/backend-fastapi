"""
Schemas Pydantic para sistema (notificaciones, configuraciones)
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
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


# Formularios dinámicos
class FormularioDinamicoBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    modulo: str = Field(default="general", max_length=50)
    entidad_tipo: str = Field(default="general", max_length=50)
    proceso_id: Optional[UUID] = None
    activo: bool = True
    version: int = 1


class FormularioDinamicoCreate(FormularioDinamicoBase):
    pass


class FormularioDinamicoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    modulo: Optional[str] = Field(None, max_length=50)
    entidad_tipo: Optional[str] = Field(None, max_length=50)
    proceso_id: Optional[UUID] = None
    activo: Optional[bool] = None
    version: Optional[int] = None


class FormularioDinamicoResponse(FormularioDinamicoBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class CampoFormularioBase(BaseModel):
    formulario_id: Optional[UUID] = None
    proceso_id: Optional[UUID] = None
    nombre: str = Field(..., max_length=200)
    etiqueta: str = Field(..., max_length=200)
    tipo_campo: str = Field(..., max_length=50)
    requerido: bool = False
    opciones: Optional[Any] = None
    orden: int = 1
    activo: bool = True
    validaciones: Optional[Any] = None


class CampoFormularioCreate(CampoFormularioBase):
    pass


class CampoFormularioUpdate(BaseModel):
    formulario_id: Optional[UUID] = None
    proceso_id: Optional[UUID] = None
    nombre: Optional[str] = Field(None, max_length=200)
    etiqueta: Optional[str] = Field(None, max_length=200)
    tipo_campo: Optional[str] = Field(None, max_length=50)
    requerido: Optional[bool] = None
    opciones: Optional[Any] = None
    orden: Optional[int] = None
    activo: Optional[bool] = None
    validaciones: Optional[Any] = None


class CampoFormularioResponse(CampoFormularioBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class RespuestaFormularioBase(BaseModel):
    campo_formulario_id: UUID
    instancia_proceso_id: Optional[UUID] = None
    auditoria_id: Optional[UUID] = None
    valor: Optional[str] = None
    archivo_adjunto: Optional[str] = None
    usuario_respuesta_id: Optional[UUID] = None


class RespuestaFormularioCreate(RespuestaFormularioBase):
    pass


class RespuestaFormularioUpdate(BaseModel):
    valor: Optional[str] = None
    archivo_adjunto: Optional[str] = None
    usuario_respuesta_id: Optional[UUID] = None


class RespuestaFormularioResponse(RespuestaFormularioBase):
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
