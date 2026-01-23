"""
Schemas Pydantic para procesos y sus componentes
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


# Proceso Schemas
class ProcesoBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=300)
    area_id: Optional[UUID] = None
    objetivo: Optional[str] = None
    alcance: Optional[str] = None
    etapa_phva: Optional[str] = Field(None, max_length=50)
    restringido: bool = False
    tipo_proceso: Optional[str] = Field(None, max_length=50)
    responsable_id: Optional[UUID] = None
    estado: str = Field(default='activo', max_length=50)
    version: Optional[str] = Field(None, max_length=20)
    fecha_aprobacion: Optional[date] = None
    proxima_revision: Optional[date] = None


class ProcesoCreate(ProcesoBase):
    pass


class ProcesoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=300)
    area_id: Optional[UUID] = None
    objetivo: Optional[str] = None
    alcance: Optional[str] = None
    etapa_phva: Optional[str] = Field(None, max_length=50)
    restringido: Optional[bool] = None
    tipo_proceso: Optional[str] = Field(None, max_length=50)
    responsable_id: Optional[UUID] = None
    estado: Optional[str] = Field(None, max_length=50)
    version: Optional[str] = Field(None, max_length=20)
    fecha_aprobacion: Optional[date] = None
    proxima_revision: Optional[date] = None


class ProcesoResponse(ProcesoBase):
    id: UUID
    creado_por: Optional[UUID] = None
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# EtapaProceso Schemas
class EtapaProcesoBase(BaseModel):
    proceso_id: UUID
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    orden: int = Field(default=1)
    responsable_id: Optional[UUID] = None
    tiempo_estimado: Optional[int] = None
    activa: bool = True


class EtapaProcesoCreate(EtapaProcesoBase):
    pass


class EtapaProcesoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    responsable_id: Optional[UUID] = None
    tiempo_estimado: Optional[int] = None
    activa: Optional[bool] = None


class EtapaProcesoResponse(EtapaProcesoBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# InstanciaProceso Schemas
class InstanciaProcesoBase(BaseModel):
    proceso_id: UUID
    codigo_instancia: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    estado: str = Field(default='iniciado', max_length=50)
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    iniciado_por: Optional[UUID] = None


class InstanciaProcesoCreate(InstanciaProcesoBase):
    pass


class InstanciaProcesoUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=50)
    fecha_fin: Optional[datetime] = None


class InstanciaProcesoResponse(InstanciaProcesoBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


# AccionProceso Schemas
class AccionProcesoBase(BaseModel):
    proceso_id: UUID
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    tipo_accion: str = Field(..., max_length=50)
    origen: Optional[str] = Field(None, max_length=100)
    responsable_id: Optional[UUID] = None
    fecha_planificada: Optional[datetime] = None
    fecha_implementacion: Optional[datetime] = None
    fecha_verificacion: Optional[datetime] = None
    estado: str = Field(default='planificada', max_length=50)
    efectividad: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None


class AccionProcesoCreate(AccionProcesoBase):
    pass


class AccionProcesoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    tipo_accion: Optional[str] = Field(None, max_length=50)
    origen: Optional[str] = Field(None, max_length=100)
    responsable_id: Optional[UUID] = None
    fecha_planificada: Optional[datetime] = None
    fecha_implementacion: Optional[datetime] = None
    fecha_verificacion: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=50)
    efectividad: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None


class AccionProcesoResponse(AccionProcesoBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)
