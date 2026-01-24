"""
Modelos de usuarios, áreas, roles y permisos
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Area(BaseModel):
    """Modelo de áreas organizacionales"""
    __tablename__ = "areas"
    
    codigo = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Relaciones
    usuarios = relationship("Usuario", back_populates="area", foreign_keys="[Usuario.area_id]")
    procesos = relationship("Proceso", back_populates="area")
    objetivos_calidad = relationship("ObjetivoCalidad", back_populates="area")
    asignaciones = relationship("Asignacion", back_populates="area")
    
    def __repr__(self):
        return f"<Area(codigo={self.codigo}, nombre={self.nombre})>"


class Usuario(BaseModel):
    """Modelo de usuarios del sistema"""
    __tablename__ = "usuarios"
    
    documento = Column(Integer, nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    segundo_nombre = Column(String(100), nullable=True)
    primer_apellido = Column(String(100), nullable=False)
    segundo_apellido = Column(String(100), nullable=True)
    correo_electronico = Column(String(254), nullable=False)
    nombre_usuario = Column(String(150), nullable=False, unique=True)
    contrasena_hash = Column(Text, nullable=False)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    foto_url = Column(String(500), nullable=True, comment="URL de la foto de perfil del usuario")
    
    # Relaciones
    area = relationship("Area", back_populates="usuarios", foreign_keys=[area_id])
    roles = relationship("UsuarioRol", back_populates="usuario")
    
    # Relaciones inversas (como creador/responsable)
    procesos_creados = relationship("Proceso", back_populates="creador", foreign_keys="[Proceso.creado_por]")
    procesos_responsable = relationship("Proceso", back_populates="responsable", foreign_keys="[Proceso.responsable_id]")
    documentos_creados = relationship("Documento", back_populates="creador", foreign_keys="[Documento.creado_por]")
    documentos_aprobados = relationship("Documento", back_populates="aprobador", foreign_keys="[Documento.aprobado_por]")
    versiones_documentos = relationship("VersionDocumento", back_populates="creador")
    etapas_responsable = relationship("EtapaProceso", back_populates="responsable")
    instancias_iniciadas = relationship("InstanciaProceso", back_populates="iniciador")
    participaciones = relationship("ParticipanteProceso", back_populates="usuario")
    indicadores_responsable = relationship("Indicador", back_populates="responsable_medicion")
    no_conformidades_detectadas = relationship("NoConformidad", back_populates="detector", foreign_keys="[NoConformidad.detectado_por]")
    no_conformidades_responsable = relationship("NoConformidad", back_populates="responsable", foreign_keys="[NoConformidad.responsable_id]")
    acciones_correctivas = relationship("AccionCorrectiva", back_populates="responsable", foreign_keys="[AccionCorrectiva.responsable_id]")
    acciones_verificadas = relationship("AccionCorrectiva", back_populates="verificador", foreign_keys="[AccionCorrectiva.verificado_por]")
    auditorias_lider = relationship("Auditoria", back_populates="auditor_lider", foreign_keys="[Auditoria.auditor_lider_id]")
    auditorias_creadas = relationship("Auditoria", back_populates="creador", foreign_keys="[Auditoria.creado_por]")
    hallazgos_responsable = relationship("HallazgoAuditoria", back_populates="responsable_respuesta")
    riesgos_responsable = relationship("Riesgo", back_populates="responsable")
    controles_responsable = relationship("ControlRiesgo", back_populates="responsable")
    objetivos_calidad_responsable = relationship("ObjetivoCalidad", back_populates="responsable")
    seguimientos_responsable = relationship("SeguimientoObjetivo", back_populates="responsable")
    capacitaciones_responsable = relationship("Capacitacion", back_populates="responsable")
    asistencias = relationship("AsistenciaCapacitacion", back_populates="usuario")
    acciones_procesos_responsable = relationship("AccionProceso", back_populates="responsable")
    respuestas_formularios = relationship("RespuestaFormulario", back_populates="usuario_respuesta")
    tickets_solicitados = relationship("Ticket", back_populates="solicitante", foreign_keys="[Ticket.solicitante_id]")
    tickets_asignados = relationship("Ticket", back_populates="asignado", foreign_keys="[Ticket.asignado_a]")
    notificaciones = relationship("Notificacion", back_populates="usuario")
    asignaciones = relationship("Asignacion", back_populates="usuario")
    
    # Índices
    __table_args__ = (
        Index('usuarios_documento', 'documento'),
        Index('usuarios_nombre_usuario', 'nombre_usuario'),
        Index('usuarios_correo_electronico', 'correo_electronico'),
        Index('usuarios_area_id', 'area_id'),
    )
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        nombres = [self.nombre, self.segundo_nombre] if self.segundo_nombre else [self.nombre]
        apellidos = [self.primer_apellido, self.segundo_apellido] if self.segundo_apellido else [self.primer_apellido]
        return f"{' '.join(nombres)} {' '.join(apellidos)}"
    
    @property
    def permisos_codes(self):
        """Retorna una lista de códigos de permisos únicos del usuario"""
        codigos = set()
        for ur in self.roles:
            for rp in ur.rol.permisos:
                if rp.permiso:
                    codigos.add(rp.permiso.codigo)
        return list(codigos)
    
    def __repr__(self):
        return f"<Usuario(nombre_usuario={self.nombre_usuario}, documento={self.documento})>"


class Rol(BaseModel):
    """Modelo de roles del sistema"""
    __tablename__ = "roles"
    
    nombre = Column(String(150), nullable=False)
    clave = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Relaciones
    usuarios = relationship("UsuarioRol", back_populates="rol")
    permisos = relationship("RolPermiso", back_populates="rol")
    
    # Nota: creado_en está heredado de BaseModel, no necesita actualizado_en
    def __repr__(self):
        return f"<Rol(nombre={self.nombre}, clave={self.clave})>"


class Permiso(BaseModel):
    """Modelo de permisos del sistema"""
    __tablename__ = "permisos"
    
    nombre = Column(String(200), nullable=False)
    codigo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Relaciones
    roles = relationship("RolPermiso", back_populates="permiso")
    
    # Nota: creado_en está heredado de BaseModel, no necesita actualizado_en
    def __repr__(self):
        return f"<Permiso(nombre={self.nombre}, codigo={self.codigo})>"


class UsuarioRol(BaseModel):
    """Tabla intermedia usuarios-roles"""
    __tablename__ = "usuario_roles"
    
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    rol_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="roles")
    rol = relationship("Rol", back_populates="usuarios")
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('usuario_id', 'rol_id', name='usuario_roles_unique_constraint'),
    )
    
    # Nota: solo tiene creado_en, no actualizado_en
    def __repr__(self):
        return f"<UsuarioRol(usuario_id={self.usuario_id}, rol_id={self.rol_id})>"


class RolPermiso(BaseModel):
    """Tabla intermedia roles-permisos"""
    __tablename__ = "rol_permisos"
    
    rol_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    permiso_id = Column(UUID(as_uuid=True), ForeignKey("permisos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    
    # Relaciones
    rol = relationship("Rol", back_populates="permisos")
    permiso = relationship("Permiso", back_populates="roles")
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('rol_id', 'permiso_id', name='rol_permisos_unique_constraint'),
    )
    
    # Nota: solo tiene creado_en, no actualizado_en
    def __repr__(self):
        return f"<RolPermiso(rol_id={self.rol_id}, permiso_id={self.permiso_id})>"
