"""
Schemas Pydantic para auditorías
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


# ProgramaAuditoria Schemas
class ProgramaAuditoriaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    anio: int
    objetivo: Optional[str] = None
    estado: Literal['borrador', 'aprobado', 'en_ejecucion', 'finalizado', 'cerrado'] = 'borrador'
    criterio_riesgo: Optional[str] = Field(None, alias="criterioRiesgo")
    aprobado_por: Optional[UUID] = Field(None, alias="aprobadoPorId")
    fecha_aprobacion: Optional[datetime] = Field(None, alias="fechaAprobacion")


class ProgramaAuditoriaCreate(ProgramaAuditoriaBase):
    pass


class ProgramaAuditoriaUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    anio: Optional[int] = None
    objetivo: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=30)
    criterio_riesgo: Optional[str] = Field(None, alias="criterioRiesgo")
    aprobado_por: Optional[UUID] = Field(None, alias="aprobadoPorId")
    fecha_aprobacion: Optional[datetime] = Field(None, alias="fechaAprobacion")

    @field_validator("estado")
    @classmethod
    def validar_estado_programa(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        estados_validos = {"borrador", "aprobado", "en_ejecucion", "finalizado", "cerrado"}
        if value not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(sorted(estados_validos))}")
        return value


class ProgramaAuditoriaResponse(ProgramaAuditoriaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Schema auxiliar para datos del auditor líder
class AuditorLiderInfo(BaseModel):
    id: UUID
    nombre: str
    primer_apellido: Optional[str] = Field(None, alias="primerApellido")
    correo_electronico: Optional[str] = Field(None, alias="email")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Auditoria Schemas
class AuditoriaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=200)
    tipo_auditoria: str = Field(..., max_length=50, alias="tipo")
    alcance: Optional[str] = None
    objetivo: Optional[str] = None
    fecha_planificada: Optional[datetime] = Field(None, alias="fechaPlanificada")
    fecha_inicio: Optional[datetime] = Field(None, alias="fechaInicio")
    fecha_fin: Optional[datetime] = Field(None, alias="fechaFin")
    estado: str = Field(default='planificada', max_length=50)
    norma_referencia: Optional[str] = Field("ISO 9001:2015", max_length=200, alias="normaReferencia")
    equipo_auditor: Optional[str] = Field(None, alias="equipoAuditor")
    auditor_lider_id: Optional[UUID] = Field(None, alias="auditorLiderId")
    proceso_id: Optional[UUID] = Field(None, alias="procesoId")
    creado_por: Optional[UUID] = Field(None, alias="creadoPor")
    informe_final: Optional[str] = Field(None, alias="informeFinal")
    programa_id: UUID = Field(..., alias="programaId")


class AuditoriaCreate(AuditoriaBase):
    pass


class AuditoriaUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    nombre: Optional[str] = Field(None, max_length=200)
    tipo_auditoria: Optional[str] = Field(None, max_length=50, alias="tipo")
    alcance: Optional[str] = None
    objetivo: Optional[str] = None
    fecha_planificada: Optional[datetime] = Field(None, alias="fechaPlanificada")
    fecha_inicio: Optional[datetime] = Field(None, alias="fechaInicio")
    fecha_fin: Optional[datetime] = Field(None, alias="fechaFin")
    estado: Optional[str] = Field(None, max_length=50)
    norma_referencia: Optional[str] = Field(None, max_length=200, alias="normaReferencia")
    equipo_auditor: Optional[str] = Field(None, alias="equipoAuditor")
    auditor_lider_id: Optional[UUID] = Field(None, alias="auditorLiderId")
    proceso_id: Optional[UUID] = Field(None, alias="procesoId")
    informe_final: Optional[str] = Field(None, alias="informeFinal")
    programa_id: Optional[UUID] = Field(None, alias="programaId")


class AuditoriaResponse(AuditoriaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    auditor_lider: Optional[AuditorLiderInfo] = Field(None, alias="auditorLider")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# HallazgoAuditoria Schemas
class HallazgoAuditoriaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auditoria_id: UUID = Field(..., alias="auditoriaId")
    codigo: str = Field(..., max_length=100)
    descripcion: str
    tipo_hallazgo: str = Field(..., max_length=50, alias="tipo")
    proceso_id: Optional[UUID] = None
    clausula_norma: Optional[str] = Field(None, max_length=100, alias="clausulaIso")
    evidencia: Optional[str] = None
    responsable_respuesta_id: Optional[UUID] = Field(None, alias="responsableId")
    fecha_respuesta: Optional[datetime] = None
    estado: str = Field(default='abierto', max_length=50)

    # Campos nuevos
    no_conformidad_id: Optional[UUID] = Field(None, alias="noConformidadId")
    verificado_por: Optional[UUID] = Field(None, alias="verificadoPor")
    fecha_verificacion: Optional[datetime] = Field(None, alias="fechaVerificacion")
    resultado_verificacion: Optional[str] = Field(None, alias="resultadoVerificacion")


class HallazgoAuditoriaCreate(HallazgoAuditoriaBase):
    pass


class HallazgoAuditoriaUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    descripcion: Optional[str] = None
    tipo_hallazgo: Optional[str] = Field(None, max_length=50, alias="tipo")
    proceso_id: Optional[UUID] = None
    clausula_norma: Optional[str] = Field(None, max_length=100, alias="clausulaIso")
    evidencia: Optional[str] = None
    responsable_respuesta_id: Optional[UUID] = Field(None, alias="responsableId")
    fecha_respuesta: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=50)
    
    no_conformidad_id: Optional[UUID] = Field(None, alias="noConformidadId")
    verificado_por: Optional[UUID] = Field(None, alias="verificadoPor")
    fecha_verificacion: Optional[datetime] = Field(None, alias="fechaVerificacion")
    resultado_verificacion: Optional[str] = Field(None, alias="resultadoVerificacion")


class HallazgoAuditoriaResponse(HallazgoAuditoriaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
