"""
Endpoints CRUD para gestión de procesos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.proceso import Proceso, EtapaProceso, InstanciaProceso, AccionProceso
from ..models.auditoria import HallazgoAuditoria
from ..schemas.proceso import (
    ProcesoCreate,
    ProcesoUpdate,
    ProcesoResponse,
    EtapaProcesoCreate,
    EtapaProcesoUpdate,
    EtapaProcesoResponse,
    EtapaProcesoOrdenItem,
    InstanciaProcesoCreate,
    InstanciaProcesoUpdate,
    InstanciaProcesoResponse,
    AccionProcesoCreate,
    AccionProcesoUpdate,
    AccionProcesoResponse
)
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario
from ..services.proceso_service import ProcesoService

router = APIRouter(prefix="/api/v1", tags=["procesos"])


# ======================
# Endpoints de Procesos
# ======================

@router.get("/procesos", response_model=List[ProcesoResponse])
def listar_procesos(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    area_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los procesos"""
    service = ProcesoService(db)
    procesos = service.listar(skip=skip, limit=limit, estado=estado, area_id=area_id)
    result = []
    for proceso in procesos:
        proceso_data = ProcesoResponse.model_validate(proceso)
        proceso_data.area_nombre = proceso.area.nombre if proceso.area else None
        proceso_data.responsable_nombre = f"{proceso.responsable.nombre} {proceso.responsable.primer_apellido}" if proceso.responsable else None
        result.append(proceso_data)
    
    return result


@router.post("/procesos", response_model=ProcesoResponse, status_code=status.HTTP_201_CREATED)
def crear_proceso(
    proceso: ProcesoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo proceso"""
    service = ProcesoService(db)
    return service.crear_proceso(proceso, current_user.id)


@router.get("/procesos/{proceso_id}", response_model=ProcesoResponse)
def obtener_proceso(
    proceso_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un proceso por ID"""
    service = ProcesoService(db)
    proceso = service.obtener(proceso_id)
    proceso_data = ProcesoResponse.model_validate(proceso)
    proceso_data.area_nombre = proceso.area.nombre if proceso.area else None
    proceso_data.responsable_nombre = f"{proceso.responsable.nombre} {proceso.responsable.primer_apellido}" if proceso.responsable else None
    
    return proceso_data


@router.put("/procesos/{proceso_id}", response_model=ProcesoResponse)
def actualizar_proceso(
    proceso_id: UUID,
    proceso_update: ProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un proceso"""
    service = ProcesoService(db)
    return service.actualizar_proceso(proceso_id, proceso_update, current_user.id)


@router.delete("/procesos/{proceso_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proceso(
    proceso_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un proceso"""
    service = ProcesoService(db)
    service.eliminar_proceso(proceso_id, current_user.id)
    return None


# ===============================
# Endpoints de Etapas de Proceso
# ===============================

@router.get("/procesos/{proceso_id}/etapas", response_model=List[EtapaProcesoResponse])
def listar_etapas_proceso(
    proceso_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar etapas de un proceso"""
    etapas = db.query(EtapaProceso).options(
        joinedload(EtapaProceso.responsable)
    ).filter(
        EtapaProceso.proceso_id == proceso_id,
        EtapaProceso.activo.is_(True)
    ).order_by(EtapaProceso.orden).all()

    if not etapas:
        return []

    etapa_ids = [etapa.id for etapa in etapas]
    hallazgos_por_etapa = dict(
        db.query(
            HallazgoAuditoria.etapa_proceso_id,
            func.count(HallazgoAuditoria.id)
        ).filter(
            HallazgoAuditoria.etapa_proceso_id.in_(etapa_ids)
        ).group_by(HallazgoAuditoria.etapa_proceso_id).all()
    )

    resultado = []
    for etapa in etapas:
        etapa_data = EtapaProcesoResponse.model_validate(etapa)
        etapa_data.responsable_nombre = (
            f"{etapa.responsable.nombre} {etapa.responsable.primer_apellido}".strip()
            if etapa.responsable else None
        )
        etapa_data.hallazgos_count = hallazgos_por_etapa.get(etapa.id, 0)
        resultado.append(etapa_data)

    return resultado


@router.post("/etapas", response_model=EtapaProcesoResponse, status_code=status.HTTP_201_CREATED)
def crear_etapa_proceso(
    etapa: EtapaProcesoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva etapa de proceso"""
    service = ProcesoService(db)
    return service.crear_etapa(etapa, current_user.id)


@router.put("/etapas/{etapa_id}", response_model=EtapaProcesoResponse)
def actualizar_etapa_proceso(
    etapa_id: UUID,
    etapa_update: EtapaProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una etapa de proceso"""
    service = ProcesoService(db)
    return service.actualizar_etapa(etapa_id, etapa_update, current_user.id)


@router.delete("/etapas/{etapa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_etapa_proceso(
    etapa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una etapa de proceso"""
    service = ProcesoService(db)
    service.eliminar_etapa(etapa_id, current_user.id)
    return None


@router.patch("/procesos/{proceso_id}/etapas/reordenar", status_code=status.HTTP_204_NO_CONTENT)
def reordenar_etapas_proceso(
    proceso_id: UUID,
    orden: List[EtapaProcesoOrdenItem],
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Reordenar etapas de un proceso en operación masiva"""
    if not orden:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos una etapa para reordenar"
        )

    ids_payload = [item.id for item in orden]
    if len(ids_payload) != len(set(ids_payload)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se permiten IDs de etapa duplicados en el reordenamiento"
        )

    etapas = db.query(EtapaProceso).filter(
        EtapaProceso.proceso_id == proceso_id,
        EtapaProceso.id.in_(ids_payload)
    ).all()

    if len(etapas) != len(ids_payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una o más etapas no pertenecen al proceso o no existen"
        )

    etapas_por_id = {etapa.id: etapa for etapa in etapas}
    for item in orden:
        etapas_por_id[item.id].orden = item.orden

    db.commit()
    return None


# =================================
# Endpoints de Instancias de Proceso
# =================================

@router.get("/instancias", response_model=List[InstanciaProcesoResponse])
def listar_instancias(
    skip: int = 0,
    limit: int = 100,
    proceso_id: UUID = None,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar instancias de procesos"""
    query = db.query(InstanciaProceso)
    
    if proceso_id:
        query = query.filter(InstanciaProceso.proceso_id == proceso_id)
    if estado:
        query = query.filter(InstanciaProceso.estado == estado)
    
    instancias = query.offset(skip).limit(limit).all()
    return instancias


@router.post("/instancias", response_model=InstanciaProcesoResponse, status_code=status.HTTP_201_CREATED)
def crear_instancia_proceso(
    instancia: InstanciaProcesoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva instancia de proceso"""
    # Verificar código único
    db_instancia = db.query(InstanciaProceso).filter(
        InstanciaProceso.codigo_instancia == instancia.codigo_instancia
    ).first()
    if db_instancia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de instancia ya existe"
        )
    
    nueva_instancia = InstanciaProceso(**instancia.model_dump())
    db.add(nueva_instancia)
    db.commit()
    db.refresh(nueva_instancia)
    return nueva_instancia


# ================================
# Endpoints de Acciones de Proceso
# ================================

@router.get("/acciones-proceso", response_model=List[AccionProcesoResponse])
def listar_acciones_proceso(
    skip: int = 0,
    limit: int = 100,
    proceso_id: UUID = None,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar acciones de proceso"""
    query = db.query(AccionProceso)
    
    if proceso_id:
        query = query.filter(AccionProceso.proceso_id == proceso_id)
    if estado:
        query = query.filter(AccionProceso.estado == estado)
    
    acciones = query.offset(skip).limit(limit).all()
    return acciones


@router.post("/acciones-proceso", response_model=AccionProcesoResponse, status_code=status.HTTP_201_CREATED)
def crear_accion_proceso(
    accion: AccionProcesoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva acción de proceso"""
    # Verificar código único
    db_accion = db.query(AccionProceso).filter(AccionProceso.codigo == accion.codigo).first()
    if db_accion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de acción ya existe"
        )
    
    nueva_accion = AccionProceso(**accion.model_dump())
    db.add(nueva_accion)
    db.commit()
    db.refresh(nueva_accion)
    return nueva_accion


@router.put("/acciones-proceso/{accion_id}", response_model=AccionProcesoResponse)
def actualizar_accion_proceso(
    accion_id: UUID,
    accion_update: AccionProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una acción de proceso"""
    accion = db.query(AccionProceso).filter(AccionProceso.id == accion_id).first()
    if not accion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acción no encontrada"
        )
    
    update_data = accion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(accion, field, value)
    
    db.commit()
    db.refresh(accion)
    return accion
