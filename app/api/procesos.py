"""
Endpoints CRUD para gestión de procesos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.proceso import Proceso, EtapaProceso, InstanciaProceso, AccionProceso, ResponsableProceso
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
    AccionProcesoResponse,
    ResponsableProcesoCreate,
    ResponsableProcesoUpdate,
    ResponsableProcesoResponse,
)
from ..api.dependencies import require_any_permission
from ..models.usuario import Usuario
from ..services.proceso_service import ProcesoService
from ..services.competency_risk_automation_service import CompetencyRiskAutomationService

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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Crear un nuevo proceso"""
    service = ProcesoService(db)
    return service.crear_proceso(proceso, current_user.id)


@router.get("/procesos/{proceso_id}", response_model=ProcesoResponse)
def obtener_proceso(
    proceso_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Actualizar un proceso"""
    service = ProcesoService(db)
    return service.actualizar_proceso(proceso_id, proceso_update, current_user.id)


@router.delete("/procesos/{proceso_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proceso(
    proceso_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Crear una nueva etapa de proceso"""
    service = ProcesoService(db)
    return service.crear_etapa(etapa, current_user.id)


@router.put("/etapas/{etapa_id}", response_model=EtapaProcesoResponse)
def actualizar_etapa_proceso(
    etapa_id: UUID,
    etapa_update: EtapaProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Actualizar una etapa de proceso"""
    service = ProcesoService(db)
    return service.actualizar_etapa(etapa_id, etapa_update, current_user.id)


@router.delete("/etapas/{etapa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_etapa_proceso(
    etapa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
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


# =========================================
# Endpoints de Responsables Formales
# ISO 9001:2015 Cláusula 5.3
# =========================================

@router.get("/procesos/{proceso_id}/responsables", response_model=List[ResponsableProcesoResponse])
def listar_responsables_proceso(
    proceso_id: UUID,
    rol: str = None,
    solo_vigentes: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Listar todos los responsables formales de un proceso"""
    from datetime import datetime

    query = db.query(ResponsableProceso).filter(
        ResponsableProceso.proceso_id == proceso_id
    )
    if rol:
        query = query.filter(ResponsableProceso.rol == rol)
    if solo_vigentes:
        query = query.filter(
            (ResponsableProceso.vigente_hasta == None) |
            (ResponsableProceso.vigente_hasta > datetime.utcnow())
        )

    responsables = query.options(
        joinedload(ResponsableProceso.usuario),
        joinedload(ResponsableProceso.proceso)
    ).order_by(ResponsableProceso.es_principal.desc(), ResponsableProceso.fecha_asignacion).all()

    result = []
    for r in responsables:
        resp = ResponsableProcesoResponse.model_validate(r)
        if r.usuario:
            resp.usuario_nombre = r.usuario.nombre_completo
            resp.usuario_correo = r.usuario.correo_electronico
        if r.proceso:
            resp.proceso_nombre = r.proceso.nombre
            resp.proceso_codigo = r.proceso.codigo
        result.append(resp)

    return result


@router.post("/procesos/{proceso_id}/responsables", response_model=ResponsableProcesoResponse, status_code=status.HTTP_201_CREATED)
def asignar_responsable_proceso(
    proceso_id: UUID,
    data: ResponsableProcesoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Asignar un responsable formal al proceso"""
    # Validar proceso existe
    proceso = db.query(Proceso).filter(Proceso.id == proceso_id).first()
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Validar usuario existe y esté activo
    usuario = db.query(Usuario).filter(Usuario.id == data.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="El usuario especificado no existe")
    if not usuario.activo:
        raise HTTPException(status_code=400, detail="El usuario especificado está inactivo")

    # Validar unicidad (proceso + usuario + rol)
    existente = db.query(ResponsableProceso).filter(
        ResponsableProceso.proceso_id == proceso_id,
        ResponsableProceso.usuario_id == data.usuario_id,
        ResponsableProceso.rol == data.rol
    ).first()
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"El usuario ya tiene el rol '{data.rol}' en este proceso"
        )

    # Si es_principal, desmarcar el principal anterior
    if data.es_principal:
        db.query(ResponsableProceso).filter(
            ResponsableProceso.proceso_id == proceso_id,
            ResponsableProceso.es_principal == True
        ).update({"es_principal": False})

    responsable = ResponsableProceso(
        proceso_id=proceso_id,
        usuario_id=data.usuario_id,
        rol=data.rol,
        es_principal=data.es_principal,
        fecha_asignacion=data.fecha_asignacion,
        vigente_hasta=data.vigente_hasta,
        observaciones=data.observaciones,
    )
    db.add(responsable)
    automation = CompetencyRiskAutomationService(db)
    automation.evaluar_usuario_en_proceso(data.usuario_id, proceso_id)
    db.commit()
    db.refresh(responsable)

    # Cargar relaciones para la respuesta
    db.refresh(responsable, ["usuario", "proceso"])
    resp = ResponsableProcesoResponse.model_validate(responsable)
    if responsable.usuario:
        resp.usuario_nombre = responsable.usuario.nombre_completo
        resp.usuario_correo = responsable.usuario.correo_electronico
    if responsable.proceso:
        resp.proceso_nombre = responsable.proceso.nombre
        resp.proceso_codigo = responsable.proceso.codigo
    return resp


@router.put("/responsables-proceso/{responsable_id}", response_model=ResponsableProcesoResponse)
def actualizar_responsable_proceso(
    responsable_id: UUID,
    data: ResponsableProcesoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Actualizar la asignación de un responsable"""
    responsable = db.query(ResponsableProceso).filter(
        ResponsableProceso.id == responsable_id
    ).first()
    if not responsable:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    update_data = data.model_dump(exclude_unset=True)

    # Si se marca como principal, desmarcar los demás
    if update_data.get("es_principal") and not responsable.es_principal:
        db.query(ResponsableProceso).filter(
            ResponsableProceso.proceso_id == responsable.proceso_id,
            ResponsableProceso.id != responsable_id,
            ResponsableProceso.es_principal == True
        ).update({"es_principal": False})

    for key, value in update_data.items():
        setattr(responsable, key, value)

    db.commit()
    db.refresh(responsable, ["usuario", "proceso"])

    resp = ResponsableProcesoResponse.model_validate(responsable)
    if responsable.usuario:
        resp.usuario_nombre = responsable.usuario.nombre_completo
        resp.usuario_correo = responsable.usuario.correo_electronico
    if responsable.proceso:
        resp.proceso_nombre = responsable.proceso.nombre
        resp.proceso_codigo = responsable.proceso.codigo
    return resp


@router.delete("/responsables-proceso/{responsable_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_responsable_proceso(
    responsable_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Eliminar la asignación de un responsable"""
    responsable = db.query(ResponsableProceso).filter(
        ResponsableProceso.id == responsable_id
    ).first()
    if not responsable:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    db.delete(responsable)
    db.commit()
    return None


@router.get("/usuarios/{usuario_id}/procesos-asignados", response_model=List[ResponsableProcesoResponse])
def obtener_procesos_asignados_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["procesos.admin", "sistema.admin"]))
):
    """Obtener todos los procesos donde el usuario tiene un rol formal"""
    from datetime import datetime

    asignaciones = db.query(ResponsableProceso).filter(
        ResponsableProceso.usuario_id == usuario_id,
        (ResponsableProceso.vigente_hasta == None) |
        (ResponsableProceso.vigente_hasta > datetime.utcnow())
    ).options(
        joinedload(ResponsableProceso.proceso),
        joinedload(ResponsableProceso.usuario)
    ).all()

    result = []
    for r in asignaciones:
        resp = ResponsableProcesoResponse.model_validate(r)
        if r.usuario:
            resp.usuario_nombre = r.usuario.nombre_completo
            resp.usuario_correo = r.usuario.correo_electronico
        if r.proceso:
            resp.proceso_nombre = r.proceso.nombre
            resp.proceso_codigo = r.proceso.codigo
        result.append(resp)

    return result
