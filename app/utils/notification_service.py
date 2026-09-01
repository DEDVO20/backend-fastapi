"""
Servicio helper para crear notificaciones automáticamente
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.sistema import Notificacion

logger = logging.getLogger(__name__)


def _mismo_usuario(a, b) -> bool:
    if a is None or b is None:
        return False
    return str(a) == str(b)


def notificar_asignacion(
    db: Session,
    usuario_id: Optional[UUID],
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID,
    *,
    actor_id: Optional[UUID] = None,
    anterior_usuario_id: Optional[UUID] = None,
    tipo: str = "asignacion",
) -> Optional[Notificacion]:
    """
    Crea una notificación cuando se asigna algo a un usuario.

    No notifica si no hay destinatario, si es la misma persona de antes
    o si el usuario se asignó a sí mismo.
    """
    if not usuario_id or not referencia_id:
        return None
    if _mismo_usuario(usuario_id, anterior_usuario_id):
        return None
    if _mismo_usuario(usuario_id, actor_id):
        return None

    try:
        notificacion = Notificacion(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            leida=False,
        )
        db.add(notificacion)
        db.commit()
        db.refresh(notificacion)
        return notificacion
    except Exception:
        logger.exception("No se pudo crear la notificación de asignación")
        try:
            db.rollback()
        except Exception:
            pass
        return None


def notificar_asignaciones(
    db: Session,
    usuario_ids: Iterable[Optional[UUID]],
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID,
    *,
    actor_id: Optional[UUID] = None,
    anteriores: Optional[Iterable[UUID]] = None,
    tipo: str = "asignacion",
) -> None:
    ya_notificados = {str(uid) for uid in (anteriores or []) if uid}
    vistos = set()
    for usuario_id in usuario_ids:
        if not usuario_id:
            continue
        clave = str(usuario_id)
        if clave in vistos or clave in ya_notificados:
            continue
        vistos.add(clave)
        notificar_asignacion(
            db,
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            actor_id=actor_id,
            tipo=tipo,
        )


def crear_notificacion_asignacion(
    db: Session,
    usuario_id: UUID,
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID,
    actor_id: Optional[UUID] = None,
    anterior_usuario_id: Optional[UUID] = None,
) -> Optional[Notificacion]:
    """Compatibilidad con llamadas existentes."""
    return notificar_asignacion(
        db,
        usuario_id=usuario_id,
        titulo=titulo,
        mensaje=mensaje,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        actor_id=actor_id,
        anterior_usuario_id=anterior_usuario_id,
        tipo="asignacion",
    )


def crear_notificacion_revision(
    db: Session,
    usuario_id: UUID,
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID
) -> Optional[Notificacion]:
    return notificar_asignacion(
        db,
        usuario_id=usuario_id,
        titulo=titulo,
        mensaje=mensaje,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        tipo="revision",
    )


def crear_notificacion_aprobacion(
    db: Session,
    usuario_id: UUID,
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID
) -> Optional[Notificacion]:
    return notificar_asignacion(
        db,
        usuario_id=usuario_id,
        titulo=titulo,
        mensaje=mensaje,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        tipo="aprobacion",
    )


def crear_notificacion_ticket_resuelto(
    db: Session,
    usuario_id: UUID,
    titulo_ticket: str,
    referencia_id: UUID
) -> Optional[Notificacion]:
    return notificar_asignacion(
        db,
        usuario_id=usuario_id,
        titulo="Ticket Resuelto",
        mensaje=f"Tu ticket '{titulo_ticket}' ha sido marcado como resuelto. Por favor verifica la solución.",
        referencia_tipo="ticket",
        referencia_id=referencia_id,
        tipo="info",
    )


def crear_notificacion_resultado_solicitud(
    db: Session,
    usuario_id: UUID,
    titulo_ticket: str,
    estado: str,
    referencia_id: UUID,
    comentario: str | None = None
) -> Optional[Notificacion]:
    accion = "aprobada" if estado == "aprobado" else "declinada"
    mensaje = f"Tu solicitud '{titulo_ticket}' fue {accion}."
    if comentario:
        mensaje = f"{mensaje} Comentario: {comentario}"

    return notificar_asignacion(
        db,
        usuario_id=usuario_id,
        titulo=f"Solicitud {accion}",
        mensaje=mensaje,
        referencia_tipo="ticket",
        referencia_id=referencia_id,
        tipo="info",
    )
