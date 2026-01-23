"""
Modelos de gestión de calidad (indicadores, no conformidades, objetivos)
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Indicador(BaseModel):
    """Modelo de indicadores de desempeño"""
    __tablename__ = "indicadores"
    
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    codigo = Column(String(100), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    unidad_medida = Column(String(50), nullable=True)
    meta = Column(Numeric(10, 2), nullable=True)
    frecuencia_medicion = Column(String(50), nullable=False, default='mensual')
    responsable_medicion_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    activo = Column(Integer, nullable=False, default=True)
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="indicadores")
    responsable_medicion = relationship("Usuario", back_populates="indicadores_responsable")
    
    # Índices
    __table_args__ = (
        Index('indicadores_codigo', 'codigo'),
        Index('indicadores_proceso_id', 'proceso_id'),
    )
    
    def __repr__(self):
        return f"<Indicador(codigo={self.codigo}, nombre={self.nombre})>"


class NoConformidad(BaseModel):
    """Modelo de no conformidades"""
    __tablename__ = "no_conformidades"
    
    codigo = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=False)
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    tipo = Column(String(50), nullable=False)
    fuente = Column(String(100), nullable=False)
    detectado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_deteccion = Column(BaseModel.creado_en.type, nullable=False)
    estado = Column(String(50), nullable=False, default='abierta')
    analisis_causa = Column(Text, nullable=True)
    plan_accion = Column(Text, nullable=True)
    fecha_cierre = Column(BaseModel.creado_en.type, nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="no_conformidades")
    detector = relationship("Usuario", back_populates="no_conformidades_detectadas", foreign_keys=[detectado_por])
    responsable = relationship("Usuario", back_populates="no_conformidades_responsable", foreign_keys=[responsable_id])
    acciones_correctivas = relationship("AccionCorrectiva", back_populates="no_conformidad")
    
    # Índices
    __table_args__ = (
        Index('no_conformidades_codigo', 'codigo'),
        Index('no_conformidades_proceso_id', 'proceso_id'),
        Index('no_conformidades_estado', 'estado'),
    )
    
    def __repr__(self):
        return f"<NoConformidad(codigo={self.codigo}, estado={self.estado})>"


class AccionCorrectiva(BaseModel):
    """Modelo de acciones correctivas y preventivas"""
    __tablename__ = "acciones_correctivas"
    
    no_conformidad_id = Column(UUID(as_uuid=True), ForeignKey("no_conformidades.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    codigo = Column(String(50), nullable=False, unique=True)
    tipo = Column(String(50), nullable=True)
    descripcion = Column(Text, nullable=True)
    analisis_causa_raiz = Column(Text, nullable=True)
    plan_accion = Column(Text, nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_compromiso = Column(Date, nullable=True)
    fecha_implementacion = Column(Date, nullable=True)
    estado = Column(String(50), nullable=True)
    eficacia_verificada = Column(Integer, nullable=True)
    verificado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_verificacion = Column(Date, nullable=True)
    observacion = Column(Text, nullable=True)
    
    # Relaciones
    no_conformidad = relationship("NoConformidad", back_populates="acciones_correctivas")
    responsable = relationship("Usuario", back_populates="acciones_correctivas", foreign_keys=[responsable_id])
    verificador = relationship("Usuario", back_populates="acciones_verificadas", foreign_keys=[verificado_por])
    
    def __repr__(self):
        return f"<AccionCorrectiva(codigo={self.codigo}, estado={self.estado})>"


class ObjetivoCalidad(BaseModel):
    """Modelo de objetivos de calidad"""
    __tablename__ = "objetivos_calidad"
    
    codigo = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=False)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_inicio = Column(BaseModel.creado_en.type, nullable=False)
    fecha_fin = Column(BaseModel.creado_en.type, nullable=False)
    estado = Column(String(50), nullable=False, default='planificado')
    progreso = Column(Numeric(5, 2), nullable=False, default=0)
    
    # Relaciones
    area = relationship("Area", back_populates="objetivos_calidad")
    responsable = relationship("Usuario", back_populates="objetivos_calidad_responsable")
    seguimientos = relationship("SeguimientoObjetivo", back_populates="objetivo_calidad")
    
    # Índices
    __table_args__ = (
        Index('objetivos_calidad_codigo', 'codigo'),
    )
    
    def __repr__(self):
        return f"<ObjetivoCalidad(codigo={self.codigo}, progreso={self.progreso}%)>"


class SeguimientoObjetivo(BaseModel):
    """Modelo de seguimiento de objetivos de calidad"""
    __tablename__ = "seguimiento_objetivos"
    
    objetivo_calidad_id = Column(UUID(as_uuid=True), ForeignKey("objetivos_calidad.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    fecha_seguimiento = Column(BaseModel.creado_en.type, nullable=False)
    valor_actual = Column(Numeric(10, 2), nullable=True)
    observaciones = Column(Text, nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    objetivo_calidad = relationship("ObjetivoCalidad", back_populates="seguimientos")
    responsable = relationship("Usuario", back_populates="seguimientos_responsable")
    
    # Nota: solo tiene creado_en
    def __repr__(self):
        return f"<SeguimientoObjetivo(objetivo_id={self.objetivo_calidad_id}, fecha={self.fecha_seguimiento})>"
