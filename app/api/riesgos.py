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
from ..services.riesgo_service import RiesgoService

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
    service = RiesgoService(db)

    # Data Scoping por área del usuario
    area_id_filtro = None
    try:
        es_admin_o_gestor = any(
            ur.rol.clave in ['admin', 'gestor_calidad']
            for ur in current_user.roles
        )
        if not es_admin_o_gestor and current_user.area_id:
            area_id_filtro = current_user.area_id
    except Exception:
        pass  # Fallback: ver todos

    riesgos = service.listar(
        skip=skip,
        limit=limit,
        proceso_id=proceso_id,
        estado=estado,
        nivel_riesgo=nivel_riesgo,
    )

    # Filtrar por área si aplica
    if area_id_filtro:
        riesgos = [r for r in riesgos if r.proceso and r.proceso.area_id == area_id_filtro]

    return riesgos


@router.post("/riesgos", response_model=RiesgoResponse, status_code=status.HTTP_201_CREATED)
def crear_riesgo(
    riesgo: RiesgoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo riesgo"""
    service = RiesgoService(db)
    # Verify permission "riesgos.identificar"
    tiene_permiso = any(
        rp.permiso.codigo == "riesgos.identificar" 
        for ur in current_user.roles 
        for rp in ur.rol.permisos
        if rp.permiso
    )
    if not tiene_permiso:
        raise HTTPException(status_code=403, detail="No tienes permiso para identificar riesgos")
        
    return service.crear(riesgo, current_user.id)


@router.get("/riesgos/{riesgo_id}", response_model=RiesgoResponse)
def obtener_riesgo(
    riesgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un riesgo por ID"""
    service = RiesgoService(db)
    return service.obtener(riesgo_id)


@router.put("/riesgos/{riesgo_id}", response_model=RiesgoResponse)
def actualizar_riesgo(
    riesgo_id: UUID,
    riesgo_update: RiesgoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un riesgo"""
    service = RiesgoService(db)
    return service.actualizar(riesgo_id, riesgo_update, current_user.id)


@router.delete("/riesgos/{riesgo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_riesgo(
    riesgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un riesgo"""
    service = RiesgoService(db)
    service.eliminar(riesgo_id, current_user.id)
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
    service = RiesgoService(db)
    return service.listar_controles_riesgo(riesgo_id)


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
    service = RiesgoService(db)
    return service.listar_controles(skip=skip, limit=limit, activo=activo, tipo_control=tipo_control)


@router.post("/controles-riesgo", response_model=ControlRiesgoResponse, status_code=status.HTTP_201_CREATED)
def crear_control_riesgo(
    control: ControlRiesgoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo control de riesgo"""
    service = RiesgoService(db)
    return service.crear_control(control, current_user.id)


@router.get("/controles-riesgo/{control_id}", response_model=ControlRiesgoResponse)
def obtener_control_riesgo(
    control_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un control de riesgo por ID"""
    service = RiesgoService(db)
    return service.obtener_control(control_id)


@router.put("/controles-riesgo/{control_id}", response_model=ControlRiesgoResponse)
def actualizar_control_riesgo(
    control_id: UUID,
    control_update: ControlRiesgoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un control de riesgo"""
    service = RiesgoService(db)
    return service.actualizar_control(control_id, control_update, current_user.id)


@router.delete("/controles-riesgo/{control_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_control_riesgo(
    control_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un control de riesgo"""
    service = RiesgoService(db)
    service.eliminar_control(control_id, current_user.id)
    return None
