"""
Modelos de documentos y control de versiones
"""
from sqlalchemy import Column, String, Text, ForeignKey, Index, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Documento(BaseModel):
    """Modelo de documentos del sistema"""
    __tablename__ = "documentos"
    
    codigo = Column(String(100), nullable=False, unique=True)
    nombre = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo_documento = Column(String(100), nullable=False)
    ruta_archivo = Column(Text, nullable=True)
    version_actual = Column(String(20), nullable=False, default='1.0')
    estado = Column(String(50), nullable=False, default='borrador')
    fecha_aprobacion = Column(DateTime(timezone=True), nullable=True)
    fecha_vigencia = Column(DateTime(timezone=True), nullable=True)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    revisado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    aprobado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    creador = relationship("Usuario", back_populates="documentos_creados", foreign_keys=[creado_por])
    revisor = relationship("Usuario", back_populates="documentos_revisados", foreign_keys=[revisado_por])
    aprobador = relationship("Usuario", back_populates="documentos_aprobados", foreign_keys=[aprobado_por])
    versiones = relationship("VersionDocumento", back_populates="documento")
    procesos = relationship("DocumentoProceso", back_populates="documento")
    
    # Índices
    __table_args__ = (
        Index('documentos_codigo', 'codigo'),
        Index('documentos_tipo_documento', 'tipo_documento'),
        Index('documentos_estado', 'estado'),
    )
    
    def __repr__(self):
        return f"<Documento(codigo={self.codigo}, nombre={self.nombre}, version={self.version_actual})>"


class VersionDocumento(BaseModel):
    """Modelo de versiones de documentos"""
    __tablename__ = "version_documentos"
    
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    version = Column(String(20), nullable=False)
    descripcion_cambios = Column(Text, nullable=True)
    ruta_archivo = Column(Text, nullable=True)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    documento = relationship("Documento", back_populates="versiones")
    creador = relationship("Usuario", back_populates="versiones_documentos")
    
    # Nota: solo tiene creado_en
    def __repr__(self):
        return f"<VersionDocumento(documento_id={self.documento_id}, version={self.version})>"


class DocumentoProceso(BaseModel):
    """Tabla de relación documentos-procesos"""
    __tablename__ = "documento_procesos"
    
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    proceso_id = Column(UUID(as_uuid=True), ForeignKey("procesos.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    tipo_relacion = Column(String(50), nullable=False, default='asociado')
    
    # Relaciones
    documento = relationship("Documento", back_populates="procesos")
    proceso = relationship("Proceso", back_populates="documentos")
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('documento_id', 'proceso_id', name='documento_procesos_unique_constraint'),
    )
    
    # Nota: solo tiene creado_en
    def __repr__(self):
        return f"<DocumentoProceso(documento_id={self.documento_id}, proceso_id={self.proceso_id})>"
