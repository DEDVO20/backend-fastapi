"""
Schemas Pydantic para auditorías
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# Auditoria Schemas
class AuditoriaBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=200)
    tipo_auditoria: str = Field(..., max_length=50)
    alcance: Optional[str] = None
    objetivo: Optional[str] = None
    fecha_planificada: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: str = Field(default='planificada', max_length=50)
    equipo_auditor: Optional[str] = None
    auditor_lider_id: Optional[UUID] = None
    creado_por: Optional[UUID] = None
    informe_final: Optional[str] = None


class AuditoriaCreate(AuditoriaBase):
    pass


class AuditoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=200)
    tipo_auditoria: Optional[str] = Field(None, max_length=50)
    alcance: Optional[str] = None
    objetivo: Optional[str] = None
    fecha_planificada: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=50)
    equipo_auditor: Optional[str] = None
    auditor_lider_id: Optional[UUID] = None
    informe_final: Optional[str] = None


class AuditoriaResponse(AuditoriaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)


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
