"""
Schemas Pydantic para capacitaciones
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# Capacitacion Schemas
class CapacitacionBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    tipo_capacitacion: str = Field(..., max_length=50)
    modalidad: str = Field(..., max_length=50)
    duracion_horas: Optional[int] = None
    instructor: Optional[str] = Field(None, max_length=200)
    fecha_programada: Optional[datetime] = None
    fecha_realizacion: Optional[datetime] = None
    lugar: Optional[str] = Field(None, max_length=200)
    estado: str = Field(default='programada', max_length=50)
    objetivo: Optional[str] = None
    contenido: Optional[str] = None
    responsable_id: Optional[UUID] = None


class CapacitacionCreate(CapacitacionBase):
    pass


class CapacitacionUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    tipo_capacitacion: Optional[str] = Field(None, max_length=50)
    modalidad: Optional[str] = Field(None, max_length=50)
    duracion_horas: Optional[int] = None
    instructor: Optional[str] = Field(None, max_length=200)
    fecha_programada: Optional[datetime] = None
    fecha_realizacion: Optional[datetime] = None
    lugar: Optional[str] = Field(None, max_length=200)
    estado: Optional[str] = Field(None, max_length=50)
    objetivo: Optional[str] = None
    contenido: Optional[str] = None
    responsable_id: Optional[UUID] = None


class CapacitacionResponse(CapacitacionBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# AsistenciaCapacitacion Schemas
class AsistenciaCapacitacionBase(BaseModel):
    capacitacion_id: UUID
    usuario_id: UUID
    asistio: bool = False
    calificacion: Optional[Decimal] = Field(None, ge=0, le=100)
    observaciones: Optional[str] = None
    certificado: bool = False
    fecha_registro: datetime


class AsistenciaCapacitacionCreate(AsistenciaCapacitacionBase):
    pass


class AsistenciaCapacitacionUpdate(BaseModel):
    asistio: Optional[bool] = None
    calificacion: Optional[Decimal] = Field(None, ge=0, le=100)
    observaciones: Optional[str] = None
    certificado: Optional[bool] = None


class AsistenciaCapacitacionResponse(AsistenciaCapacitacionBase):
    id: UUID
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)
