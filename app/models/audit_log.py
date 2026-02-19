"""
Modelo de auditoría transversal de cambios CRUD.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_log"

    tabla = Column(String(100), nullable=False)
    registro_id = Column(UUID(as_uuid=True), nullable=False)
    accion = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    cambios_json = Column(JSONB, nullable=True)
    fecha = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_log_tabla", "tabla"),
        Index("idx_audit_log_registro_id", "registro_id"),
        Index("idx_audit_log_fecha", "fecha"),
    )

    def __repr__(self):
        return f"<AuditLog(tabla={self.tabla}, accion={self.accion}, registro_id={self.registro_id})>"
