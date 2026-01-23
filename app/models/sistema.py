"""
Modelos del sistema (tickets, notificaciones, configuraciones, formularios, asignaciones)
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Ticket(BaseModel):
    """Modelo de sistema de tickets/solicitudes"""
    __tablename__ = "tickets"
    
    codigo = Column(String(100), nullable=False, unique=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    categoria = Column(String(100), nullable=False)
    prioridad = Column(String(50), nullable=False, default='media')
    estado = Column(String(50), nullable=False, default='abierto')
    solicitante_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    asignado_a = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    fecha_limite = Column(BaseModel.creado_en.type, nullable=True)
    fecha_resolucion = Column(BaseModel.creado_en.type, nullable=True)
    solucion = Column(Text, nullable=True)
    tiempo_resolucion = Column(Integer, nullable=True)  # En minutos
    satisfaccion_cliente = Column(Integer, nullable=True)  # Escala 1-5
    
    # Relaciones
    solicitante = relationship("Usuario", back_populates="tickets_solicitados", foreign_keys=[solicitante_id])
    asignado = relationship("Usuario", back_populates="tickets_asignados", foreign_keys=[asignado_a])
    
    # Índices
    __table_args__ = (
        Index('tickets_codigo', 'codigo'),
        Index('tickets_estado', 'estado'),
    )
    
    def __repr__(self):
        return f"<Ticket(codigo={self.codigo}, estado={self.estado}, prioridad={self.prioridad})>"


class Notificacion(BaseModel):
    """Modelo de notificaciones a usuarios"""
    __tablename__ = "notificaciones"
    
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(String(50), nullable=False)
    leida = Column(Boolean, nullable=False, default=False)
    fecha_lectura = Column(BaseModel.creado_en.type, nullable=True)
    referencia_tipo = Column(String(50), nullable=True)  # Tipo de entidad referenciada
    referencia_id = Column(UUID(as_uuid=True), nullable=True)  # ID de la entidad referenciada
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="notificaciones")
    
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


class CampoFormulario(BaseModel):
    """Modelo de campos dinámicos de formularios"""
    __tablename__ = "campo_formularios"
    
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    nombre = Column(String(200), nullable=False)
    etiqueta = Column(String(200), nullable=False)
    tipo_campo = Column(String(50), nullable=False)  # text, number, select, date, etc.
    requerido = Column(Boolean, nullable=False, default=False)
    opciones = Column(JSON, nullable=True)  # Para campos tipo select, checkbox, etc.
    orden = Column(Integer, nullable=False, default=1)
    activo = Column(Boolean, nullable=False, default=True)
    validaciones = Column(JSON, nullable=True)  # Reglas de validación
    
    # Relaciones
    proceso = relationship("Proceso", back_populates="campos_formulario")
    respuestas = relationship("RespuestaFormulario", back_populates="campo")
    
    def __repr__(self):
        return f"<CampoFormulario(nombre={self.nombre}, tipo={self.tipo_campo})>"


class RespuestaFormulario(BaseModel):
    """Modelo de respuestas a formularios dinámicos"""
    __tablename__ = "respuesta_formularios"
    
    campo_formulario_id = Column(UUID(as_uuid=True), ForeignKey("campo_formularios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    instancia_proceso_id = Column(UUID(as_uuid=True), ForeignKey("instancia_procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    valor = Column(Text, nullable=True)
    archivo_adjunto = Column(Text, nullable=True)  # URL o path del archivo
    usuario_respuesta_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    campo = relationship("CampoFormulario", back_populates="respuestas")
    instancia = relationship("InstanciaProceso", back_populates="respuestas_formularios")
    usuario_respuesta = relationship("Usuario", back_populates="respuestas_formularios")
    
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
    usuario = relationship("Usuario", back_populates="asignaciones")
    
    # Constraint único e índices
    __table_args__ = (
        UniqueConstraint('area_id', 'usuario_id', name='asignaciones_area_usuario_unique'),
        Index('asignaciones_area_id_idx', 'area_id'),
        Index('asignaciones_usuario_id_idx', 'usuario_id'),
    )
    
    def __repr__(self):
        return f"<Asignacion(area_id={self.area_id}, usuario_id={self.usuario_id}, principal={self.es_principal})>"
