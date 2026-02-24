"""
Endpoints CRUD para gestión de capacitaciones
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from typing import List, Iterable, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from ..database import get_db
from ..models.capacitacion import Capacitacion, AsistenciaCapacitacion
from ..models.usuario import Usuario
from ..schemas.capacitacion import (
    CapacitacionCreate,
    CapacitacionUpdate,
    CapacitacionResponse,
    AsistenciaCapacitacionCreate,
    AsistenciaCapacitacionUpdate,
    AsistenciaCapacitacionResponse,
    ResumenAsistenciaCapacitacionResponse,
    UsuarioCapacitacionHistorialItem,
    UsuarioSinCapacitacionObligatoriaResponse,
    ReporteCapacitacionAuditoriaResponse,
)
from ..api.dependencies import get_current_user
from ..services.capacitacion_service import CapacitacionService

router = APIRouter(prefix="/api/v1", tags=["capacitaciones"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validar_convocados(
    db: Session,
    area_id: Optional[UUID],
    aplica_todas_areas: bool,
    usuarios_convocados_ids: Iterable[UUID],
) -> list[UUID]:
    convocados_ids = list(dict.fromkeys(usuarios_convocados_ids))
    if not convocados_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe seleccionar al menos una persona convocada.",
        )

    usuarios_query = db.query(Usuario).filter(
        Usuario.id.in_(convocados_ids),
        Usuario.activo.is_(True),
    )
    if not aplica_todas_areas and area_id:
        usuarios_query = usuarios_query.filter(Usuario.area_id == area_id)
    usuarios_validos = usuarios_query.all()

    if len(usuarios_validos) != len(convocados_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hay usuarios convocados inválidos, inactivos o fuera del área seleccionada.",
        )
    return convocados_ids


def _sincronizar_convocados(
    db: Session,
    capacitacion_id: UUID,
    convocados_ids: list[UUID],
) -> None:
    existentes = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == capacitacion_id
    ).all()
    existentes_por_usuario = {row.usuario_id: row for row in existentes}
    convocados_set = set(convocados_ids)

    for usuario_id, asistencia in existentes_por_usuario.items():
        if usuario_id not in convocados_set:
            db.delete(asistencia)

    ahora = _utcnow()
    for usuario_id in convocados_ids:
        if usuario_id in existentes_por_usuario:
            continue
        db.add(
            AsistenciaCapacitacion(
                capacitacion_id=capacitacion_id,
                usuario_id=usuario_id,
                asistio=False,
                certificado=False,
                fecha_registro=ahora,
            )
        )


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
    proceso_id: UUID = None,
    relacionada_con_hallazgo_id: UUID = None,
    relacionada_con_riesgo_id: UUID = None,
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
    if proceso_id:
        query = query.filter(Capacitacion.proceso_id == proceso_id)
    if relacionada_con_hallazgo_id:
        query = query.filter(Capacitacion.relacionada_con_hallazgo_id == relacionada_con_hallazgo_id)
    if relacionada_con_riesgo_id:
        query = query.filter(Capacitacion.relacionada_con_riesgo_id == relacionada_con_riesgo_id)
    
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
    
    data = capacitacion.model_dump()
    usuarios_convocados_ids = data.pop("usuarios_convocados_ids", [])
    convocados_ids = _validar_convocados(
        db=db,
        area_id=data.get("area_id"),
        aplica_todas_areas=bool(data.get("aplica_todas_areas")),
        usuarios_convocados_ids=usuarios_convocados_ids,
    )

    nueva_capacitacion = Capacitacion(**data)
    db.add(nueva_capacitacion)
    db.flush()
    _sincronizar_convocados(
        db=db,
        capacitacion_id=nueva_capacitacion.id,
        convocados_ids=convocados_ids,
    )
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
    usuarios_convocados_ids = update_data.pop("usuarios_convocados_ids", None)

    for field, value in update_data.items():
        setattr(capacitacion, field, value)

    if usuarios_convocados_ids is not None:
        convocados_ids = _validar_convocados(
            db=db,
            area_id=capacitacion.area_id,
            aplica_todas_areas=bool(capacitacion.aplica_todas_areas),
            usuarios_convocados_ids=usuarios_convocados_ids,
        )
        _sincronizar_convocados(
            db=db,
            capacitacion_id=capacitacion.id,
            convocados_ids=convocados_ids,
        )
    
    db.commit()
    db.refresh(capacitacion)
    return capacitacion


@router.post("/capacitaciones/{capacitacion_id}/iniciar", response_model=CapacitacionResponse)
def iniciar_capacitacion(
    capacitacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    capacitacion = db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
    if not capacitacion:
        raise HTTPException(status_code=404, detail="Capacitación no encontrada")

    if capacitacion.estado != "programada":
        raise HTTPException(status_code=400, detail="Solo se pueden iniciar capacitaciones programadas")

    ahora = _utcnow()
    capacitacion.estado = "en_curso"
    capacitacion.fecha_inicio = ahora
    capacitacion.fecha_realizacion = ahora
    capacitacion.fecha_fin = None
    capacitacion.fecha_cierre_asistencia = None
    db.commit()
    db.refresh(capacitacion)
    return capacitacion


@router.post("/capacitaciones/{capacitacion_id}/finalizar", response_model=CapacitacionResponse)
def finalizar_capacitacion(
    capacitacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    capacitacion = db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
    if not capacitacion:
        raise HTTPException(status_code=404, detail="Capacitación no encontrada")

    if capacitacion.estado != "en_curso":
        raise HTTPException(status_code=400, detail="Solo se pueden finalizar capacitaciones en curso")

    ahora = _utcnow()
    capacitacion.estado = "completada"
    capacitacion.fecha_fin = ahora
    capacitacion.fecha_cierre_asistencia = ahora + timedelta(minutes=5)
    db.commit()
    db.refresh(capacitacion)
    return capacitacion


@router.post("/capacitaciones/{capacitacion_id}/cerrar", response_model=CapacitacionResponse)
def cerrar_capacitacion(
    capacitacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    service = CapacitacionService(db)
    return service.cerrar_capacitacion(capacitacion_id, current_user.id)


@router.post("/capacitaciones/{capacitacion_id}/marcar-mi-asistencia", response_model=AsistenciaCapacitacionResponse)
def marcar_mi_asistencia(
    capacitacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    capacitacion = db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
    if not capacitacion:
        raise HTTPException(status_code=404, detail="Capacitación no encontrada")

    if capacitacion.estado != "completada":
        raise HTTPException(status_code=400, detail="La capacitación aún no ha finalizado.")

    ahora = _utcnow()
    fecha_cierre_asistencia = capacitacion.fecha_cierre_asistencia
    if fecha_cierre_asistencia and fecha_cierre_asistencia.tzinfo is None:
        fecha_cierre_asistencia = fecha_cierre_asistencia.replace(tzinfo=timezone.utc)

    if not fecha_cierre_asistencia or ahora > fecha_cierre_asistencia:
        raise HTTPException(status_code=400, detail="La ventana de 5 minutos para marcar asistencia ya cerró.")

    asistencia = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == capacitacion_id,
        AsistenciaCapacitacion.usuario_id == current_user.id,
    ).first()
    if not asistencia:
        raise HTTPException(status_code=403, detail="No estás convocado a esta capacitación.")

    asistencia.asistio = True
    asistencia.fecha_asistencia = ahora
    db.commit()
    db.refresh(asistencia)
    return asistencia


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
    db_capacitacion = db.query(Capacitacion).filter(Capacitacion.id == asistencia.capacitacion_id).first()
    if not db_capacitacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capacitación no encontrada"
        )

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
    
    asistencia_data = asistencia.model_dump()
    if not asistencia_data.get("fecha_registro"):
        asistencia_data["fecha_registro"] = _utcnow()
    if not asistencia_data.get("fecha_asistencia") and asistencia_data.get("asistio"):
        asistencia_data["fecha_asistencia"] = _utcnow()

    nueva_asistencia = AsistenciaCapacitacion(**asistencia_data)
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

    if update_data.get("asistio") is True and "fecha_asistencia" not in update_data:
        update_data["fecha_asistencia"] = _utcnow()

    for field, value in update_data.items():
        setattr(asistencia, field, value)
    
    db.commit()
    db.refresh(asistencia)
    return asistencia


@router.get("/capacitaciones/{capacitacion_id}/resumen-asistencia", response_model=ResumenAsistenciaCapacitacionResponse)
def resumen_asistencia_capacitacion(
    capacitacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    capacitacion = db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
    if not capacitacion:
        raise HTTPException(status_code=404, detail="Capacitación no encontrada")

    total_participantes = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == capacitacion_id
    ).count()
    asistieron = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == capacitacion_id,
        AsistenciaCapacitacion.asistio.is_(True)
    ).count()
    evaluados = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == capacitacion_id,
        AsistenciaCapacitacion.evaluacion_aprobada.isnot(None)
    ).count()
    evaluacion_aprobada = db.query(AsistenciaCapacitacion).filter(
        AsistenciaCapacitacion.capacitacion_id == capacitacion_id,
        AsistenciaCapacitacion.evaluacion_aprobada.is_(True)
    ).count()

    no_asistieron = max(total_participantes - asistieron, 0)
    porcentaje_asistencia = round((asistieron / total_participantes) * 100, 2) if total_participantes else 0.0
    porcentaje_aprobacion = round((evaluacion_aprobada / evaluados) * 100, 2) if evaluados else 0.0

    return ResumenAsistenciaCapacitacionResponse(
        capacitacion_id=capacitacion_id,
        total_participantes=total_participantes,
        asistieron=asistieron,
        no_asistieron=no_asistieron,
        porcentaje_asistencia=porcentaje_asistencia,
        evaluados=evaluados,
        evaluacion_aprobada=evaluacion_aprobada,
        porcentaje_aprobacion=porcentaje_aprobacion,
    )


@router.get("/usuarios/{usuario_id}/historial-capacitaciones", response_model=List[UsuarioCapacitacionHistorialItem])
def historial_capacitaciones_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    registros = db.query(AsistenciaCapacitacion, Capacitacion).join(
        Capacitacion, AsistenciaCapacitacion.capacitacion_id == Capacitacion.id
    ).filter(
        AsistenciaCapacitacion.usuario_id == usuario_id
    ).order_by(
        Capacitacion.fecha_programada.desc().nullslast(),
        AsistenciaCapacitacion.creado_en.desc()
    ).all()

    response: List[UsuarioCapacitacionHistorialItem] = []
    for asistencia, capacitacion in registros:
        response.append(
            UsuarioCapacitacionHistorialItem(
                capacitacion_id=capacitacion.id,
                codigo=capacitacion.codigo,
                nombre=capacitacion.nombre,
                tipo_capacitacion=capacitacion.tipo_capacitacion,
                estado=capacitacion.estado,
                fecha_programada=capacitacion.fecha_programada,
                fecha_asistencia=asistencia.fecha_asistencia,
                asistio=asistencia.asistio,
                evaluacion_aprobada=asistencia.evaluacion_aprobada,
                calificacion=asistencia.calificacion,
                observaciones=asistencia.observaciones,
            )
        )
    return response


@router.get("/capacitaciones-obligatorias/usuarios-pendientes", response_model=List[UsuarioSinCapacitacionObligatoriaResponse])
def usuarios_sin_capacitacion_obligatoria(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    capacitaciones_obligatorias = db.query(Capacitacion).filter(
        Capacitacion.tipo_capacitacion == "obligatoria",
        Capacitacion.estado.in_(["programada", "completada", "en_curso"])
    ).all()

    if not capacitaciones_obligatorias:
        return []

    obligatorias_ids = [c.id for c in capacitaciones_obligatorias]
    usuarios_activos = db.query(Usuario).filter(Usuario.activo.is_(True)).all()

    pendientes: List[UsuarioSinCapacitacionObligatoriaResponse] = []
    for usuario in usuarios_activos:
        aprobadas_usuario = db.query(AsistenciaCapacitacion.capacitacion_id).filter(
            AsistenciaCapacitacion.usuario_id == usuario.id,
            AsistenciaCapacitacion.capacitacion_id.in_(obligatorias_ids),
            AsistenciaCapacitacion.asistio.is_(True)
        ).all()
        aprobadas_ids = {row[0] for row in aprobadas_usuario}
        faltantes_ids = [cid for cid in obligatorias_ids if cid not in aprobadas_ids]
        if faltantes_ids:
            pendientes.append(
                UsuarioSinCapacitacionObligatoriaResponse(
                    usuario_id=usuario.id,
                    nombre=usuario.nombre,
                    primer_apellido=usuario.primer_apellido,
                    capacitaciones_obligatorias_pendientes=len(faltantes_ids),
                    capacitaciones_ids=faltantes_ids
                )
            )
    return pendientes


@router.get("/capacitaciones/reportes/auditoria", response_model=ReporteCapacitacionAuditoriaResponse)
def reporte_capacitacion_auditoria(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    total_capacitaciones = db.query(Capacitacion).count()
    capacitaciones_programadas = db.query(Capacitacion).filter(Capacitacion.estado == "programada").count()
    capacitaciones_ejecutadas = db.query(Capacitacion).filter(Capacitacion.estado.in_(["completada", "en_curso"])).count()
    total_registros_asistencia = db.query(AsistenciaCapacitacion).count()

    asistencia_por_cap = db.query(
        AsistenciaCapacitacion.capacitacion_id,
        func.count(AsistenciaCapacitacion.id).label("total"),
        func.sum(case((AsistenciaCapacitacion.asistio.is_(True), 1), else_=0)).label("asistieron")
    ).group_by(AsistenciaCapacitacion.capacitacion_id).all()

    porcentajes = []
    for row in asistencia_por_cap:
        if row.total and row.total > 0:
            porcentajes.append((row.asistieron or 0) * 100 / row.total)
    porcentaje_asistencia_promedio = round(sum(porcentajes) / len(porcentajes), 2) if porcentajes else 0.0

    capacitaciones_sin_evidencia = db.query(Capacitacion).filter(
        Capacitacion.estado.in_(["completada", "en_curso"]),
        (Capacitacion.archivo_evidencia.is_(None)) | (Capacitacion.archivo_evidencia == "")
    ).count()

    obligatorias = db.query(Capacitacion.id).filter(
        Capacitacion.tipo_capacitacion == "obligatoria",
        Capacitacion.estado.in_(["programada", "completada", "en_curso"])
    ).all()
    obligatorias_ids = [row[0] for row in obligatorias]

    capacitaciones_obligatorias_sin_cobertura = 0
    if obligatorias_ids:
        for cap_id in obligatorias_ids:
            asistentes = db.query(AsistenciaCapacitacion).filter(
                AsistenciaCapacitacion.capacitacion_id == cap_id,
                AsistenciaCapacitacion.asistio.is_(True)
            ).count()
            if asistentes == 0:
                capacitaciones_obligatorias_sin_cobertura += 1

    return ReporteCapacitacionAuditoriaResponse(
        total_capacitaciones=total_capacitaciones,
        capacitaciones_programadas=capacitaciones_programadas,
        capacitaciones_ejecutadas=capacitaciones_ejecutadas,
        total_registros_asistencia=total_registros_asistencia,
        porcentaje_asistencia_promedio=porcentaje_asistencia_promedio,
        capacitaciones_sin_evidencia=capacitaciones_sin_evidencia,
        capacitaciones_obligatorias_sin_cobertura=capacitaciones_obligatorias_sin_cobertura
    )
