"""
Schemas Pydantic para gestión de calidad
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


# Indicador Schemas
class IndicadorBase(BaseModel):
    proceso_id: UUID
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    formula: Optional[str] = None
    unidad_medida: Optional[str] = Field(None, max_length=50)
    meta: Optional[Decimal] = None
    frecuencia_medicion: str = Field(default='mensual', max_length=50)
    responsable_medicion_id: Optional[UUID] = None
    activo: bool = True


class IndicadorCreate(IndicadorBase):
    pass


class IndicadorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    formula: Optional[str] = None
    unidad_medida: Optional[str] = Field(None, max_length=50)
    meta: Optional[Decimal] = None
    frecuencia_medicion: Optional[str] = Field(None, max_length=50)
    responsable_medicion_id: Optional[UUID] = None
    activo: Optional[bool] = None


class IndicadorResponse(IndicadorBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# NoConformidad Schemas
class NoConformidadBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    descripcion: str
    proceso_id: Optional[UUID] = None
    tipo: str = Field(..., max_length=50)
    fuente: str = Field(..., max_length=100)
    detectado_por: Optional[UUID] = None
    fecha_deteccion: datetime
    estado: str = Field(default='abierta', max_length=50)
    analisis_causa: Optional[str] = None
    plan_accion: Optional[str] = None
    fecha_cierre: Optional[datetime] = None
    responsable_id: Optional[UUID] = None


class NoConformidadCreate(NoConformidadBase):
    pass


class NoConformidadUpdate(BaseModel):
    descripcion: Optional[str] = None
    proceso_id: Optional[UUID] = None
    tipo: Optional[str] = Field(None, max_length=50)
    fuente: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=50)
    analisis_causa: Optional[str] = None
    plan_accion: Optional[str] = None
    fecha_cierre: Optional[datetime] = None
    responsable_id: Optional[UUID] = None


class NoConformidadResponse(NoConformidadBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# AccionCorrectiva Schemas
class AccionCorrectivaBase(BaseModel):
    no_conformidad_id: UUID
    codigo: str = Field(..., max_length=50)
    tipo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    analisis_causa_raiz: Optional[str] = None
    plan_accion: Optional[str] = None
    responsable_id: Optional[UUID] = None
    fecha_compromiso: Optional[date] = None
    fecha_implementacion: Optional[date] = None
    estado: Optional[str] = Field(None, max_length=50)
    eficacia_verificada: Optional[bool] = None
    verificado_por: Optional[UUID] = None
    fecha_verificacion: Optional[date] = None
    observacion: Optional[str] = None


class AccionCorrectivaEstadoUpdate(BaseModel):
    estado: str = Field(..., max_length=50)


class AccionCorrectivaVerificacion(BaseModel):
    observaciones: Optional[str] = None


class AccionCorrectivaCreate(AccionCorrectivaBase):
    pass


class AccionCorrectivaUpdate(BaseModel):
    tipo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    analisis_causa_raiz: Optional[str] = None
    plan_accion: Optional[str] = None
    responsable_id: Optional[UUID] = None
    fecha_compromiso: Optional[date] = None
    fecha_implementacion: Optional[date] = None
    estado: Optional[str] = Field(None, max_length=50)
    eficacia_verificada: Optional[bool] = None
    verificado_por: Optional[UUID] = None
    fecha_verificacion: Optional[date] = None
    observacion: Optional[str] = None


class AccionCorrectivaResponse(AccionCorrectivaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ObjetivoCalidad Schemas
class ObjetivoCalidadBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    descripcion: str
    area_id: Optional[UUID] = None
    responsable_id: Optional[UUID] = None
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str = Field(default='planificado', max_length=50)
    progreso: Decimal = Field(default=0, ge=0, le=100)


class ObjetivoCalidadCreate(ObjetivoCalidadBase):
    pass


class ObjetivoCalidadUpdate(BaseModel):
    descripcion: Optional[str] = None
    area_id: Optional[UUID] = None
    responsable_id: Optional[UUID] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=50)
    progreso: Optional[Decimal] = Field(None, ge=0, le=100)


class ObjetivoCalidadResponse(ObjetivoCalidadBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)
