"""
Modelos de capacitación y asistencia
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, Numeric, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Capacitacion(BaseModel):
    """Modelo de capacitaciones"""
    __tablename__ = "capacitaciones"
    
    codigo = Column(String(100), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo_capacitacion = Column(String(50), nullable=False)
    modalidad = Column(String(50), nullable=False)  # Presencial, Virtual, Mixta
    duracion_horas = Column(Integer, nullable=True)
    instructor = Column(String(200), nullable=True)
    fecha_programada = Column(DateTime(timezone=True), nullable=True)
    fecha_inicio = Column(DateTime(timezone=True), nullable=True)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    fecha_cierre_asistencia = Column(DateTime(timezone=True), nullable=True)
    fecha_realizacion = Column(DateTime(timezone=True), nullable=True)
    lugar = Column(String(200), nullable=True)
    estado = Column(String(50), nullable=False, default='programada')
    objetivo = Column(Text, nullable=True)
    contenido = Column(Text, nullable=True)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    aplica_todas_areas = Column(Boolean, nullable=False, default=False)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    relacionada_con_hallazgo_id = Column(UUID(as_uuid=True), ForeignKey("hallazgo_auditorias.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    relacionada_con_riesgo_id = Column(UUID(as_uuid=True), ForeignKey("riesgos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    archivo_evidencia = Column(Text, nullable=True)
    
    # Relaciones
    responsable = relationship("Usuario", back_populates="capacitaciones_responsable")
    area = relationship("Area")
    asistencias = relationship("AsistenciaCapacitacion", back_populates="capacitacion")
    
    # Índices
    __table_args__ = (
        Index('capacitaciones_codigo', 'codigo'),
        Index('capacitaciones_estado', 'estado'),
    )
    
    def __repr__(self):
        return f"<Capacitacion(codigo={self.codigo}, nombre={self.nombre}, estado={self.estado})>"


class AsistenciaCapacitacion(BaseModel):
    """Modelo de asistencia a capacitaciones"""
    __tablename__ = "asistencia_capacitaciones"
    
    capacitacion_id = Column(UUID(as_uuid=True), ForeignKey("capacitaciones.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    asistio = Column(Boolean, nullable=False, default=False)
    calificacion = Column(Numeric(3, 1), nullable=True)  # Calificación 0.0 a 100.0
    observaciones = Column(Text, nullable=True)
    certificado = Column(Boolean, nullable=False, default=False)
    fecha_registro = Column(DateTime(timezone=True), nullable=False)
    fecha_asistencia = Column(DateTime(timezone=True), nullable=True)
    evaluacion_aprobada = Column(Boolean, nullable=True)
    
    # Relaciones
    capacitacion = relationship("Capacitacion", back_populates="asistencias")
    usuario = relationship("Usuario", back_populates="asistencias")
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('capacitacion_id', 'usuario_id', name='asistencia_capacitaciones_unique_constraint'),
    )
    
    # Nota: solo tiene creado_en
    def __repr__(self):
        return f"<AsistenciaCapacitacion(capacitacion_id={self.capacitacion_id}, usuario_id={self.usuario_id}, asistio={self.asistio})>"
