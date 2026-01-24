"""
Schemas Pydantic para la API de migraciones de base de datos.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MigracionInfo(BaseModel):
    """Información de una migración individual."""
    revision: str = Field(..., description="ID de la revisión")
    down_revision: Optional[str] = Field(None, description="Revisión anterior")
    descripcion: str = Field(..., description="Descripción de la migración")
    fecha_creacion: Optional[str] = Field(None, description="Fecha de creación del archivo")
    aplicada: bool = Field(..., description="Si la migración está aplicada")
    fecha_aplicacion: Optional[datetime] = Field(None, description="Fecha de aplicación")


class MigracionEstadoActual(BaseModel):
    """Estado actual de la base de datos."""
    revision_actual: Optional[str] = Field(None, description="Revisión actual de la BD")
    descripcion: Optional[str] = Field(None, description="Descripción de la revisión actual")
    total_migraciones: int = Field(..., description="Total de migraciones disponibles")
    migraciones_aplicadas: int = Field(..., description="Número de migraciones aplicadas")
    migraciones_pendientes: int = Field(..., description="Número de migraciones pendientes")
    ultima_actualizacion: Optional[datetime] = Field(None, description="Última actualización")


class MigracionHistorialItem(BaseModel):
    """Entrada del historial de migraciones."""
    revision: str
    descripcion: str
    fecha: datetime
    operacion: str = Field(..., description="upgrade o downgrade")


class MigracionOperacionRequest(BaseModel):
    """Request para operaciones de migración."""
    target: str = Field(..., description="Revisión objetivo o 'head'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target": "head"
            }
        }


class MigracionOperacionResponse(BaseModel):
    """Respuesta de una operación de migración."""
    success: bool
    message: str
    revision_anterior: Optional[str] = None
    revision_nueva: Optional[str] = None
    output: Optional[str] = None


class MigracionListaResponse(BaseModel):
    """Respuesta con lista de migraciones."""
    migraciones: List[MigracionInfo]
    estado: MigracionEstadoActual
