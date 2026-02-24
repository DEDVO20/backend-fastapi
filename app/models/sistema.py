"""
Modelos del sistema (tickets, notificaciones, configuraciones, formularios, asignaciones)
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, JSON, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel




class Notificacion(BaseModel):
    """Modelo de notificaciones a usuarios"""
    __tablename__ = "notificaciones"
    
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(String(50), nullable=False)
    leida = Column(Boolean, nullable=False, default=False)
    fecha_lectura = Column(DateTime(timezone=True), nullable=True)
    referencia_tipo = Column(String(50), nullable=True)  # Tipo de entidad referenciada
    referencia_id = Column(UUID(as_uuid=True), nullable=True)  # ID de la entidad referenciada
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="notificaciones", foreign_keys=[usuario_id])
    
    # Índices
    __table_args__ = (
        Index('notificaciones_usuario_id', 'usuario_id'),
        Index('notificaciones_leida', 'leida'),
    )
    
    # Nota: solo tiene creado_en
    def __repr__(self):
        return f"<Notificacion(usuario_id={self.usuario_id}, leida={self.leida})>"


class Configuracion(BaseModel):
    """Modelo de configuraciones del sistema"""
    __tablename__ = "configuraciones"
    
    clave = Column(String(100), nullable=False, unique=True)
    valor = Column(Text, nullable=True)
    descripcion = Column(Text, nullable=True)
    tipo_dato = Column(String(50), nullable=False, default='string')
    categoria = Column(String(100), nullable=True)
    activa = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<Configuracion(clave={self.clave}, activa={self.activa})>"


class FormularioDinamico(BaseModel):
    """Modelo de formularios dinámicos configurables"""
    __tablename__ = "formularios_dinamicos"

    codigo = Column(String(100), nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    modulo = Column(String(50), nullable=False, default="general")
    entidad_tipo = Column(String(50), nullable=False, default="general")
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    estado_workflow = Column(String(30), nullable=False, default="borrador")  # borrador|revision|aprobado|obsoleto
    vigente_desde = Column(DateTime(timezone=True), nullable=True)
    vigente_hasta = Column(DateTime(timezone=True), nullable=True)
    aprobado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_aprobacion = Column(DateTime(timezone=True), nullable=True)
    parent_formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios_dinamicos.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)

    # Relaciones
    proceso = relationship("Proceso", back_populates="formularios_dinamicos")
    campos = relationship("CampoFormulario", back_populates="formulario", cascade="all, delete-orphan")
    aprobador = relationship("Usuario", foreign_keys=[aprobado_por])
    parent_formulario = relationship("FormularioDinamico", remote_side="FormularioDinamico.id", uselist=False)

    __table_args__ = (
        Index("formularios_dinamicos_codigo_idx", "codigo"),
        Index("formularios_dinamicos_modulo_idx", "modulo"),
        Index("formularios_dinamicos_entidad_tipo_idx", "entidad_tipo"),
    )

    def __repr__(self):
        return f"<FormularioDinamico(codigo={self.codigo}, modulo={self.modulo})>"


class CampoFormulario(BaseModel):
    """Modelo de campos dinámicos de formularios"""
    __tablename__ = "campo_formularios"

    formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios_dinamicos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    nombre = Column(String(200), nullable=False)
    etiqueta = Column(String(200), nullable=False)
    tipo_campo = Column(String(50), nullable=False)  # text, number, select, date, etc.
    requerido = Column(Boolean, nullable=False, default=False)
    opciones = Column(JSON, nullable=True)  # Para campos tipo select, checkbox, etc.
    orden = Column(Integer, nullable=False, default=1)
    activo = Column(Boolean, nullable=False, default=True)
    validaciones = Column(JSON, nullable=True)  # Reglas de validación
    seccion_iso = Column(String(100), nullable=True)  # Contexto, Liderazgo, etc.
    clausula_iso = Column(String(50), nullable=True)
    subclausula_iso = Column(String(50), nullable=True)
    evidencia_requerida = Column(Boolean, nullable=False, default=False)
    
    # Relaciones
    formulario = relationship("FormularioDinamico", back_populates="campos")
    proceso = relationship("Proceso", back_populates="campos_formulario")
    respuestas = relationship("RespuestaFormulario", back_populates="campo")
    
    def __repr__(self):
        return f"<CampoFormulario(nombre={self.nombre}, tipo={self.tipo_campo})>"


class RespuestaFormulario(BaseModel):
    """Modelo de respuestas a formularios dinámicos"""
    __tablename__ = "respuesta_formularios"
    
    campo_formulario_id = Column(UUID(as_uuid=True), ForeignKey("campo_formularios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    instancia_proceso_id = Column(UUID(as_uuid=True), ForeignKey("instancia_procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    auditoria_id = Column(UUID(as_uuid=True), ForeignKey("auditorias.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    valor = Column(Text, nullable=True)
    archivo_adjunto = Column(Text, nullable=True)  # URL o path del archivo
    usuario_respuesta_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    evidencia_hash = Column(String(128), nullable=True)
    evidencia_fecha = Column(DateTime(timezone=True), nullable=True)
    evidencia_usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    campo = relationship("CampoFormulario", back_populates="respuestas")
    instancia = relationship("InstanciaProceso", back_populates="respuestas_formularios")
    auditoria = relationship("Auditoria", back_populates="respuestas_formularios")
    usuario_respuesta = relationship("Usuario", back_populates="respuestas_formularios", foreign_keys=[usuario_respuesta_id])
    evidencia_usuario = relationship("Usuario", foreign_keys=[evidencia_usuario_id])
    
    def __repr__(self):
        return f"<RespuestaFormulario(campo_id={self.campo_formulario_id}, instancia_id={self.instancia_proceso_id})>"


class Asignacion(BaseModel):
    """Modelo de asignaciones de usuarios a áreas"""
    __tablename__ = "asignaciones"
    
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    es_principal = Column(Boolean, nullable=False, default=False, comment="Indica si es el responsable principal del área")
    
    # Relaciones
    area = relationship("Area", back_populates="asignaciones")
    usuario = relationship("Usuario", back_populates="asignaciones", foreign_keys=[usuario_id])
    
    # Constraint único e índices
    __table_args__ = (
        UniqueConstraint('area_id', 'usuario_id', name='asignaciones_area_usuario_unique'),
        Index('asignaciones_area_id_idx', 'area_id'),
        Index('asignaciones_usuario_id_idx', 'usuario_id'),
    )
    
    def __repr__(self):
        return f"<Asignacion(area_id={self.area_id}, usuario_id={self.usuario_id}, principal={self.es_principal})>"
