"""
Endpoints CRUD para gestión de riesgos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.riesgo import Riesgo, ControlRiesgo
from ..schemas.riesgo import (
    RiesgoCreate,
    RiesgoUpdate,
    RiesgoResponse,
    ControlRiesgoCreate,
    ControlRiesgoUpdate,
    ControlRiesgoResponse
)
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

router = APIRouter(prefix="/api/v1", tags=["riesgos"])


# ======================
# Endpoints de Riesgos
# ======================

@router.get("/riesgos", response_model=List[RiesgoResponse])
def listar_riesgos(
    skip: int = 0,
    limit: int = 100,
    proceso_id: UUID = None,
    estado: str = None,
    nivel_riesgo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar riesgos"""
    query = db.query(Riesgo)
    
    if proceso_id:
        query = query.filter(Riesgo.proceso_id == proceso_id)
    if estado:
        query = query.filter(Riesgo.estado == estado)
    if nivel_riesgo:
        query = query.filter(Riesgo.nivel_riesgo == nivel_riesgo)
    
    # Data Scoping: Verificar si el usuario puede ver riesgos de todas las áreas
    # Si el usuario es admin o gestor de calidad, puede ver todos los riesgos
    # De lo contrario, solo ve los riesgos de su área
    
    try:
        es_admin_o_gestor = any(ur.rol.clave in ['admin', 'gestor_calidad'] for ur in current_user.roles)
        
        if not es_admin_o_gestor and current_user.area_id:
            # Filtrar por área del usuario
            from ..models.proceso import Proceso
            query = query.join(Proceso).filter(Proceso.area_id == current_user.area_id)
    except Exception as e:
        # Si hay error en el filtrado por área, permitir ver todos (fallback seguro)
        print(f"Error en filtrado por área: {e}")
    
    riesgos = query.offset(skip).limit(limit).all()
    return riesgos


@router.post("/riesgos", response_model=RiesgoResponse, status_code=status.HTTP_201_CREATED)
def crear_riesgo(
    riesgo: RiesgoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo riesgo"""
    # Verify permission "riesgos.identificar"
    tiene_permiso = any(
        rp.permiso.codigo == "riesgos.identificar" 
        for ur in current_user.roles 
        for rp in ur.rol.permisos
        if rp.permiso
    )
    if not tiene_permiso:
        raise HTTPException(status_code=403, detail="No tienes permiso para identificar riesgos")
        
    # Verificar código único
    db_riesgo = db.query(Riesgo).filter(Riesgo.codigo == riesgo.codigo).first()
    if db_riesgo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de riesgo ya existe"
        )
    
    nuevo_riesgo = Riesgo(**riesgo.model_dump())
    db.add(nuevo_riesgo)
    db.commit()
    db.refresh(nuevo_riesgo)
    return nuevo_riesgo


@router.get("/riesgos/{riesgo_id}", response_model=RiesgoResponse)
def obtener_riesgo(
    riesgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un riesgo por ID"""
    riesgo = db.query(Riesgo).filter(Riesgo.id == riesgo_id).first()
    if not riesgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Riesgo no encontrado"
        )
    return riesgo


@router.put("/riesgos/{riesgo_id}", response_model=RiesgoResponse)
def actualizar_riesgo(
    riesgo_id: UUID,
    riesgo_update: RiesgoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un riesgo"""
    riesgo = db.query(Riesgo).filter(Riesgo.id == riesgo_id).first()
    if not riesgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Riesgo no encontrado"
        )
    
    update_data = riesgo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(riesgo, field, value)
    
    db.commit()
    db.refresh(riesgo)
    return riesgo


@router.delete("/riesgos/{riesgo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_riesgo(
    riesgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un riesgo"""
    riesgo = db.query(Riesgo).filter(Riesgo.id == riesgo_id).first()
    if not riesgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Riesgo no encontrado"
        )
    
    db.delete(riesgo)
    db.commit()
    return None


# ============================
# Endpoints de Controles de Riesgo
# ============================

@router.get("/riesgos/{riesgo_id}/controles", response_model=List[ControlRiesgoResponse])
def listar_controles_riesgo(
    riesgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar controles de un riesgo"""
    controles = db.query(ControlRiesgo).filter(
        ControlRiesgo.riesgo_id == riesgo_id
    ).all()
    return controles


@router.get("/controles-riesgo", response_model=List[ControlRiesgoResponse])
def listar_controles(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    tipo_control: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los controles de riesgo"""
    query = db.query(ControlRiesgo)
    
    if activo is not None:
        query = query.filter(ControlRiesgo.activo == activo)
    if tipo_control:
        query = query.filter(ControlRiesgo.tipo_control == tipo_control)
    
    controles = query.offset(skip).limit(limit).all()
    return controles


@router.post("/controles-riesgo", response_model=ControlRiesgoResponse, status_code=status.HTTP_201_CREATED)
def crear_control_riesgo(
    control: ControlRiesgoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo control de riesgo"""
    nuevo_control = ControlRiesgo(**control.model_dump())
    db.add(nuevo_control)
    db.commit()
    db.refresh(nuevo_control)
    return nuevo_control


@router.get("/controles-riesgo/{control_id}", response_model=ControlRiesgoResponse)
def obtener_control_riesgo(
    control_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un control de riesgo por ID"""
    control = db.query(ControlRiesgo).filter(ControlRiesgo.id == control_id).first()
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control de riesgo no encontrado"
        )
    return control


@router.put("/controles-riesgo/{control_id}", response_model=ControlRiesgoResponse)
def actualizar_control_riesgo(
    control_id: UUID,
    control_update: ControlRiesgoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un control de riesgo"""
    control = db.query(ControlRiesgo).filter(ControlRiesgo.id == control_id).first()
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control de riesgo no encontrado"
        )
    
    update_data = control_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(control, field, value)
    
    db.commit()
    db.refresh(control)
    return control


@router.delete("/controles-riesgo/{control_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_control_riesgo(
    control_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un control de riesgo"""
    control = db.query(ControlRiesgo).filter(ControlRiesgo.id == control_id).first()
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control de riesgo no encontrado"
        )
    
    db.delete(control)
    db.commit()
    return None
