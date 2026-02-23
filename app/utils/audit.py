"""
Utilidades de auditoría de cambios.
"""
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from ..models.audit_log import AuditLog


AUDIT_ACTIONS = {"CREATE", "UPDATE", "DELETE", "CERRAR", "VERIFICAR"}


def registrar_auditoria(
    db: Session,
    tabla: str,
    registro_id: UUID,
    accion: str,
    usuario_id: Optional[UUID] = None,
    cambios: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Registra un evento de auditoría simple en la tabla audit_log."""
    accion_normalizada = accion.upper().strip()
    if accion_normalizada not in AUDIT_ACTIONS:
        accion_normalizada = "UPDATE"

    entry = AuditLog(
        tabla=tabla,
        registro_id=registro_id,
        accion=accion_normalizada,
        usuario_id=usuario_id,
        cambios_json=jsonable_encoder(cambios) if cambios else None,
    )
    db.add(entry)
    return entry
