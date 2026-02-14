from sqlalchemy import Column, String, Text, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class HistorialEstado(BaseModel):
    """Modelo para trazabilidad de cambios de estado"""
    __tablename__ = "historial_estados"
    
    entidad_tipo = Column(String(50), nullable=False) # 'auditoria', 'hallazgo', 'no_conformidad', etc.
    entidad_id = Column(UUID(as_uuid=True), nullable=False) # ID genérico
    estado_anterior = Column(String(50), nullable=True)
    estado_nuevo = Column(String(50), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    comentario = Column(Text, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario")

    __table_args__ = (
        Index('historial_entidad', 'entidad_tipo', 'entidad_id'),
    )

    def __repr__(self):
        return f"<HistorialEstado(entidad={self.entidad_tipo}, nuevo={self.estado_nuevo})>"
