"""
Modelos de auditorías y hallazgos
"""
from sqlalchemy import Column, String, Text, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Auditoria(BaseModel):
    """Modelo de auditorías internas y externas"""
    __tablename__ = "auditorias"
    
    codigo = Column(String(100), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    tipo_auditoria = Column(String(50), nullable=False)
    alcance = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True)
    fecha_planificada = Column(DateTime(timezone=True), nullable=True)
    fecha_inicio = Column(DateTime(timezone=True), nullable=True)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    estado = Column(String(50), nullable=False, default='planificada')
    norma_referencia = Column(String(200), nullable=True)
    equipo_auditor = Column(Text, nullable=True)
    auditor_lider_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    informe_final = Column(Text, nullable=True)
    
    # Relaciones
    auditor_lider = relationship("Usuario", back_populates="auditorias_lider", foreign_keys=[auditor_lider_id])
    creador = relationship("Usuario", back_populates="auditorias_creadas", foreign_keys=[creado_por])
    hallazgos = relationship("HallazgoAuditoria", back_populates="auditoria")
    
    # Índices
    __table_args__ = (
        Index('auditorias_codigo', 'codigo'),
        Index('auditorias_estado', 'estado'),
    )
    
    def __repr__(self):
        return f"<Auditoria(codigo={self.codigo}, nombre={self.nombre}, estado={self.estado})>"


class HallazgoAuditoria(BaseModel):
    """Modelo de hallazgos de auditorías"""
    __tablename__ = "hallazgo_auditorias"
    
    auditoria_id = Column(UUID(as_uuid=True), ForeignKey("auditorias.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    codigo = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_hallazgo = Column(String(50), nullable=False)
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    clausula_norma = Column(String(100), nullable=True)
    evidencia = Column(Text, nullable=True)
    responsable_respuesta_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_respuesta = Column(DateTime(timezone=True), nullable=True)
    estado = Column(String(50), nullable=False, default='abierto')
    
    # Relaciones
    auditoria = relationship("Auditoria", back_populates="hallazgos")
    proceso = relationship("Proceso", back_populates="hallazgos")
    responsable_respuesta = relationship("Usuario", back_populates="hallazgos_responsable")
    
    def __repr__(self):
        return f"<HallazgoAuditoria(codigo={self.codigo}, tipo={self.tipo_hallazgo}, estado={self.estado})>"
