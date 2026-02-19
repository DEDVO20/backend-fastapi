"""
Modelos de gestión de calidad (indicadores, no conformidades, objetivos).
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, Numeric, Date, DateTime, Boolean
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
    responsable_medicion = relationship("Usuario", back_populates="indicadores_responsable", foreign_keys=[responsable_medicion_id])
    mediciones = relationship("MedicionIndicador", back_populates="indicador", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('indicadores_codigo', 'codigo'),
        Index('indicadores_proceso_id', 'proceso_id'),
    )
    
    def __repr__(self):
        return f"<Indicador(codigo={self.codigo}, nombre={self.nombre})>"


class MedicionIndicador(BaseModel):
    __tablename__ = "mediciones_indicador"

    indicador_id = Column(UUID(as_uuid=True), ForeignKey("indicadores.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    periodo = Column(String(20), nullable=False)  # 2026-01, 2026-Q1
    valor = Column(Numeric(10, 2), nullable=False)
    meta = Column(Numeric(10, 2), nullable=True)
    cumple_meta = Column(Boolean, nullable=True)
    observaciones = Column(Text, nullable=True)
    registrado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)

    indicador = relationship("Indicador", back_populates="mediciones")
    registrador = relationship("Usuario", foreign_keys=[registrado_por])

    __table_args__ = (
        Index("idx_mediciones_indicador_id", "indicador_id"),
        Index("idx_mediciones_indicador_periodo", "periodo"),
    )

    def __repr__(self):
        return f"<MedicionIndicador(indicador_id={self.indicador_id}, periodo={self.periodo}, valor={self.valor})>"


class NoConformidad(BaseModel):
    """Modelo de no conformidades"""
    __tablename__ = "no_conformidades"
    
    codigo = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=False)
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    tipo = Column(String(50), nullable=False)
    fuente = Column(String(100), nullable=False)
    detectado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_deteccion = Column(DateTime(timezone=True), nullable=False)
    gravedad = Column(String(50), nullable=True)
    estado = Column(String(50), nullable=False, default='abierta')
    analisis_causa = Column(Text, nullable=True)
    plan_accion = Column(Text, nullable=True)
    evidencias = Column(Text, nullable=True) # JSON string con URLs de evidencias
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)
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
    implementado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    estado = Column(String(50), nullable=True)
    eficacia_verificada = Column(Integer, nullable=True)
    verificado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_verificacion = Column(Date, nullable=True)
    observacion = Column(Text, nullable=True)
    evidencias = Column(Text, nullable=True)  # JSON string con URLs o descripciones de evidencias
    
    # Relaciones
    no_conformidad = relationship("NoConformidad", back_populates="acciones_correctivas")
    responsable = relationship("Usuario", back_populates="acciones_correctivas", foreign_keys=[responsable_id])
    implementador = relationship("Usuario", back_populates="acciones_implementadas", foreign_keys=[implementado_por])
    verificador = relationship("Usuario", back_populates="acciones_verificadas", foreign_keys=[verificado_por])
    comentarios = relationship("AccionCorrectivaComentario", back_populates="accion_correctiva", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AccionCorrectiva(codigo={self.codigo}, estado={self.estado})>"


class ObjetivoCalidad(BaseModel):
    """Modelo de objetivos de calidad"""
    __tablename__ = "objetivos_calidad"
    
    codigo = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=False)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=False)
    estado = Column(String(50), nullable=False, default='planificado')
    progreso = Column(Numeric(5, 2), nullable=False, default=0)
    # ISO 9001:2015 Cláusula 6.2 - Campos adicionales
    meta = Column(Text, nullable=True)                          # Qué se hará / meta medible
    indicador = Column(String(255), nullable=True)              # Cómo se evaluarán los resultados
    valor_meta = Column(Numeric(10, 2), nullable=True)          # Valor numérico objetivo
    
    # Relaciones
    area = relationship("Area", back_populates="objetivos_calidad")
    responsable = relationship("Usuario", back_populates="objetivos_calidad_responsable", foreign_keys=[responsable_id])
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
    fecha_seguimiento = Column(DateTime(timezone=True), nullable=False)
    valor_actual = Column(Numeric(10, 2), nullable=True)
    observaciones = Column(Text, nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    objetivo_calidad = relationship("ObjetivoCalidad", back_populates="seguimientos")
    responsable = relationship("Usuario", back_populates="seguimientos_responsable", foreign_keys=[responsable_id])
    
    # Nota: solo tiene creado_en
    def __repr__(self):
        return f"<SeguimientoObjetivo(objetivo_id={self.objetivo_calidad_id}, fecha={self.fecha_seguimiento})>"


class AccionCorrectivaComentario(BaseModel):
    """Modelo de comentarios para acciones correctivas"""
    __tablename__ = "acciones_correctivas_comentarios"
    
    accion_correctiva_id = Column(UUID(as_uuid=True), ForeignKey("acciones_correctivas.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    comentario = Column(Text, nullable=False)
    
    # Relaciones
    accion_correctiva = relationship("AccionCorrectiva", back_populates="comentarios")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    
    def __repr__(self):
        return f"<AccionCorrectivaComentario(id={self.id}, accion_id={self.accion_correctiva_id})>"
