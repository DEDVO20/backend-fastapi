"""
Endpoints CRUD para gestión de auditorías
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.auditoria import Auditoria, HallazgoAuditoria, ProgramaAuditoria
from ..models.calidad import AccionCorrectiva
from ..schemas.auditoria import (
    AuditoriaCreate,
    AuditoriaUpdate,
    AuditoriaResponse,
    HallazgoAuditoriaCreate,
    HallazgoAuditoriaUpdate,
    HallazgoAuditoriaResponse,
    ProgramaAuditoriaCreate,
    ProgramaAuditoriaUpdate,
    ProgramaAuditoriaResponse
)
from ..services.auditorias.auditoria_service import AuditoriaService
from ..services.auditorias.hallazgo_service import HallazgoService
from ..schemas.calidad import NoConformidadResponse
from ..utils.notification_service import crear_notificacion_asignacion
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario
from ..utils.pdf_generator import PDFGenerator

router = APIRouter(prefix="/api/v1", tags=["auditorias"])

def _aplicar_reglas_iso_programa(programa_data: dict, current_user: Usuario, programa_actual: ProgramaAuditoria = None) -> dict:
    estado_objetivo = programa_data.get("estado", programa_actual.estado if programa_actual else "borrador")
    criterio_riesgo = programa_data.get(
        "criterio_riesgo",
        programa_actual.criterio_riesgo if programa_actual else None
    )

    if estado_objetivo == "aprobado":
        if not criterio_riesgo or not str(criterio_riesgo).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para aprobar el programa debe definir criterio_riesgo (ISO 9001:2015, enfoque basado en riesgos)."
            )
        programa_data.setdefault("aprobado_por", current_user.id)
        programa_data.setdefault("fecha_aprobacion", datetime.utcnow())

    if estado_objetivo in {"en_ejecucion", "finalizado", "cerrado"}:
        aprobado_por = programa_data.get(
            "aprobado_por",
            programa_actual.aprobado_por if programa_actual else None
        )
        fecha_aprobacion = programa_data.get(
            "fecha_aprobacion",
            programa_actual.fecha_aprobacion if programa_actual else None
        )
        if not aprobado_por or not fecha_aprobacion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para avanzar el programa primero debe estar aprobado (aprobado_por y fecha_aprobacion)."
            )

    return programa_data


def _validar_programa_para_auditoria(db: Session, programa_id: UUID, fecha_planificada=None) -> ProgramaAuditoria:
    programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == programa_id).first()
    if not programa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El programa de auditoría no existe.")

    if programa.estado not in {"aprobado", "en_ejecucion"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden crear auditorías en un programa no aprobado o fuera de ejecución."
        )

    if fecha_planificada and fecha_planificada.year != programa.anio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La fecha planificada ({fecha_planificada.year}) no coincide con el año del programa ({programa.anio})."
        )

    return programa


def _tiene_auditorias_abiertas(db: Session, programa_id: UUID) -> bool:
    abiertas = db.query(Auditoria).filter(
        Auditoria.programa_id == programa_id,
        Auditoria.estado.notin_(["completada", "cerrada"])
    ).count()
    return abiertas > 0

# ======================
# Endpoints de Programa de Auditorías
# ======================

@router.get("/programa-auditorias", response_model=List[ProgramaAuditoriaResponse])
def listar_programa_auditorias(
    skip: int = 0,
    limit: int = 100,
    anio: int = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar programas de auditoría"""
    query = db.query(ProgramaAuditoria)
    if anio:
        query = query.filter(ProgramaAuditoria.anio == anio)
    return query.offset(skip).limit(limit).all()

@router.post("/programa-auditorias", response_model=ProgramaAuditoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_programa_auditoria(
    programa: ProgramaAuditoriaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo programa anual de auditoría"""
    # Verificar si ya existe un programa para ese año
    existing = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.anio == programa.anio).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un programa de auditoría para el año {programa.anio}"
        )
    
    programa_data = _aplicar_reglas_iso_programa(programa.model_dump(), current_user)
    nuevo_programa = ProgramaAuditoria(**programa_data)
    db.add(nuevo_programa)
    db.commit()
    db.refresh(nuevo_programa)
    return nuevo_programa

@router.get("/programa-auditorias/{programa_id}", response_model=ProgramaAuditoriaResponse)
def obtener_programa_auditoria(
    programa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un programa de auditoría por ID"""
    programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == programa_id).first()
    if not programa:
        raise HTTPException(status_code=404, detail="Programa de auditoría no encontrado")
    return programa

@router.put("/programa-auditorias/{programa_id}", response_model=ProgramaAuditoriaResponse)
def actualizar_programa_auditoria(
    programa_id: UUID,
    programa_update: ProgramaAuditoriaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un programa de auditoría"""
    programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == programa_id).first()
    if not programa:
        raise HTTPException(status_code=404, detail="Programa de auditoría no encontrado")
    
    update_data = programa_update.model_dump(exclude_unset=True)

    nuevo_anio = update_data.get("anio")
    if nuevo_anio and nuevo_anio != programa.anio:
        existing = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.anio == nuevo_anio).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un programa de auditoría para el año {nuevo_anio}"
            )

    update_data = _aplicar_reglas_iso_programa(update_data, current_user, programa)

    estado_objetivo = update_data.get("estado")
    if estado_objetivo in {"finalizado", "cerrado"} and _tiene_auditorias_abiertas(db, programa.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cerrar/finalizar el programa mientras existan auditorías abiertas."
        )

    for field, value in update_data.items():
        setattr(programa, field, value)
    
    db.commit()
    db.refresh(programa)
    return programa


@router.delete("/programa-auditorias/{programa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_programa_auditoria(
    programa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == programa_id).first()
    if not programa:
        raise HTTPException(status_code=404, detail="Programa de auditoría no encontrado")

    if db.query(Auditoria).filter(Auditoria.programa_id == programa_id).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un programa con auditorías asociadas."
        )

    db.delete(programa)
    db.commit()
    return None


@router.get("/programas/{programa_id}/resumen")
def resumen_programa_auditoria(
    programa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == programa_id).first()
    if not programa:
        raise HTTPException(status_code=404, detail="Programa de auditoría no encontrado")

    total_auditorias = db.query(Auditoria).filter(Auditoria.programa_id == programa_id).count()
    planificadas = db.query(Auditoria).filter(
        Auditoria.programa_id == programa_id,
        Auditoria.estado == "planificada"
    ).count()
    en_curso = db.query(Auditoria).filter(
        Auditoria.programa_id == programa_id,
        Auditoria.estado == "en_curso"
    ).count()
    completadas = db.query(Auditoria).filter(
        Auditoria.programa_id == programa_id,
        Auditoria.estado.in_(["completada", "cerrada"])
    ).count()

    hallazgos_totales = db.query(HallazgoAuditoria).join(
        Auditoria, HallazgoAuditoria.auditoria_id == Auditoria.id
    ).filter(Auditoria.programa_id == programa_id).count()

    nc_generadas = db.query(func.count(func.distinct(HallazgoAuditoria.no_conformidad_id))).join(
        Auditoria, HallazgoAuditoria.auditoria_id == Auditoria.id
    ).filter(
        Auditoria.programa_id == programa_id,
        HallazgoAuditoria.no_conformidad_id.isnot(None)
    ).scalar() or 0

    acciones_abiertas = db.query(func.count(func.distinct(AccionCorrectiva.id))).join(
        HallazgoAuditoria, HallazgoAuditoria.no_conformidad_id == AccionCorrectiva.no_conformidad_id
    ).join(
        Auditoria, HallazgoAuditoria.auditoria_id == Auditoria.id
    ).filter(
        Auditoria.programa_id == programa_id,
        AccionCorrectiva.estado.isnot(None),
        AccionCorrectiva.estado.notin_(["cerrada", "verificada"])
    ).scalar() or 0

    avance_porcentaje = 0
    if total_auditorias > 0:
        avance_porcentaje = round(((completadas + (en_curso * 0.5)) / total_auditorias) * 100)

    return {
        "total_auditorias": total_auditorias,
        "planificadas": planificadas,
        "en_curso": en_curso,
        "completadas": completadas,
        "hallazgos_totales": hallazgos_totales,
        "nc_generadas": nc_generadas,
        "acciones_abiertas": acciones_abiertas,
        "avance_porcentaje": avance_porcentaje
    }

@router.post("/auditorias/{auditoria_id}/iniciar", response_model=AuditoriaResponse)
def iniciar_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Iniciar la ejecución de una auditoría"""
    return AuditoriaService.iniciar_auditoria(db, auditoria_id, current_user.id)

@router.post("/auditorias/{auditoria_id}/finalizar", response_model=AuditoriaResponse)
def finalizar_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Finalizar la ejecución de una auditoría"""
    return AuditoriaService.finalizar_auditoria(db, auditoria_id, current_user.id)

@router.post("/auditorias/{auditoria_id}/cerrar", response_model=AuditoriaResponse)
def cerrar_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Cerrar formalmente una auditoría"""
    return AuditoriaService.cerrar_auditoria(db, auditoria_id, current_user.id)

# ... existing hallazgo endpoints ...

@router.post("/hallazgos-auditoria/{hallazgo_id}/generar-nc", response_model=NoConformidadResponse)
def generar_nc_hallazgo(
    hallazgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Generar una No Conformidad a partir de un hallazgo"""
    return HallazgoService.generar_nc(db, hallazgo_id, current_user.id)

@router.post("/hallazgos-auditoria/{hallazgo_id}/verificar", response_model=HallazgoAuditoriaResponse)
def verificar_hallazgo(
    hallazgo_id: UUID, 
    resultado: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Verificar y cerrar un hallazgo"""
    return HallazgoService.verificar_hallazgo(db, hallazgo_id, current_user.id, resultado)


@router.get("/auditorias/{auditoria_id}/informe")
def generar_informe_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Generar informe de auditoría en PDF"""
    auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")

    # Preparar datos para el PDF
    auditoria_data = {
        "codigo": auditoria.codigo,
        "nombre": auditoria.nombre,
        "tipo": auditoria.tipo_auditoria,
        "estado": auditoria.estado,
        "alcance": auditoria.alcance,
        "objetivo": auditoria.objetivo,
        "fecha_inicio": auditoria.fecha_inicio.strftime('%d/%m/%Y') if auditoria.fecha_inicio else 'N/A',
        "fecha_fin": auditoria.fecha_fin.strftime('%d/%m/%Y') if auditoria.fecha_fin else 'N/A',
        "auditor_lider": f"{auditoria.auditor_lider.nombre} {auditoria.auditor_lider.primer_apellido}" if auditoria.auditor_lider else "N/A"
    }
    
    hallazgos_data = []
    for h in auditoria.hallazgos:
        hallazgos_data.append({
            "codigo": h.codigo,
            "tipo": h.tipo_hallazgo,
            "descripcion": h.descripcion,
            "estado": h.estado,
            "gravedad": h.gravedad
        })

    pdf_buffer = PDFGenerator.generar_informe_auditoria(auditoria_data, hallazgos_data)
    
    filename = f"Informe_Auditoria_{auditoria.codigo}.pdf"
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



# ======================
# Endpoints de Auditorías
# ======================

@router.get("/auditorias", response_model=List[AuditoriaResponse])
def listar_auditorias(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar auditorías"""
    query = db.query(Auditoria)
    
    if estado:
        query = query.filter(Auditoria.estado == estado)
    if tipo:
        query = query.filter(Auditoria.tipo_auditoria == tipo)
    
    auditorias = query.offset(skip).limit(limit).all()
    return auditorias


@router.post("/auditorias", response_model=AuditoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_auditoria(
    auditoria: AuditoriaCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva auditoría"""
    # Verify permission "auditorias.planificar"
    tiene_permiso = any(
        rp.permiso.codigo == "auditorias.planificar" 
        for ur in current_user.roles 
        for rp in ur.rol.permisos
        if rp.permiso
    )
    if not tiene_permiso:
        raise HTTPException(status_code=403, detail="No tienes permiso para planificar auditorías")

    # Verificar código único
    db_auditoria = db.query(Auditoria).filter(Auditoria.codigo == auditoria.codigo).first()
    if db_auditoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de auditoría ya existe"
        )
    
    auditoria_data = auditoria.model_dump()
    auditoria_data["norma_referencia"] = auditoria_data.get("norma_referencia") or "ISO 9001:2015"

    _validar_programa_para_auditoria(
        db,
        auditoria_data["programa_id"],
        auditoria_data.get("fecha_planificada")
    )

    nueva_auditoria = Auditoria(**auditoria_data)
    db.add(nueva_auditoria)
    db.commit()
    db.refresh(nueva_auditoria)
    
    # Notificar al auditor líder asignado
    if nueva_auditoria.auditor_lider_id:
        crear_notificacion_asignacion(
            db=db,
            usuario_id=nueva_auditoria.auditor_lider_id,
            titulo="Auditoría Asignada",
            mensaje=f"Se te ha asignado como Auditor Líder para la auditoría: {nueva_auditoria.codigo}",
            referencia_tipo="auditoria",
            referencia_id=nueva_auditoria.id
        )
        
    return nueva_auditoria


@router.get("/auditorias/{auditoria_id}", response_model=AuditoriaResponse)
def obtener_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una auditoría por ID"""
    auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )
    return auditoria


@router.put("/auditorias/{auditoria_id}", response_model=AuditoriaResponse)
def actualizar_auditoria(
    auditoria_id: UUID,
    auditoria_update: AuditoriaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una auditoría"""
    auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )
    
    # Verificar cambio de auditor líder
    previous_auditor_lider = auditoria.auditor_lider_id
    
    update_data = auditoria_update.model_dump(exclude_unset=True)

    if "programa_id" in update_data and update_data["programa_id"] != auditoria.programa_id and auditoria.estado != "planificada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cambiar el programa de una auditoría ya iniciada."
        )

    programa_id_objetivo = update_data.get("programa_id", auditoria.programa_id)
    fecha_planificada_objetivo = update_data.get("fecha_planificada", auditoria.fecha_planificada)
    _validar_programa_para_auditoria(db, programa_id_objetivo, fecha_planificada_objetivo)

    if "norma_referencia" in update_data and not update_data["norma_referencia"]:
        update_data["norma_referencia"] = "ISO 9001:2015"

    for field, value in update_data.items():
        setattr(auditoria, field, value)
    
    db.commit()
    db.refresh(auditoria)
    
    # Notificar si cambió el auditor líder
    if auditoria.auditor_lider_id and auditoria.auditor_lider_id != previous_auditor_lider:
        crear_notificacion_asignacion(
            db=db,
            usuario_id=auditoria.auditor_lider_id,
            titulo="Auditoría Asignada",
            mensaje=f"Se te ha asignado como Auditor Líder para la auditoría: {auditoria.codigo}",
            referencia_tipo="auditoria",
            referencia_id=auditoria.id
        )
        
    return auditoria


@router.delete("/auditorias/{auditoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una auditoría"""
    auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )
    
    db.delete(auditoria)
    db.commit()
    return None


# ================================
# Endpoints de Hallazgos de Auditoría
# ================================

@router.get("/auditorias/{auditoria_id}/hallazgos", response_model=List[HallazgoAuditoriaResponse])
def listar_hallazgos_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar hallazgos de una auditoría"""
    hallazgos = db.query(HallazgoAuditoria).filter(
        HallazgoAuditoria.auditoria_id == auditoria_id
    ).all()
    return hallazgos


@router.get("/hallazgos-auditoria", response_model=List[HallazgoAuditoriaResponse])
def listar_hallazgos(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    tipo_hallazgo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los hallazgos"""
    query = db.query(HallazgoAuditoria)
    
    if estado:
        query = query.filter(HallazgoAuditoria.estado == estado)
    if tipo_hallazgo:
        query = query.filter(HallazgoAuditoria.tipo_hallazgo == tipo_hallazgo)
    
    hallazgos = query.offset(skip).limit(limit).all()
    return hallazgos


@router.post("/hallazgos-auditoria", response_model=HallazgoAuditoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_hallazgo_auditoria(
    hallazgo: HallazgoAuditoriaCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo hallazgo de auditoría"""
    # Verify permission "auditorias.ejecutar"
    tiene_permiso = any(
        rp.permiso.codigo == "auditorias.ejecutar" 
        for ur in current_user.roles 
        for rp in ur.rol.permisos
        if rp.permiso
    )
    if not tiene_permiso:
        raise HTTPException(status_code=403, detail="No tienes permiso para registrar hallazgos")

    nuevo_hallazgo = HallazgoAuditoria(**hallazgo.model_dump())
    db.add(nuevo_hallazgo)
    db.commit()
    db.refresh(nuevo_hallazgo)
    return nuevo_hallazgo


@router.get("/hallazgos-auditoria/{hallazgo_id}", response_model=HallazgoAuditoriaResponse)
def obtener_hallazgo_auditoria(
    hallazgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un hallazgo por ID"""
    hallazgo = db.query(HallazgoAuditoria).filter(HallazgoAuditoria.id == hallazgo_id).first()
    if not hallazgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hallazgo no encontrado"
        )
    return hallazgo


@router.put("/hallazgos-auditoria/{hallazgo_id}", response_model=HallazgoAuditoriaResponse)
def actualizar_hallazgo_auditoria(
    hallazgo_id: UUID,
    hallazgo_update: HallazgoAuditoriaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un hallazgo de auditoría"""
    hallazgo = db.query(HallazgoAuditoria).filter(HallazgoAuditoria.id == hallazgo_id).first()
    if not hallazgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hallazgo no encontrado"
        )
    
    update_data = hallazgo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hallazgo, field, value)
    
    db.commit()
    db.refresh(hallazgo)
    return hallazgo


@router.delete("/hallazgos-auditoria/{hallazgo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_hallazgo_auditoria(
    hallazgo_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un hallazgo"""
    hallazgo = db.query(HallazgoAuditoria).filter(HallazgoAuditoria.id == hallazgo_id).first()
    if not hallazgo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hallazgo no encontrado"
        )
    
    db.delete(hallazgo)
    db.commit()
    return None
