"""
Schemas Pydantic para gestión de calidad
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


from .proceso import ProcesoResponse

TIPOS_INDICADOR = {"eficacia", "eficiencia", "cumplimiento"}
ESTADOS_INDICADOR = {"borrador", "pendiente_aprobacion", "aprobado", "rechazado"}


# Schema para usuarios anidados
class UsuarioNested(BaseModel):
    """Schema para mostrar información básica de usuarios en relaciones"""
    id: UUID
    documento: Optional[int] = None
    nombre: str = ""
    segundoNombre: Optional[str] = Field(None, validation_alias="segundo_nombre")
    primerApellido: Optional[str] = Field(None, validation_alias="primer_apellido")
    segundoApellido: Optional[str] = Field(None, validation_alias="segundo_apellido")
    correoElectronico: Optional[str] = Field(None, validation_alias="correo_electronico")
    nombreUsuario: Optional[str] = Field(None, validation_alias="nombre_usuario")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("nombre", mode="before")
    @classmethod
    def nombre_no_nulo(cls, value):
        return value or ""


class ProcesoIndicadorNested(BaseModel):
    id: UUID
    codigo: Optional[str] = None
    nombre: str

    model_config = ConfigDict(from_attributes=True)


def _validar_tipo_indicador(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    tipo = value.strip().lower()
    if tipo not in TIPOS_INDICADOR:
        raise ValueError(f"Tipo inválido. Use uno de: {', '.join(sorted(TIPOS_INDICADOR))}")
    return tipo


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
    tipo_indicador: str = Field(default="eficacia", max_length=50)
    activo: bool = True


class IndicadorCreate(IndicadorBase):
    codigo: Optional[str] = Field(None, max_length=100)

    @field_validator("tipo_indicador")
    @classmethod
    def validar_tipo(cls, value: str) -> str:
        return _validar_tipo_indicador(value) or "eficacia"


class IndicadorUpdate(BaseModel):
    proceso_id: Optional[UUID] = None
    codigo: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    formula: Optional[str] = None
    unidad_medida: Optional[str] = Field(None, max_length=50)
    meta: Optional[Decimal] = None
    frecuencia_medicion: Optional[str] = Field(None, max_length=50)
    responsable_medicion_id: Optional[UUID] = None
    tipo_indicador: Optional[str] = Field(None, max_length=50)
    activo: Optional[bool] = None

    @field_validator("tipo_indicador")
    @classmethod
    def validar_tipo(cls, value: Optional[str]) -> Optional[str]:
        return _validar_tipo_indicador(value)


class MedicionIndicadorBase(BaseModel):
    periodo: str = Field(..., max_length=20)
    valor: Decimal
    meta: Optional[Decimal] = None
    observaciones: Optional[str] = None


class MedicionIndicadorCreate(MedicionIndicadorBase):
    pass


class MedicionIndicadorResponse(MedicionIndicadorBase):
    id: UUID
    indicador_id: UUID
    cumple_meta: Optional[bool] = None
    registrado_por: Optional[UUID] = None
    creado_en: datetime
    actualizado_en: datetime
    registrador: Optional[UsuarioNested] = None

    model_config = ConfigDict(from_attributes=True)


class IndicadorDecision(BaseModel):
    observacion: Optional[str] = None


class IndicadorResponse(IndicadorBase):
    id: UUID
    estado: str = "borrador"
    creado_por: Optional[UUID] = None
    revisado_por: Optional[UUID] = None
    fecha_revision: Optional[datetime] = None
    aprobado_por: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    observacion_aprobacion: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime
    proceso: Optional[ProcesoIndicadorNested] = None
    responsable: Optional[UsuarioNested] = None
    creador: Optional[UsuarioNested] = None
    revisador: Optional[UsuarioNested] = None
    aprobador: Optional[UsuarioNested] = None
    ultima_medicion: Optional[MedicionIndicadorResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tipo_indicador", mode="before")
    @classmethod
    def coerce_tipo(cls, value):
        if not value:
            return "eficacia"
        tipo = str(value).strip().lower()
        return tipo if tipo in TIPOS_INDICADOR else "eficacia"

    @field_validator("estado", mode="before")
    @classmethod
    def coerce_estado(cls, value):
        if not value:
            return "borrador"
        estado = str(value).strip().lower()
        return estado if estado in ESTADOS_INDICADOR else "borrador"


class TendenciaIndicadorResponse(BaseModel):
    indicador_id: UUID
    total_mediciones: int
    promedio: Decimal
    ultimo_valor: Optional[Decimal] = None
    ultimo_periodo: Optional[str] = None
    tendencia: str


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
    evidencias: Optional[str] = None # JSON string
    fecha_cierre: Optional[datetime] = None
    responsable_id: Optional[UUID] = None


class NoConformidadCreate(NoConformidadBase):
    codigo: Optional[str] = Field(None, max_length=100)


class NoConformidadUpdate(BaseModel):
    descripcion: Optional[str] = None
    proceso_id: Optional[UUID] = None
    tipo: Optional[str] = Field(None, max_length=50)
    fuente: Optional[str] = Field(None, max_length=100)
    gravedad: Optional[str] = Field(None, max_length=50)
    estado: Optional[str] = Field(None, max_length=50)
    detectado_por: Optional[UUID] = None
    analisis_causa: Optional[str] = None
    plan_accion: Optional[str] = None
    evidencias: Optional[str] = None
    fecha_cierre: Optional[datetime] = None
    responsable_id: Optional[UUID] = None


class NoConformidadResponse(NoConformidadBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    # Nested objects
    proceso: Optional[ProcesoResponse] = None
    detector: Optional[UsuarioNested] = None
    responsable: Optional[UsuarioNested] = None

    model_config = ConfigDict(from_attributes=True)


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
    eficaz: Optional[bool] = None
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
    codigo: Optional[str] = Field(None, max_length=50)


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


class AccionCorrectivaComentarioBase(BaseModel):
    comentario: str = Field(..., min_length=1)

class AccionCorrectivaComentarioCreate(AccionCorrectivaComentarioBase):
    pass

class AccionCorrectivaComentarioResponse(AccionCorrectivaComentarioBase):
    id: UUID
    accion_correctiva_id: UUID
    usuario_id: UUID
    usuario: Optional[UsuarioNested] = None
    creadoEn: datetime = Field(..., validation_alias="creado_en")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AccionCorrectivaResponse(AccionCorrectivaBase):
    id: UUID
    creadoEn: datetime = Field(..., validation_alias="creado_en")
    actualizadoEn: datetime = Field(..., validation_alias="actualizado_en")
    
    # Relaciones con usuarios
    responsable: Optional[UsuarioNested] = None
    implementador: Optional[UsuarioNested] = None
    verificador: Optional[UsuarioNested] = None
    
    # Comentarios
    comentarios: Optional[list[AccionCorrectivaComentarioResponse]] = []
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ObjetivoCalidad Schemas
class ObjetivoCalidadBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    descripcion: str = Field(..., min_length=10)
    area_id: Optional[UUID] = None
    responsable_id: Optional[UUID] = None
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str = Field(default='planificado', max_length=50)
    progreso: Decimal = Field(default=0, ge=0, le=100)
    # ISO 9001:2015 Cláusula 6.2
    meta: Optional[str] = None
    indicador: Optional[str] = Field(None, max_length=255)
    valor_meta: Optional[Decimal] = Field(None, ge=0)

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not str(value).strip():
            return None
        return str(value).strip().upper()

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, value: str) -> str:
        estados_permitidos = {"planificado", "en_curso", "cumplido", "no_cumplido", "cancelado"}
        estado = value.strip().lower()
        if estado not in estados_permitidos:
            raise ValueError(f"Estado inválido. Use uno de: {', '.join(sorted(estados_permitidos))}")
        return estado


class ObjetivoCalidadCreate(ObjetivoCalidadBase):
    codigo: Optional[str] = Field(None, max_length=100)

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return self


class ObjetivoCalidadUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=10)
    area_id: Optional[UUID] = None
    responsable_id: Optional[UUID] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=50)
    progreso: Optional[Decimal] = Field(None, ge=0, le=100)
    meta: Optional[str] = None
    indicador: Optional[str] = Field(None, max_length=255)
    valor_meta: Optional[Decimal] = Field(None, ge=0)

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        estados_permitidos = {"planificado", "en_curso", "cumplido", "no_cumplido", "cancelado"}
        estado = value.strip().lower()
        if estado not in estados_permitidos:
            raise ValueError(f"Estado inválido. Use uno de: {', '.join(sorted(estados_permitidos))}")
        return estado


class _AreaSimple(BaseModel):
    id: UUID
    nombre: str
    codigo: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class _ResponsableSimple(BaseModel):
    id: UUID
    documento: Optional[int] = None
    nombre: str
    segundo_nombre: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = None
    correo_electronico: Optional[str] = None
    nombre_usuario: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ObjetivoCalidadResponse(BaseModel):
    id: UUID
    codigo: str
    descripcion: str
    area_id: Optional[UUID] = None
    responsable_id: Optional[UUID] = None
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str
    progreso: Decimal = Field(default=0)
    meta: Optional[str] = None
    indicador: Optional[str] = None
    valor_meta: Optional[Decimal] = None
    creado_en: datetime
    actualizado_en: datetime
    
    # Relaciones opcionales (si se cargan con joinedload)
    area: Optional[_AreaSimple] = None
    responsable: Optional[_ResponsableSimple] = None
    
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


class SeguimientoObjetivoResponse(BaseModel):
    id: UUID
    objetivo_calidad_id: UUID
    fecha_seguimiento: datetime
    valor_actual: Optional[Decimal] = None
    observaciones: Optional[str] = None
    responsable_id: Optional[UUID] = None
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
