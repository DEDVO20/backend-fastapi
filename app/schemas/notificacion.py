"""
Schemas de Pydantic para Notificaciones
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class NotificacionBase(BaseModel):
    """Schema base para notificaciones"""
    titulo: str = Field(..., max_length=200)
    mensaje: str
    tipo: str = Field(..., max_length=50)
    referencia_tipo: Optional[str] = Field(None, max_length=50)
    referencia_id: Optional[UUID] = None


class NotificacionCreate(NotificacionBase):
    """Schema para crear una notificación"""
    usuario_id: UUID


class NotificacionUpdate(BaseModel):
    """Schema para actualizar una notificación"""
    leida: Optional[bool] = None
    fecha_lectura: Optional[datetime] = None


class NotificacionResponse(NotificacionBase):
    """Schema de respuesta para notificaciones"""
    id: UUID
    usuario_id: UUID
    leida: bool
    fecha_lectura: Optional[datetime]
    creado_en: datetime
    
    class Config:
        from_attributes = True
