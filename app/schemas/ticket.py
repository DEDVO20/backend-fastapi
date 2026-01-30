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
    categoria: TipoTicket  # En BD es 'categoria', no 'tipo'
    prioridad: PrioridadTicket


class TicketCreate(TicketBase):
    """Schema para crear un ticket"""
    pass


class TicketUpdate(BaseModel):
    """Schema para actualizar un ticket"""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[TipoTicket] = None  # En BD es 'categoria'
    prioridad: Optional[PrioridadTicket] = None
    estado: Optional[EstadoTicket] = None
    asignado_a: Optional[UUID] = None


class TicketResponse(TicketBase):
    """Schema para respuesta de ticket"""
    id: UUID
    estado: EstadoTicket
    solicitante_id: UUID
    asignado_a: Optional[UUID] = None
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)
