"""
Endpoints CRUD para gestión de auditorías
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.auditoria import Auditoria, HallazgoAuditoria, ProgramaAuditoria
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

# === PROGRAMA DE AUDITORIAS ===

@router.get("/programa-auditorias", response_model=List[ProgramaAuditoriaResponse])
def get_programas(
    anio: int = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(ProgramaAuditoria)
    if anio:
        query = query.filter(ProgramaAuditoria.anio == anio)
    return query.all()

@router.post("/programa-auditorias", response_model=ProgramaAuditoriaResponse, status_code=status.HTTP_201_CREATED)
def create_programa(
    programa: ProgramaAuditoriaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar si ya existe un programa para ese año (opcional, pero buena práctica)
    existing = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.anio == programa.anio).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un programa de auditoría para el año {programa.anio}"
        )

    db_programa = ProgramaAuditoria(**programa.model_dump())
    db.add(db_programa)
    db.commit()
    db.refresh(db_programa)
    return db_programa

@router.get("/programa-auditorias/{id}", response_model=ProgramaAuditoriaResponse)
def get_programa(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == id).first()
    if not programa:
        raise HTTPException(status_code=404, detail="Programa de auditoría no encontrado")
    return programa

@router.put("/programa-auditorias/{id}", response_model=ProgramaAuditoriaResponse)
def update_programa(
    id: UUID,
    programa_update: ProgramaAuditoriaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == id).first()
    if not db_programa:
        raise HTTPException(status_code=404, detail="Programa de auditoría no encontrado")
    
    update_data = programa_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_programa, key, value)
    
    db.commit()
    db.refresh(db_programa)
    return db_programa

# === AUDITORIAS ===


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
    
    nuevo_programa = ProgramaAuditoria(**programa.model_dump())
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
    for field, value in update_data.items():
        setattr(programa, field, value)
    
    db.commit()
    db.refresh(programa)
    return programa

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
    
    nueva_auditoria = Auditoria(**auditoria.model_dump())
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
