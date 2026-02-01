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
    categoria: str
    prioridad: str


class TicketCreate(TicketBase):
    """Schema para crear un ticket"""
    pass


class TicketUpdate(BaseModel):
    """Schema para actualizar un ticket"""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    asignado_a: Optional[UUID] = None


class TicketResolver(BaseModel):
    """Schema para resolver un ticket"""
    solucion: str
    satisfaccion_cliente: Optional[int] = None


class TicketResponse(TicketBase):
    """Schema para respuesta de ticket"""
    id: UUID
    estado: str
    solicitante_id: UUID
    asignado_a: Optional[UUID] = None
    
    # Campos de resolución
    solucion: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None
    satisfaccion_cliente: Optional[int] = None
    
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)
