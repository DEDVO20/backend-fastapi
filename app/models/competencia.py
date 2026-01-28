"""
Modelos de Competencias (ISO 9001:2015 Clause 7.2)
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Competencia(BaseModel):
    """
    Catálogo de Competencias (e.g., Liderazgo, Python, Trabajo en Equipo)
    """
    __tablename__ = "competencias"

    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)

    # Relaciones
    evaluaciones = relationship("EvaluacionCompetencia", back_populates="competencia")

    def __repr__(self):
        return f"<Competencia(nombre={self.nombre})>"


class EvaluacionCompetencia(BaseModel):
    """
    Evaluación de una competencia específica para un usuario.
    Registra el nivel alcanzado y el estado.
    """
    __tablename__ = "evaluaciones_competencia"

    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    competencia_id = Column(UUID(as_uuid=True), ForeignKey("competencias.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    
    nivel = Column(String(50), nullable=False)  # Básico, Intermedio, Avanzado
    estado = Column(String(50), nullable=False) # Pendiente, En Desarrollo, Reforzada, Desarrollada
    fecha_evaluacion = Column(DateTime(timezone=True), nullable=False)
    
    evaluador_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    observaciones = Column(Text, nullable=True)

    # Relaciones
    usuario = relationship("Usuario", back_populates="competencias_evaluadas", foreign_keys=[usuario_id])
    competencia = relationship("Competencia", back_populates="evaluaciones")
    evaluador = relationship("Usuario", foreign_keys=[evaluador_id])

    def __repr__(self):
        return f"<EvaluacionCompetencia(usuario={self.usuario_id}, competencia={self.competencia_id}, nivel={self.nivel})>"
