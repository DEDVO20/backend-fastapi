"""
Modelos de gestión de riesgos y controles.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, Date, DateTime
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
    etapa_proceso_id = Column(UUID(as_uuid=True), ForeignKey("etapa_procesos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    probabilidad = Column(Integer, nullable=True)  # Escala 1-5
    impacto = Column(Integer, nullable=True)  # Escala 1-5
    nivel_riesgo = Column(String(50), nullable=True)  # Bajo, Medio, Alto, Crítico
    nivel_residual = Column(Integer, nullable=True)  # Nivel residual ajustado por controles/factor humano
    causas = Column(Text, nullable=True)
    consecuencias = Column(Text, nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    estado = Column(String(50), nullable=False, default='activo')
    fecha_identificacion = Column(Date, nullable=True)  # Fecha en que se identificó el riesgo
    fecha_revision = Column(Date, nullable=True)  # Fecha de última revisión del riesgo
    tratamiento = Column(Text, nullable=True)  # Plan de tratamiento/mitigación del riesgo
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="riesgos")
    etapa_proceso = relationship("EtapaProceso")
    responsable = relationship("Usuario", back_populates="riesgos_responsable", foreign_keys=[responsable_id])
    controles = relationship("ControlRiesgo", back_populates="riesgo")
    historial_evaluaciones = relationship("EvaluacionRiesgoHistorial", back_populates="riesgo", cascade="all, delete-orphan")
    competencias_criticas = relationship(
        "RiesgoCompetenciaCritica",
        back_populates="riesgo",
        cascade="all, delete-orphan",
    )
    
    # Índices
    __table_args__ = (
        Index('riesgos_codigo', 'codigo'),
        Index('riesgos_proceso_id', 'proceso_id'),
        Index('riesgos_etapa_proceso_id', 'etapa_proceso_id'),
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
    responsable = relationship("Usuario", back_populates="controles_responsable", foreign_keys=[responsable_id])
    
    def __repr__(self):
        return f"<ControlRiesgo(riesgo_id={self.riesgo_id}, tipo={self.tipo_control})>"


class EvaluacionRiesgoHistorial(BaseModel):
    __tablename__ = "evaluacion_riesgo_historial"

    riesgo_id = Column(UUID(as_uuid=True), ForeignKey("riesgos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    probabilidad_anterior = Column(Integer, nullable=True)
    impacto_anterior = Column(Integer, nullable=True)
    nivel_anterior = Column(String(50), nullable=True)
    probabilidad_nueva = Column(Integer, nullable=False)
    impacto_nueva = Column(Integer, nullable=False)
    nivel_nuevo = Column(String(50), nullable=False)
    justificacion = Column(Text, nullable=True)
    evaluado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_evaluacion = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    riesgo = relationship("Riesgo", back_populates="historial_evaluaciones")
    evaluador = relationship("Usuario", foreign_keys=[evaluado_por])

    def __repr__(self):
        return f"<EvaluacionRiesgoHistorial(riesgo_id={self.riesgo_id}, nivel={self.nivel_nuevo})>"


class RiesgoCompetenciaCritica(BaseModel):
    """Competencias mínimas críticas para un riesgo."""
    __tablename__ = "riesgo_competencias_criticas"

    riesgo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("riesgos.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    competencia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competencias.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    nivel_minimo = Column(String(50), nullable=False)

    riesgo = relationship("Riesgo", back_populates="competencias_criticas")
    competencia = relationship("Competencia")

    __table_args__ = (
        Index("idx_riesgo_comp_crit_riesgo", "riesgo_id"),
        Index("idx_riesgo_comp_crit_competencia", "competencia_id"),
        Index("idx_riesgo_comp_crit_nivel", "nivel_minimo"),
    )

    def __repr__(self):
        return f"<RiesgoCompetenciaCritica(riesgo={self.riesgo_id}, competencia={self.competencia_id})>"
