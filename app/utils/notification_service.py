"""
Servicio helper para crear notificaciones automáticamente
"""
from sqlalchemy.orm import Session
from uuid import UUID
from ..models.sistema import Notificacion


def crear_notificacion_asignacion(
    db: Session,
    usuario_id: UUID,
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID
) -> Notificacion:
    """
    Crear notificación cuando se asigna una tarea/ticket a un usuario
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario que recibirá la notificación
        titulo: Título de la notificación
        mensaje: Mensaje descriptivo
        referencia_tipo: Tipo de entidad (ticket, documento, auditoria, etc.)
        referencia_id: ID de la entidad referenciada
    
    Returns:
        Notificación creada
    """
    notificacion = Notificacion(
        usuario_id=usuario_id,
        titulo=titulo,
        mensaje=mensaje,
        tipo="asignacion",
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        leida=False
    )
    
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    
    return notificacion


def crear_notificacion_revision(
    db: Session,
    usuario_id: UUID,
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID
) -> Notificacion:
    """
    Crear notificación cuando se asigna una revisión de documento
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del revisor
        titulo: Título de la notificación
        mensaje: Mensaje descriptivo
        referencia_tipo: Tipo de entidad (generalmente 'documento')
        referencia_id: ID del documento
    
    Returns:
        Notificación creada
    """
    notificacion = Notificacion(
        usuario_id=usuario_id,
        titulo=titulo,
        mensaje=mensaje,
        tipo="revision",
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        leida=False
    )
    
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    
    return notificacion


def crear_notificacion_aprobacion(
    db: Session,
    usuario_id: UUID,
    titulo: str,
    mensaje: str,
    referencia_tipo: str,
    referencia_id: UUID
) -> Notificacion:
    """
    Crear notificación cuando se requiere aprobación
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del aprobador
        titulo: Título de la notificación
        mensaje: Mensaje descriptivo
        referencia_tipo: Tipo de entidad (generalmente 'documento')
        referencia_id: ID del documento
    
    Returns:
        Notificación creada
    """
    notificacion = Notificacion(
        usuario_id=usuario_id,
        titulo=titulo,
        mensaje=mensaje,
        tipo="aprobacion",
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        leida=False
    )
    
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    
    return notificacion


def crear_notificacion_ticket_resuelto(
    db: Session,
    usuario_id: UUID,  # Solicitante original
    titulo_ticket: str,
    referencia_id: UUID
) -> Notificacion:
    """
    Crear notificación cuando se resuelve un ticket
    """
    notificacion = Notificacion(
        usuario_id=usuario_id,
        titulo="Ticket Resuelto",
        mensaje=f"Tu ticket '{titulo_ticket}' ha sido marcado como resuelto. Por favor verifica la solución.",
        tipo="info",  # o un tipo 'resolucion' si lo agregamos
        referencia_tipo="ticket",
        referencia_id=referencia_id,
        leida=False
    )
    
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    
    return notificacion
