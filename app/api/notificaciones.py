"""
API endpoints para Notificaciones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from ..database import get_db
from ..models.sistema import Notificacion
from ..schemas.notificacion import NotificacionResponse, NotificacionUpdate
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

router = APIRouter(prefix="/api/v1/notificaciones", tags=["notificaciones"])


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _propias(db: Session, current_user: Usuario):
    return db.query(Notificacion).filter(Notificacion.usuario_id == current_user.id)


def _obtener_propia(db: Session, notificacion_id: UUID, current_user: Usuario) -> Notificacion:
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == current_user.id,
    ).first()
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )
    return notificacion


def _marcar_objeto(notificacion: Notificacion, leida: bool = True) -> Notificacion:
    notificacion.leida = leida
    if leida:
        notificacion.fecha_lectura = notificacion.fecha_lectura or _ahora()
    else:
        notificacion.fecha_lectura = None
    return notificacion


def _marcar_todas_en_db(db: Session, current_user: Usuario) -> int:
    ahora = _ahora()
    filtros = (
        Notificacion.usuario_id == current_user.id,
        or_(Notificacion.leida.is_(False), Notificacion.leida.is_(None)),
    )
    valores = {"leida": True, "fecha_lectura": ahora}
    try:
        count = db.query(Notificacion).filter(*filtros).update(
            valores,
            synchronize_session=False,
        )
        db.commit()
        return count
    except Exception:
        db.rollback()
        count = db.query(Notificacion).filter(*filtros).update(
            {"leida": True},
            synchronize_session=False,
        )
        db.commit()
        return count


@router.get("", response_model=List[NotificacionResponse])
@router.get("/", response_model=List[NotificacionResponse])
def listar_notificaciones(
    skip: int = 0,
    limit: int = 50,
    solo_no_leidas: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Listar notificaciones del usuario actual"""
    query = _propias(db, current_user)

    if solo_no_leidas:
        query = query.filter(or_(Notificacion.leida.is_(False), Notificacion.leida.is_(None)))

    notificaciones = query.order_by(Notificacion.creado_en.desc()).offset(skip).limit(limit).all()
    return [n for n in notificaciones if str(n.usuario_id) == str(current_user.id)]


@router.get("/no-leidas/count", response_model=dict)
def contar_no_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Contar notificaciones no leídas del usuario actual"""
    count = _propias(db, current_user).filter(
        or_(Notificacion.leida.is_(False), Notificacion.leida.is_(None)),
    ).count()
    return {"count": count}


@router.post("/marcar-todas-leidas", response_model=dict)
@router.put("/marcar-todas-leidas", response_model=dict)
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Marcar todas las notificaciones del usuario como leídas.

    POST evita el choque con PUT /{uuid} de rutas antiguas de sistema.
    """
    count = _marcar_todas_en_db(db, current_user)
    return {"message": f"{count} notificaciones marcadas como leídas"}


@router.put("/{notificacion_id}/marcar-leida", response_model=NotificacionResponse)
def marcar_como_leida(
    notificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Marcar una notificación como leída"""
    notificacion = _obtener_propia(db, notificacion_id, current_user)
    _marcar_objeto(notificacion, True)
    try:
        db.commit()
        db.refresh(notificacion)
        return notificacion
    except Exception as e:
        print(f"ERROR al marcar notificación {notificacion_id} como leída: {str(e)}")
        db.rollback()
        notificacion = _obtener_propia(db, notificacion_id, current_user)
        notificacion.leida = True
        try:
            db.commit()
            db.refresh(notificacion)
            return notificacion
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al marcar la notificación como leída",
            )


@router.put("/{notificacion_id}", response_model=NotificacionResponse)
def actualizar_notificacion(
    notificacion_id: UUID,
    payload: Optional[NotificacionUpdate] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualizar una notificación propia (marcar como leída sin exigir admin)."""
    notificacion = _obtener_propia(db, notificacion_id, current_user)
    data = payload.model_dump(exclude_unset=True) if payload else {}
    leida = data.get("leida", True)
    _marcar_objeto(notificacion, bool(leida))
    if "fecha_lectura" in data:
        notificacion.fecha_lectura = data["fecha_lectura"]
    db.commit()
    db.refresh(notificacion)
    return notificacion


@router.delete("/{notificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_notificacion(
    notificacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Eliminar una notificación"""
    notificacion = _obtener_propia(db, notificacion_id, current_user)
    db.delete(notificacion)
    db.commit()
    return None
