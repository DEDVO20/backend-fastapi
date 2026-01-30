"""
Endpoints CRUD para sistema (notificaciones, configuraciones)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.sistema import Notificacion, Configuracion
from ..schemas.sistema import (
    NotificacionCreate,
    NotificacionUpdate,
    NotificacionResponse,
    ConfiguracionCreate,
    ConfiguracionUpdate,
    ConfiguracionResponse
)

router = APIRouter(prefix="/api/v1", tags=["sistema"])


# =========================
# Endpoints de Asignaciones
# =========================

from ..models.sistema import Asignacion
from ..schemas.sistema import AsignacionCreate, AsignacionResponse
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError


@router.get("/asignaciones", response_model=List[AsignacionResponse])
def listar_asignaciones(
    skip: int = 0,
    limit: int = 100,
    area_id: UUID = None,
    usuario_id: UUID = None,
    db: Session = Depends(get_db)
):
    """Listar asignaciones de responsables"""
    query = db.query(Asignacion).options(
        joinedload(Asignacion.area),
        joinedload(Asignacion.usuario)
    )
    
    if area_id:
        query = query.filter(Asignacion.area_id == area_id)
    if usuario_id:
        query = query.filter(Asignacion.usuario_id == usuario_id)
    
    asignaciones = query.offset(skip).limit(limit).all()
    return asignaciones


@router.post("/asignaciones", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
def crear_asignacion(asignacion: AsignacionCreate, db: Session = Depends(get_db)):
    """Crear una nueva asignación de responsable"""
    # Verificar unicidad
    db_asignacion = db.query(Asignacion).filter(
        Asignacion.area_id == asignacion.area_id,
        Asignacion.usuario_id == asignacion.usuario_id
    ).first()
    
    if db_asignacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está asignado a esta área"
        )
    
    nueva_asignacion = Asignacion(**asignacion.model_dump())
    db.add(nueva_asignacion)
    
    try:
        db.commit()
        db.refresh(nueva_asignacion)
        # Recargar relaciones para la respuesta
        db.refresh(nueva_asignacion, attribute_names=['area', 'usuario'])
        return nueva_asignacion
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad al crear la asignación"
        )


@router.delete("/asignaciones/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(asignacion_id: UUID, db: Session = Depends(get_db)):
    """Eliminar una asignación"""
    asignacion = db.query(Asignacion).filter(Asignacion.id == asignacion_id).first()
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    
    db.delete(asignacion)
    db.commit()
    return None


# ==========================
# Endpoints de Notificaciones
# ==========================

@router.get("/notificaciones", response_model=List[NotificacionResponse])
def listar_notificaciones(
    skip: int = 0,
    limit: int = 100,
    usuario_id: UUID = None,
    leida: bool = None,
    tipo: str = None,
    db: Session = Depends(get_db)
):
    """Listar notificaciones"""
    query = db.query(Notificacion)
    
    if usuario_id:
        query = query.filter(Notificacion.usuario_id == usuario_id)
    if leida is not None:
        query = query.filter(Notificacion.leida == leida)
    if tipo:
        query = query.filter(Notificacion.tipo == tipo)
    
    notificaciones = query.order_by(Notificacion.creado_en.desc()).offset(skip).limit(limit).all()
    return notificaciones


@router.post("/notificaciones", response_model=NotificacionResponse, status_code=status.HTTP_201_CREATED)
def crear_notificacion(notificacion: NotificacionCreate, db: Session = Depends(get_db)):
    """Crear una nueva notificación"""
    nueva_notificacion = Notificacion(**notificacion.model_dump())
    db.add(nueva_notificacion)
    db.commit()
    db.refresh(nueva_notificacion)
    return nueva_notificacion


@router.get("/notificaciones/{notificacion_id}", response_model=NotificacionResponse)
def obtener_notificacion(notificacion_id: UUID, db: Session = Depends(get_db)):
    """Obtener una notificación por ID"""
    notificacion = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    return notificacion


@router.put("/notificaciones/{notificacion_id}", response_model=NotificacionResponse)
def actualizar_notificacion(
    notificacion_id: UUID,
    notificacion_update: NotificacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar una notificación (marcar como leída)"""
    notificacion = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    update_data = notificacion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notificacion, field, value)
    
    db.commit()
    db.refresh(notificacion)
    return notificacion


@router.delete("/notificaciones/{notificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_notificacion(notificacion_id: UUID, db: Session = Depends(get_db)):
    """Eliminar una notificación"""
    notificacion = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    db.delete(notificacion)
    db.commit()

# =========================
# Endpoints de Asignaciones
# =========================

from ..models.sistema import Asignacion
from ..schemas.sistema import AsignacionCreate, AsignacionResponse
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError


@router.get("/asignaciones", response_model=List[AsignacionResponse])
def listar_asignaciones(
    skip: int = 0,
    limit: int = 100,
    area_id: UUID = None,
    usuario_id: UUID = None,
    db: Session = Depends(get_db)
):
    """Listar asignaciones de responsables"""
    query = db.query(Asignacion).options(
        joinedload(Asignacion.area),
        joinedload(Asignacion.usuario)
    )
    
    if area_id:
        query = query.filter(Asignacion.area_id == area_id)
    if usuario_id:
        query = query.filter(Asignacion.usuario_id == usuario_id)
    
    asignaciones = query.offset(skip).limit(limit).all()
    return asignaciones


@router.post("/asignaciones", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
def crear_asignacion(asignacion: AsignacionCreate, db: Session = Depends(get_db)):
    """Crear una nueva asignación de responsable"""
    # Verificar unicidad
    db_asignacion = db.query(Asignacion).filter(
        Asignacion.area_id == asignacion.area_id,
        Asignacion.usuario_id == asignacion.usuario_id
    ).first()
    
    if db_asignacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está asignado a esta área"
        )
    
    nueva_asignacion = Asignacion(**asignacion.model_dump())
    db.add(nueva_asignacion)
    
    try:
        db.commit()
        db.refresh(nueva_asignacion)
        # Recargar relaciones para la respuesta
        db.refresh(nueva_asignacion, attribute_names=['area', 'usuario'])
        return nueva_asignacion
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad al crear la asignación"
        )


@router.delete("/asignaciones/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(asignacion_id: UUID, db: Session = Depends(get_db)):
    """Eliminar una asignación"""
    asignacion = db.query(Asignacion).filter(Asignacion.id == asignacion_id).first()
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    
    db.delete(asignacion)
    db.commit()
    return None


# ============================
# Endpoints de Configuraciones
# ============================

@router.get("/configuraciones", response_model=List[ConfiguracionResponse])
def listar_configuraciones(
    skip: int = 0,
    limit: int = 100,
    categoria: str = None,
    activa: bool = None,
    db: Session = Depends(get_db)
):
    """Listar configuraciones del sistema"""
    query = db.query(Configuracion)
    
    if categoria:
        query = query.filter(Configuracion.categoria == categoria)
    if activa is not None:
        query = query.filter(Configuracion.activa == activa)
    
    configuraciones = query.offset(skip).limit(limit).all()
    return configuraciones


@router.post("/configuraciones", response_model=ConfiguracionResponse, status_code=status.HTTP_201_CREATED)
def crear_configuracion(configuracion: ConfiguracionCreate, db: Session = Depends(get_db)):
    """Crear una nueva configuración"""
    # Verificar clave única
    db_config = db.query(Configuracion).filter(Configuracion.clave == configuracion.clave).first()
    if db_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clave de configuración ya existe"
        )
    
    nueva_configuracion = Configuracion(**configuracion.model_dump())
    db.add(nueva_configuracion)
    db.commit()
    db.refresh(nueva_configuracion)
    return nueva_configuracion


@router.get("/configuraciones/{clave}", response_model=ConfiguracionResponse)
def obtener_configuracion(clave: str, db: Session = Depends(get_db)):
    """Obtener una configuración por clave"""
    configuracion = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    return configuracion


@router.put("/configuraciones/{clave}", response_model=ConfiguracionResponse)
def actualizar_configuracion(
    clave: str,
    configuracion_update: ConfiguracionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar una configuración"""
    configuracion = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    update_data = configuracion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(configuracion, field, value)
    
    db.commit()
    db.refresh(configuracion)
    return configuracion


@router.delete("/configuraciones/{clave}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_configuracion(clave: str, db: Session = Depends(get_db)):
    """Eliminar una configuración"""
    configuracion = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    db.delete(configuracion)
    db.commit()

# =========================
# Endpoints de Asignaciones
# =========================

from ..models.sistema import Asignacion
from ..schemas.sistema import AsignacionCreate, AsignacionResponse
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError


@router.get("/asignaciones", response_model=List[AsignacionResponse])
def listar_asignaciones(
    skip: int = 0,
    limit: int = 100,
    area_id: UUID = None,
    usuario_id: UUID = None,
    db: Session = Depends(get_db)
):
    """Listar asignaciones de responsables"""
    query = db.query(Asignacion).options(
        joinedload(Asignacion.area),
        joinedload(Asignacion.usuario)
    )
    
    if area_id:
        query = query.filter(Asignacion.area_id == area_id)
    if usuario_id:
        query = query.filter(Asignacion.usuario_id == usuario_id)
    
    asignaciones = query.offset(skip).limit(limit).all()
    return asignaciones


@router.post("/asignaciones", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
def crear_asignacion(asignacion: AsignacionCreate, db: Session = Depends(get_db)):
    """Crear una nueva asignación de responsable"""
    # Verificar unicidad
    db_asignacion = db.query(Asignacion).filter(
        Asignacion.area_id == asignacion.area_id,
        Asignacion.usuario_id == asignacion.usuario_id
    ).first()
    
    if db_asignacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está asignado a esta área"
        )
    
    nueva_asignacion = Asignacion(**asignacion.model_dump())
    db.add(nueva_asignacion)
    
    try:
        db.commit()
        db.refresh(nueva_asignacion)
        # Recargar relaciones para la respuesta
        db.refresh(nueva_asignacion, attribute_names=['area', 'usuario'])
        return nueva_asignacion
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad al crear la asignación"
        )


@router.delete("/asignaciones/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(asignacion_id: UUID, db: Session = Depends(get_db)):
    """Eliminar una asignación"""
    asignacion = db.query(Asignacion).filter(Asignacion.id == asignacion_id).first()
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    
    db.delete(asignacion)
    db.commit()
    return None
