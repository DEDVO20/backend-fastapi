"""
Modelos de procesos y sus componentes
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, Date, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class Proceso(BaseModel):
    """Modelo de procesos del sistema"""
    __tablename__ = "procesos"
    
    codigo = Column(String(100), nullable=False, unique=True)
    nombre = Column(String(300), nullable=False)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    objetivo = Column(Text, nullable=True)
    alcance = Column(Text, nullable=True)
    etapa_phva = Column(String(50), nullable=True)  # Planear, Hacer, Verificar, Actuar
    restringido = Column(Boolean, default=False)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    tipo_proceso = Column(String(50), nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    estado = Column(String(50), nullable=False, default='activo')
    version = Column(String(20), nullable=True)
    fecha_aprobacion = Column(Date, nullable=True)
    proxima_revision = Column(Date, nullable=True)
    
    # Campos adicionales ISO 9001:2015
    entradas = Column(Text, nullable=True)  # Entradas del proceso
    salidas = Column(Text, nullable=True)  # Salidas/productos del proceso
    recursos_necesarios = Column(Text, nullable=True)  # Recursos requeridos
    criterios_desempeno = Column(Text, nullable=True)  # Criterios y métodos de medición
    riesgos_oportunidades = Column(Text, nullable=True)  # Riesgos y oportunidades
    
    # Relaciones
    area = relationship("Area", back_populates="procesos")
    creador = relationship("Usuario", back_populates="procesos_creados", foreign_keys=[creado_por])
    responsable = relationship("Usuario", back_populates="procesos_responsable", foreign_keys=[responsable_id])
    documentos = relationship("DocumentoProceso", back_populates="proceso")
    etapas = relationship("EtapaProceso", back_populates="proceso")
    instancias = relationship("InstanciaProceso", back_populates="proceso")
    indicadores = relationship("Indicador", back_populates="proceso")
    no_conformidades = relationship("NoConformidad", back_populates="proceso")
    hallazgos = relationship("HallazgoAuditoria", back_populates="proceso")
    riesgos = relationship("Riesgo", back_populates="proceso")
    acciones = relationship("AccionProceso", back_populates="proceso")
    formularios_dinamicos = relationship("FormularioDinamico", back_populates="proceso")
    campos_formulario = relationship("CampoFormulario", back_populates="proceso")
    
    # Índices
    __table_args__ = (
        Index('procesos_codigo', 'codigo'),
        Index('procesos_area_id', 'area_id'),
        Index('procesos_estado', 'estado'),
    )
    
    def __repr__(self):
        return f"<Proceso(codigo={self.codigo}, nombre={self.nombre})>"


class EtapaProceso(BaseModel):
    """Modelo de etapas de procesos"""
    __tablename__ = "etapa_procesos"
    
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    orden = Column(Integer, nullable=False, default=1)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    tiempo_estimado = Column(Integer, nullable=True)  # En minutos u horas
    activa = Column(Boolean, nullable=False, default=True)
    
    # Campos adicionales ISO 9001
    criterios_aceptacion = Column(Text, nullable=True)  # Criterios para completar la etapa
    documentos_requeridos = Column(Text, nullable=True)  # Documentos necesarios
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="etapas")
    responsable = relationship("Usuario", back_populates="etapas_responsable")
    
    def __repr__(self):
        return f"<EtapaProceso(nombre={self.nombre}, orden={self.orden})>"


class InstanciaProceso(BaseModel):
    """Modelo de instancias de ejecución de procesos"""
    __tablename__ = "instancia_procesos"
    
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    codigo_instancia = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    estado = Column(String(50), nullable=False, default='iniciado')
    fecha_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    iniciado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="instancias")
    iniciador = relationship("Usuario", back_populates="instancias_iniciadas")
    participantes = relationship("ParticipanteProceso", back_populates="instancia")
    respuestas_formularios = relationship("RespuestaFormulario", back_populates="instancia")
    
    def __repr__(self):
        return f"<InstanciaProceso(codigo={self.codigo_instancia}, estado={self.estado})>"


class ParticipanteProceso(BaseModel):
    """Modelo de participantes en instancias de procesos"""
    __tablename__ = "participante_procesos"
    
    instancia_proceso_id = Column(UUID(as_uuid=True), ForeignKey("instancia_procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    rol_participacion = Column(String(100), nullable=False)
    fecha_asignacion = Column(DateTime(timezone=True), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    
    # Relaciones
    instancia = relationship("InstanciaProceso", back_populates="participantes")
    usuario = relationship("Usuario", back_populates="participaciones")
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('instancia_proceso_id', 'usuario_id', name='participante_procesos_unique_constraint'),
    )
    
    # Nota: solo tiene creado_en
    def __repr__(self):
        return f"<ParticipanteProceso(instancia={self.instancia_proceso_id}, usuario={self.usuario_id})>"


class AccionProceso(BaseModel):
    """Modelo de acciones de mejora en procesos"""
    __tablename__ = "accion_procesos"
    
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    codigo = Column(String(100), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo_accion = Column(String(50), nullable=False)
    origen = Column(String(100), nullable=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_planificada = Column(DateTime(timezone=True), nullable=True)
    fecha_implementacion = Column(DateTime(timezone=True), nullable=True)
    fecha_verificacion = Column(DateTime(timezone=True), nullable=True)
    estado = Column(String(50), nullable=False, default='planificada')
    efectividad = Column(String(50), nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="acciones")
    responsable = relationship("Usuario", back_populates="acciones_procesos_responsable")
    
    def __repr__(self):
        return f"<AccionProceso(codigo={self.codigo}, nombre={self.nombre})>"
