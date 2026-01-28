"""
Schemas Pydantic para Competencias
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

# --- Competencia Schemas ---
class CompetenciaBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None

class CompetenciaCreate(CompetenciaBase):
    pass

class CompetenciaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None

class CompetenciaResponse(CompetenciaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)


# --- EvaluacionCompetencia Schemas ---
class EvaluacionCompetenciaBase(BaseModel):
    usuario_id: UUID
    competencia_id: UUID
    nivel: str = Field(..., max_length=50)  # Básico, Intermedio, Avanzado
    estado: str = Field(..., max_length=50) # Pendiente, En Desarrollo, Reforzada, Desarrollada
    fecha_evaluacion: datetime
    evaluador_id: Optional[UUID] = None
    observaciones: Optional[str] = None

class EvaluacionCompetenciaCreate(EvaluacionCompetenciaBase):
    pass

class EvaluacionCompetenciaUpdate(BaseModel):
    nivel: Optional[str] = Field(None, max_length=50)
    estado: Optional[str] = Field(None, max_length=50)
    fecha_evaluacion: Optional[datetime] = None
    observaciones: Optional[str] = None

class EvaluacionCompetenciaResponse(EvaluacionCompetenciaBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    
    # Nested info for display
    competencia: Optional[CompetenciaResponse] = None
    
    model_config = ConfigDict(from_attributes=True)
