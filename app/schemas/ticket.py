"""
Schemas Pydantic para Tickets
"""
from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID


class TipoTicket(str, Enum):
    """Tipos de ticket disponibles"""
    SOPORTE = "soporte"
    CONSULTA = "consulta"
    MEJORA = "mejora"


class PrioridadTicket(str, Enum):
    """Niveles de prioridad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoTicket(str, Enum):
    """Estados del ciclo de vida del ticket"""
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"


class TicketBase(BaseModel):
    """Schema base para Ticket"""
    titulo: str
    descripcion: str
    tipo: str  # Frontend usa 'tipo', se mapea a 'categoria' en BD
    prioridad: str

    model_config = ConfigDict(populate_by_name=True)


class TicketCreate(TicketBase):
    """Schema para crear un ticket"""
    pass


class TicketUpdate(BaseModel):
    """Schema para actualizar un ticket"""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[str] = None  # Frontend usa 'tipo'
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    asignado_a: Optional[UUID] = None

    model_config = ConfigDict(populate_by_name=True)


class TicketResponse(BaseModel):
    """Schema para respuesta de ticket"""
    id: UUID
    titulo: str
    descripcion: str
    tipo: str  # Devolver como 'tipo' al frontend
    prioridad: str
    estado: str
    solicitante_id: UUID
    asignado_a: Optional[UUID] = None
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
