"""
Endpoints CRUD para gestión de auditorías
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.auditoria import Auditoria, HallazgoAuditoria
from ..schemas.auditoria import (
    AuditoriaCreate,
    AuditoriaUpdate,
    AuditoriaResponse,
    HallazgoAuditoriaCreate,
    HallazgoAuditoriaUpdate,
    HallazgoAuditoriaResponse
)

router = APIRouter(prefix="/api/v1", tags=["auditorias"])


# ======================
# Endpoints de Auditorías
# ======================

@router.get("/auditorias", response_model=List[AuditoriaResponse])
def listar_auditorias(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    tipo_auditoria: str = None,
    db: Session = Depends(get_db)
):
    """Listar auditorías"""
    query = db.query(Auditoria)
    
    if estado:
        query = query.filter(Auditoria.estado == estado)
    if tipo_auditoria:
        query = query.filter(Auditoria.tipo_auditoria == tipo_auditoria)
    
    auditorias = query.offset(skip).limit(limit).all()
    return auditorias


@router.post("/auditorias", response_model=AuditoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_auditoria(auditoria: AuditoriaCreate, db: Session = Depends(get_db)):
    """Crear una nueva auditoría"""
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
    return nueva_auditoria


@router.get("/auditorias/{auditoria_id}", response_model=AuditoriaResponse)
def obtener_auditoria(auditoria_id: UUID, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """Actualizar una auditoría"""
    auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auditoría no encontrada"
        )
    
    update_data = auditoria_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(auditoria, field, value)
    
    db.commit()
    db.refresh(auditoria)
    return auditoria


@router.delete("/auditorias/{auditoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_auditoria(auditoria_id: UUID, db: Session = Depends(get_db)):
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
def listar_hallazgos_auditoria(auditoria_id: UUID, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
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
def crear_hallazgo_auditoria(hallazgo: HallazgoAuditoriaCreate, db: Session = Depends(get_db)):
    """Crear un nuevo hallazgo de auditoría"""
    nuevo_hallazgo = HallazgoAuditoria(**hallazgo.model_dump())
    db.add(nuevo_hallazgo)
    db.commit()
    db.refresh(nuevo_hallazgo)
    return nuevo_hallazgo


@router.get("/hallazgos-auditoria/{hallazgo_id}", response_model=HallazgoAuditoriaResponse)
def obtener_hallazgo_auditoria(hallazgo_id: UUID, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
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
def eliminar_hallazgo_auditoria(hallazgo_id: UUID, db: Session = Depends(get_db)):
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
