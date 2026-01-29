"""
Modelo de Tickets / Mesa de Ayuda
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class TipoTicket(str, enum.Enum):
    SOPORTE = "soporte"
    CONSULTA = "consulta"
    MEJORA = "mejora"

class PrioridadTicket(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class EstadoTicket(str, enum.Enum):
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"

class Ticket(BaseModel):
    """Modelo para tickets de la mesa de ayuda"""
    __tablename__ = "tickets"
    
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo = Column(String(50), nullable=False, default=TipoTicket.SOPORTE.value)
    prioridad = Column(String(50), nullable=False, default=PrioridadTicket.MEDIA.value)
    estado = Column(String(50), nullable=False, default=EstadoTicket.ABIERTO.value)
    
    solicitante_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    asignado_a = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    
    # Relaciones
    solicitante = relationship("Usuario", back_populates="tickets_solicitados", foreign_keys=[solicitante_id])
    asignado = relationship("Usuario", back_populates="tickets_asignados", foreign_keys=[asignado_a])
    
    def __repr__(self):
        return f"<Ticket(titulo={self.titulo}, estado={self.estado})>"
