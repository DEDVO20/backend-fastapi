"""
Schemas Pydantic para riesgos
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


# Riesgo Schemas
class RiesgoBase(BaseModel):
    proceso_id: UUID
    etapa_proceso_id: Optional[UUID] = None
    codigo: str = Field(..., max_length=100)
    descripcion: str
    categoria: Optional[str] = Field(None, max_length=100)
    tipo_riesgo: str = Field(..., max_length=50)
    probabilidad: Optional[int] = Field(None, ge=1, le=5)
    impacto: Optional[int] = Field(None, ge=1, le=5)
    nivel_riesgo: Optional[str] = Field(None, max_length=50)
    nivel_residual: Optional[int] = None
    causas: Optional[str] = None
    consecuencias: Optional[str] = None
    responsable_id: Optional[UUID] = None
    estado: str = Field(default='activo', max_length=50)
    fecha_identificacion: Optional[date] = None
    fecha_revision: Optional[date] = None
    tratamiento: Optional[str] = None


class RiesgoCreate(RiesgoBase):
    pass


class RiesgoUpdate(BaseModel):
    etapa_proceso_id: Optional[UUID] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = Field(None, max_length=100)
    tipo_riesgo: Optional[str] = Field(None, max_length=50)
    probabilidad: Optional[int] = Field(None, ge=1, le=5)
    impacto: Optional[int] = Field(None, ge=1, le=5)
    nivel_riesgo: Optional[str] = Field(None, max_length=50)
    nivel_residual: Optional[int] = None
    causas: Optional[str] = None
    consecuencias: Optional[str] = None
    responsable_id: Optional[UUID] = None
    estado: Optional[str] = Field(None, max_length=50)
    fecha_identificacion: Optional[date] = None
    fecha_revision: Optional[date] = None
    tratamiento: Optional[str] = None


class RiesgoResponse(RiesgoBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ControlRiesgo Schemas
class ControlRiesgoBase(BaseModel):
    riesgo_id: UUID
    descripcion: str
    tipo_control: str = Field(..., max_length=50)
    frecuencia: Optional[str] = Field(None, max_length=50)
    responsable_id: Optional[UUID] = None
    efectividad: Optional[str] = Field(None, max_length=50)
    activo: bool = True


class ControlRiesgoCreate(ControlRiesgoBase):
    pass


class ControlRiesgoUpdate(BaseModel):
    descripcion: Optional[str] = None
    tipo_control: Optional[str] = Field(None, max_length=50)
    frecuencia: Optional[str] = Field(None, max_length=50)
    responsable_id: Optional[UUID] = None
    efectividad: Optional[str] = Field(None, max_length=50)
    activo: Optional[bool] = None


class ControlRiesgoResponse(ControlRiesgoBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)
