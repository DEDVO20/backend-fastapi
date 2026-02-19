"""
Modelo de Tickets / Mesa de Ayuda
"""
from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum
from datetime import datetime


class TipoTicket(str, enum.Enum):
    """Tipos de ticket disponibles"""
    SOPORTE = "soporte"
    CONSULTA = "consulta"
    MEJORA = "mejora"


class PrioridadTicket(str, enum.Enum):
    """Niveles de prioridad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoTicket(str, enum.Enum):
    """Estados del ciclo de vida del ticket"""
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"
    APROBADO = "aprobado"
    DECLINADO = "declinado"


def _generar_codigo_ticket():
    """Genera un código único para el ticket basado en timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TKT-{timestamp}"


class Ticket(BaseModel):
    """Modelo para tickets de la mesa de ayuda"""
    __tablename__ = "tickets"
    
    codigo = Column(String(100), nullable=False, default=_generar_codigo_ticket)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    categoria = Column(String(50), nullable=False, default=TipoTicket.SOPORTE.value)  # En BD es 'categoria', no 'tipo'
    prioridad = Column(String(50), nullable=False, default=PrioridadTicket.MEDIA.value)
    estado = Column(String(50), nullable=False, default=EstadoTicket.ABIERTO.value)
    
    # Foreign keys
    solicitante_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    asignado_a = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    area_destino_id = Column(UUID(as_uuid=True), ForeignKey("areas.id"), nullable=True)
    documento_publico_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True)
    archivo_adjunto_url = Column(Text, nullable=True)
    
    # Campos adicionales de la BD
    fecha_limite = Column(DateTime(timezone=True), nullable=True)
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)
    solucion = Column(Text, nullable=True)
    tiempo_resolucion = Column(Integer, nullable=True)  # En minutos
    satisfaccion_cliente = Column(Integer, nullable=True)  # 1-5
    
    # Relaciones
    solicitante = relationship("Usuario", back_populates="tickets_solicitados", foreign_keys=[solicitante_id])
    asignado = relationship("Usuario", back_populates="tickets_asignados", foreign_keys=[asignado_a])
    area_destino = relationship("Area", foreign_keys=[area_destino_id])
    documento_publico = relationship("Documento", foreign_keys=[documento_publico_id])
    
    def __repr__(self):
        return f"<Ticket(titulo={self.titulo}, estado={self.estado})>"
