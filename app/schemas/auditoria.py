"""
Schemas Pydantic para auditorías
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


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
    norma_referencia: Optional[str] = Field(None, max_length=200, alias="normaReferencia")
    equipo_auditor: Optional[str] = Field(None, alias="equipoAuditor")
    auditor_lider_id: Optional[UUID] = Field(None, alias="auditorLiderId")
    creado_por: Optional[UUID] = Field(None, alias="creadoPor")
    informe_final: Optional[str] = Field(None, alias="informeFinal")


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
    informe_final: Optional[str] = Field(None, alias="informeFinal")


class AuditoriaResponse(AuditoriaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# HallazgoAuditoria Schemas
class HallazgoAuditoriaBase(BaseModel):
    auditoria_id: UUID
    codigo: str = Field(..., max_length=100)
    descripcion: str
    tipo_hallazgo: str = Field(..., max_length=50)
    proceso_id: Optional[UUID] = None
    clausula_norma: Optional[str] = Field(None, max_length=100)
    evidencia: Optional[str] = None
    responsable_respuesta_id: Optional[UUID] = None
    fecha_respuesta: Optional[datetime] = None
    estado: str = Field(default='abierto', max_length=50)


class HallazgoAuditoriaCreate(HallazgoAuditoriaBase):
    pass


class HallazgoAuditoriaUpdate(BaseModel):
    descripcion: Optional[str] = None
    tipo_hallazgo: Optional[str] = Field(None, max_length=50)
    proceso_id: Optional[UUID] = None
    clausula_norma: Optional[str] = Field(None, max_length=100)
    evidencia: Optional[str] = None
    responsable_respuesta_id: Optional[UUID] = None
    fecha_respuesta: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=50)


class HallazgoAuditoriaResponse(HallazgoAuditoriaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)
