"""
Modelos de gestión de riesgos y controles
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Riesgo(BaseModel):
    """Modelo de riesgos identificados"""
    __tablename__ = "riesgos"
    
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    codigo = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=False)
    categoria = Column(String(100), nullable=True)
    tipo_riesgo = Column(String(50), nullable=False)
    probabilidad = Column(Integer, nullable=True)  # Escala 1-5
    impacto = Column(Integer, nullable=True)  # Escala 1-5
    nivel_riesgo = Column(String(50), nullable=True)  # Bajo, Medio, Alto, Crítico
    causas = Column(Text, nullable=True)
    consecuencias = Column(Text, nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    estado = Column(String(50), nullable=False, default='activo')
    fecha_identificacion = Column(Date, nullable=True)  # Fecha en que se identificó el riesgo
    fecha_revision = Column(Date, nullable=True)  # Fecha de última revisión del riesgo
    tratamiento = Column(Text, nullable=True)  # Plan de tratamiento/mitigación del riesgo
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="riesgos")
    responsable = relationship("Usuario", back_populates="riesgos_responsable")
    controles = relationship("ControlRiesgo", back_populates="riesgo")
    
    # Índices
    __table_args__ = (
        Index('riesgos_codigo', 'codigo'),
        Index('riesgos_proceso_id', 'proceso_id'),
    )
    
    def __repr__(self):
        return f"<Riesgo(codigo={self.codigo}, nivel={self.nivel_riesgo}, estado={self.estado})>"


class ControlRiesgo(BaseModel):
    """Modelo de controles de riesgos"""
    __tablename__ = "control_riesgos"
    
    riesgo_id = Column(UUID(as_uuid=True), ForeignKey("riesgos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_control = Column(String(50), nullable=False)  # Preventivo, Detectivo, Correctivo
    frecuencia = Column(String(50), nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    efectividad = Column(String(50), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    
    # Relaciones
    riesgo = relationship("Riesgo", back_populates="controles")
    responsable = relationship("Usuario", back_populates="controles_responsable")
    
    def __repr__(self):
        return f"<ControlRiesgo(riesgo_id={self.riesgo_id}, tipo={self.tipo_control})>"
