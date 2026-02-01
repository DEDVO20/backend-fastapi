"""
Endpoints CRUD para gestión de capacitaciones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.capacitacion import Capacitacion, AsistenciaCapacitacion
from ..schemas.capacitacion import (
    CapacitacionCreate,
    CapacitacionUpdate,
    CapacitacionResponse,
    AsistenciaCapacitacionCreate,
    AsistenciaCapacitacionUpdate,
    AsistenciaCapacitacionResponse
)
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

router = APIRouter(prefix="/api/v1", tags=["capacitaciones"])


# ===========================
# Endpoints de Capacitaciones
# ===========================

@router.get("/capacitaciones", response_model=List[CapacitacionResponse])
def listar_capacitaciones(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    tipo_capacitacion: str = None,
    modalidad: str = None,
    db: Session = Depends(get_db)
):
    """Listar capacitaciones"""
    query = db.query(Capacitacion)
    
    if estado:
        query = query.filter(Capacitacion.estado == estado)
    if tipo_capacitacion:
        query = query.filter(Capacitacion.tipo_capacitacion == tipo_capacitacion)
    if modalidad:
        query = query.filter(Capacitacion.modalidad == modalidad)
    
    capacitaciones = query.offset(skip).limit(limit).all()
    return capacitaciones


@router.post("/capacitaciones", response_model=CapacitacionResponse, status_code=status.HTTP_201_CREATED)
def crear_capacitacion(
    capacitacion: CapacitacionCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva capacitación"""
    # Verificar código único
    db_capacitacion = db.query(Capacitacion).filter(Capacitacion.codigo == capacitacion.codigo).first()
    if db_capacitacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de capacitación ya existe"
        )
    
    nueva_capacitacion = Capacitacion(**capacitacion.model_dump())
    db.add(nueva_capacitacion)
    db.commit()
    db.refresh(nueva_capacitacion)
    return nueva_capacitacion


@router.get("/capacitaciones/{capacitacion_id}", response_model=CapacitacionResponse)
def obtener_capacitacion(
    capacitacion_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una capacitación por ID"""
    capacitacion = db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
    if not capacitacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capacitación no encontrada"
        )
    return capacitacion


@router.put("/capacitaciones/{capacitacion_id}", response_model=CapacitacionResponse)
def actualizar_capacitacion(
    capacitacion_id: UUID,
    capacitacion_update: CapacitacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar una capacitación"""
    capacitacion = db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
    if not capacitacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capacitación no encontrada"
        )
    
    update_data = capacitacion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(capacitacion, field, value)
    
    db.commit()
    db.refresh(capacitacion)
    return capacitacion


@router.delete("/capacitaciones/{capacitacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_capacitacion(
    capacitacion_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una capacitación"""
    capacitacion = db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
    if not capacitacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capacitación no encontrada"
        )
    
    db.delete(capacitacion)
    db.commit()
    return None


# ===================================
# Endpoints de Asistencias a Capacitaciones
# ===================================

@router.get("/capacitaciones/{capacitacion_id}/asistencias", response_model=List[AsistenciaCapacitacionResponse])
def listar_asistencias_capacitacion(
    capacitacion_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar asistencias de una capacitación"""
    asistencias = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == capacitacion_id
    ).all()
    return asistencias


@router.get("/asistencias-capacitacion", response_model=List[AsistenciaCapacitacionResponse])
def listar_asistencias(
    skip: int = 0,
    limit: int = 100,
    usuario_id: UUID = None,
    asistio: bool = None,
    db: Session = Depends(get_db)
):
    """Listar todas las asistencias"""
    query = db.query(AsistenciaCapacitacion)
    
    if usuario_id:
        query = query.filter(AsistenciaCapacitacion.usuario_id == usuario_id)
    if asistio is not None:
        query = query.filter(AsistenciaCapacitacion.asistio == asistio)
    
    asistencias = query.offset(skip).limit(limit).all()
    return asistencias


@router.post("/asistencias-capacitacion", response_model=AsistenciaCapacitacionResponse, status_code=status.HTTP_201_CREATED)
def crear_asistencia_capacitacion(
    asistencia: AsistenciaCapacitacionCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registrar asistencia a una capacitación"""
    # Verificar si ya existe la asistencia
    db_asistencia = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == asistencia.capacitacion_id,
        AsistenciaCapacitacion.usuario_id == asistencia.usuario_id
    ).first()
    if db_asistencia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La asistencia para este usuario ya está registrada"
        )
    
    nueva_asistencia = AsistenciaCapacitacion(**asistencia.model_dump())
    db.add(nueva_asistencia)
    db.commit()
    db.refresh(nueva_asistencia)
    return nueva_asistencia


@router.get("/asistencias-capacitacion/{asistencia_id}", response_model=AsistenciaCapacitacionResponse)
def obtener_asistencia_capacitacion(
    asistencia_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una asistencia por ID"""
    asistencia = db.query(AsistenciaCapacitacion).filter(AsistenciaCapacitacion.id == asistencia_id).first()
    if not asistencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asistencia no encontrada"
        )
    return asistencia


@router.put("/asistencias-capacitacion/{asistencia_id}", response_model=AsistenciaCapacitacionResponse)
def actualizar_asistencia_capacitacion(
    asistencia_id: UUID,
    asistencia_update: AsistenciaCapacitacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar una asistencia"""
    asistencia = db.query(AsistenciaCapacitacion).filter(AsistenciaCapacitacion.id == asistencia_id).first()
    if not asistencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asistencia no encontrada"
        )
    
    update_data = asistencia_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asistencia, field, value)
    
    db.commit()
    db.refresh(asistencia)
    return asistencia
