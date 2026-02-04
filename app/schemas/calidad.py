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
    gravedad: Optional[str] = Field(None, max_length=50)
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
    gravedad: Optional[str] = Field(None, max_length=50)
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


# Schema para usuarios anidados
class UsuarioNested(BaseModel):
    """Schema para mostrar información básica de usuarios en relaciones"""
    id: UUID
    nombre: str
    primerApellido: Optional[str] = Field(None, validation_alias="primer_apellido")
    segundoApellido: Optional[str] = Field(None, validation_alias="segundo_apellido")
    correoElectronico: Optional[str] = Field(None, validation_alias="correo_electronico")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# AccionCorrectiva Schemas
class AccionCorrectivaBase(BaseModel):
    no_conformidad_id: UUID = Field(..., validation_alias="noConformidadId")
    codigo: str = Field(..., max_length=50)
    tipo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    analisis_causa_raiz: Optional[str] = Field(None, validation_alias="analisisCausaRaiz")
    plan_accion: Optional[str] = Field(None, validation_alias="planAccion")
    responsable_id: Optional[UUID] = Field(None, validation_alias="responsableId")
    fecha_compromiso: Optional[date] = Field(None, validation_alias="fechaCompromiso")
    fecha_implementacion: Optional[date] = Field(None, validation_alias="fechaImplementacion")
    implementado_por: Optional[UUID] = Field(None, validation_alias="implementadoPor")
    estado: Optional[str] = Field(None, max_length=50)
    eficacia_verificada: Optional[int] = Field(None, validation_alias="eficaciaVerificada")
    verificado_por: Optional[UUID] = Field(None, validation_alias="verificadoPor")
    fecha_verificacion: Optional[date] = Field(None, validation_alias="fechaVerificacion")
    observacion: Optional[str] = None
    evidencias: Optional[str] = None  # JSON string con URLs o descripciones
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AccionCorrectivaEstadoUpdate(BaseModel):
    estado: str = Field(..., max_length=50)


class AccionCorrectivaVerificacion(BaseModel):
    observaciones: Optional[str] = None
    eficacia_verificada: Optional[int] = Field(None, validation_alias="eficaciaVerificada")
    
    model_config = ConfigDict(populate_by_name=True)


class AccionCorrectivaImplementacion(BaseModel):
    """Schema para implementar una acción correctiva"""
    fechaImplementacion: Optional[date] = Field(None, validation_alias="fecha_implementacion")
    observacion: Optional[str] = None
    evidencias: Optional[str] = None
    estado: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class AccionCorrectivaCreate(AccionCorrectivaBase):
    pass


class AccionCorrectivaUpdate(BaseModel):
    tipo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    analisis_causa_raiz: Optional[str] = Field(None, validation_alias="analisisCausaRaiz")
    plan_accion: Optional[str] = Field(None, validation_alias="planAccion")
    responsable_id: Optional[UUID] = Field(None, validation_alias="responsableId")
    fecha_compromiso: Optional[date] = Field(None, validation_alias="fechaCompromiso")
    fecha_implementacion: Optional[date] = Field(None, validation_alias="fechaImplementacion")
    implementado_por: Optional[UUID] = Field(None, validation_alias="implementadoPor")
    estado: Optional[str] = Field(None, max_length=50)
    eficacia_verificada: Optional[int] = Field(None, validation_alias="eficaciaVerificada")
    verificado_por: Optional[UUID] = Field(None, validation_alias="verificadoPor")
    fecha_verificacion: Optional[date] = Field(None, validation_alias="fechaVerificacion")
    observacion: Optional[str] = None
    evidencias: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class AccionCorrectivaResponse(AccionCorrectivaBase):
    id: UUID
    creadoEn: datetime = Field(..., validation_alias="creado_en")
    actualizadoEn: datetime = Field(..., validation_alias="actualizado_en")
    
    # Relaciones con usuarios
    responsable: Optional[UsuarioNested] = None
    implementador: Optional[UsuarioNested] = None
    verificador: Optional[UsuarioNested] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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


# SeguimientoObjetivo Schemas
class SeguimientoObjetivoBase(BaseModel):
    objetivo_calidad_id: UUID
    fecha_seguimiento: datetime
    valor_actual: Optional[Decimal] = None
    observaciones: Optional[str] = None
    responsable_id: Optional[UUID] = None


class SeguimientoObjetivoCreate(SeguimientoObjetivoBase):
    pass


class SeguimientoObjetivoUpdate(BaseModel):
    fecha_seguimiento: Optional[datetime] = None
    valor_actual: Optional[Decimal] = None
    observaciones: Optional[str] = None
    responsable_id: Optional[UUID] = None


class SeguimientoObjetivoResponse(SeguimientoObjetivoBase):
    id: UUID
    # No tiene timestamps base (creado_en/actualizado_en) en el modelo, solo lo que hereda de BaseModel si lo tuviera.
    # Revisando modelo: class SeguimientoObjetivo(BaseModel) -> hereda de .base.BaseModel.
    # Asumimos que tiene id. 
    # El modelo tiene: # Nota: solo tiene creado_en en el comentario del modelo, pero hereda de BaseModel.
    # BaseModel suele tener id, creado_en, actualizado_en.
    # Verificaremos si BaseModel del backend los tiene.
    
    model_config = ConfigDict(from_attributes=True)
