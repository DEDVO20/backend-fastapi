from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID

class TipoTicket(str, Enum):
    SOPORTE = "soporte"
    CONSULTA = "consulta"
    MEJORA = "mejora"

class PrioridadTicket(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class EstadoTicket(str, Enum):
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"

class TicketBase(BaseModel):
    titulo: str
    descripcion: str
    tipo: TipoTicket
    prioridad: PrioridadTicket

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[TipoTicket] = None
    prioridad: Optional[PrioridadTicket] = None
    estado: Optional[EstadoTicket] = None
    asignado_a: Optional[UUID] = None

class TicketResponse(TicketBase):
    id: UUID
    estado: EstadoTicket
    solicitante_id: UUID
    asignado_a: Optional[UUID] = None
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)
