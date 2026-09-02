"""
API endpoints para Notificaciones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from ..database import get_db
from ..models.sistema import Notificacion
from ..schemas.notificacion import NotificacionResponse
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

router = APIRouter(prefix="/api/v1/notificaciones", tags=["notificaciones"])


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/", response_model=List[NotificacionResponse])
def listar_notificaciones(
    skip: int = 0,
    limit: int = 50,
    solo_no_leidas: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Listar notificaciones del usuario actual"""
    try:
        query = db.query(Notificacion).filter(Notificacion.usuario_id == current_user.id)

        if solo_no_leidas:
            query = query.filter(Notificacion.leida == False)

        notificaciones = query.order_by(Notificacion.creado_en.desc()).offset(skip).limit(limit).all()

        return [n for n in notificaciones if str(n.usuario_id) == str(current_user.id)]
    except Exception as e:
        print(f"ERROR al listar notificaciones para usuario {current_user.id}: {str(e)}")
        return []


@router.get("/no-leidas/count", response_model=dict)
def contar_no_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Contar notificaciones no leídas del usuario actual"""
    try:
        count = db.query(Notificacion).filter(
            Notificacion.usuario_id == current_user.id,
            Notificacion.leida == False,
        ).count()

        return {"count": count}
    except Exception as e:
        print(f"ERROR al contar notificaciones no leídas para usuario {current_user.id}: {str(e)}")
        return {"count": 0}


@router.put("/marcar-todas-leidas", response_model=dict)
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Marcar todas las notificaciones del usuario como leídas"""
    count = db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.leida == False,
    ).update(
        {
            "leida": True,
            "fecha_lectura": _ahora(),
        },
        synchronize_session=False,
    )

    db.commit()

    return {"message": f"{count} notificaciones marcadas como leídas"}


@router.put("/{notificacion_id}/marcar-leida", response_model=NotificacionResponse)
def marcar_como_leida(
    notificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Marcar una notificación como leída"""
    try:
        notificacion = db.query(Notificacion).filter(
            Notificacion.id == notificacion_id,
            Notificacion.usuario_id == current_user.id,
        ).first()

        if not notificacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada",
            )

        notificacion.leida = True
        notificacion.fecha_lectura = _ahora()
        db.commit()
        db.refresh(notificacion)

        return notificacion

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR al marcar notificación {notificacion_id} como leída: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al marcar la notificación como leída",
        )


@router.delete("/{notificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_notificacion(
    notificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Eliminar una notificación"""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == current_user.id,
    ).first()

    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )

    db.delete(notificacion)
    db.commit()

    return None
