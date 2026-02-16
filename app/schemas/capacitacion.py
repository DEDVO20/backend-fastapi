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
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    fecha_cierre_asistencia: Optional[datetime] = None
    fecha_realizacion: Optional[datetime] = None
    lugar: Optional[str] = Field(None, max_length=200)
    estado: str = Field(default='programada', max_length=50)
    objetivo: Optional[str] = None
    contenido: Optional[str] = None
    area_id: Optional[UUID] = None
    aplica_todas_areas: bool = False
    responsable_id: Optional[UUID] = None
    proceso_id: Optional[UUID] = None
    relacionada_con_hallazgo_id: Optional[UUID] = None
    relacionada_con_riesgo_id: Optional[UUID] = None
    archivo_evidencia: Optional[str] = None


class CapacitacionCreate(CapacitacionBase):
    usuarios_convocados_ids: list[UUID] = Field(default_factory=list)


class CapacitacionUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    tipo_capacitacion: Optional[str] = Field(None, max_length=50)
    modalidad: Optional[str] = Field(None, max_length=50)
    duracion_horas: Optional[int] = None
    instructor: Optional[str] = Field(None, max_length=200)
    fecha_programada: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    fecha_cierre_asistencia: Optional[datetime] = None
    fecha_realizacion: Optional[datetime] = None
    lugar: Optional[str] = Field(None, max_length=200)
    estado: Optional[str] = Field(None, max_length=50)
    objetivo: Optional[str] = None
    contenido: Optional[str] = None
    area_id: Optional[UUID] = None
    aplica_todas_areas: Optional[bool] = None
    responsable_id: Optional[UUID] = None
    proceso_id: Optional[UUID] = None
    relacionada_con_hallazgo_id: Optional[UUID] = None
    relacionada_con_riesgo_id: Optional[UUID] = None
    archivo_evidencia: Optional[str] = None
    usuarios_convocados_ids: Optional[list[UUID]] = None


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
    fecha_registro: Optional[datetime] = None
    fecha_asistencia: Optional[datetime] = None
    evaluacion_aprobada: Optional[bool] = None


class AsistenciaCapacitacionCreate(AsistenciaCapacitacionBase):
    pass


class AsistenciaCapacitacionUpdate(BaseModel):
    asistio: Optional[bool] = None
    calificacion: Optional[Decimal] = Field(None, ge=0, le=100)
    observaciones: Optional[str] = None
    certificado: Optional[bool] = None
    fecha_asistencia: Optional[datetime] = None
    evaluacion_aprobada: Optional[bool] = None


class AsistenciaCapacitacionResponse(AsistenciaCapacitacionBase):
    id: UUID
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ResumenAsistenciaCapacitacionResponse(BaseModel):
    capacitacion_id: UUID
    total_participantes: int
    asistieron: int
    no_asistieron: int
    porcentaje_asistencia: float
    evaluados: int
    evaluacion_aprobada: int
    porcentaje_aprobacion: float


class UsuarioCapacitacionHistorialItem(BaseModel):
    capacitacion_id: UUID
    codigo: str
    nombre: str
    tipo_capacitacion: str
    estado: str
    fecha_programada: Optional[datetime] = None
    fecha_asistencia: Optional[datetime] = None
    asistio: bool
    evaluacion_aprobada: Optional[bool] = None
    calificacion: Optional[Decimal] = None
    observaciones: Optional[str] = None


class UsuarioSinCapacitacionObligatoriaResponse(BaseModel):
    usuario_id: UUID
    nombre: str
    primer_apellido: str
    capacitaciones_obligatorias_pendientes: int
    capacitaciones_ids: list[UUID]


class ReporteCapacitacionAuditoriaResponse(BaseModel):
    total_capacitaciones: int
    capacitaciones_programadas: int
    capacitaciones_ejecutadas: int
    total_registros_asistencia: int
    porcentaje_asistencia_promedio: float
    capacitaciones_sin_evidencia: int
    capacitaciones_obligatorias_sin_cobertura: int
