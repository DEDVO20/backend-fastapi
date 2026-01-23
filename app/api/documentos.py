"""
Endpoints CRUD para gestión de documentos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models.documento import Documento, VersionDocumento, DocumentoProceso
from ..schemas.documento import (
    DocumentoCreate,
    DocumentoUpdate,
    DocumentoResponse,
    VersionDocumentoCreate,
    VersionDocumentoResponse,
    DocumentoProcesoCreate,
    DocumentoProcesoResponse
)

router = APIRouter(prefix="/api/v1", tags=["documentos"])


# ==========================
# Endpoints de Documentos
# ==========================

@router.get("/documentos", response_model=List[DocumentoResponse])
def listar_documentos(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    tipo_documento: str = None,
    db: Session = Depends(get_db)
):
    """Listar todos los documentos"""
    query = db.query(Documento)
    
    if estado:
        query = query.filter(Documento.estado == estado)
    if tipo_documento:
        query = query.filter(Documento.tipo_documento == tipo_documento)
    
    documentos = query.offset(skip).limit(limit).all()
    return documentos


@router.post("/documentos", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_documento(documento: DocumentoCreate, db: Session = Depends(get_db)):
    """Crear un nuevo documento"""
    # Verificar código único
    db_documento = db.query(Documento).filter(Documento.codigo == documento.codigo).first()
    if db_documento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de documento ya existe"
        )
    
    nuevo_documento = Documento(**documento.model_dump())
    db.add(nuevo_documento)
    db.commit()
    db.refresh(nuevo_documento)
    return nuevo_documento


@router.get("/documentos/{documento_id}", response_model=DocumentoResponse)
def obtener_documento(documento_id: UUID, db: Session = Depends(get_db)):
    """Obtener un documento por ID"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    return documento


@router.put("/documentos/{documento_id}", response_model=DocumentoResponse)
def actualizar_documento(
    documento_id: UUID,
    documento_update: DocumentoUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    update_data = documento_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(documento, field, value)
    
    db.commit()
    db.refresh(documento)
    return documento


@router.delete("/documentos/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_documento(documento_id: UUID, db: Session = Depends(get_db)):
    """Eliminar un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    db.delete(documento)
    db.commit()
    return None


# ===============================
# Endpoints de Versiones de Documentos
# ===============================

@router.get("/documentos/{documento_id}/versiones", response_model=List[VersionDocumentoResponse])
def listar_versiones_documento(documento_id: UUID, db: Session = Depends(get_db)):
    """Listar versiones de un documento"""
    versiones = db.query(VersionDocumento).filter(
        VersionDocumento.documento_id == documento_id
    ).order_by(VersionDocumento.creado_en.desc()).all()
    return versiones


@router.post("/versiones-documentos", response_model=VersionDocumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_version_documento(version: VersionDocumentoCreate, db: Session = Depends(get_db)):
    """Crear una nueva versión de documento"""
    nueva_version = VersionDocumento(**version.model_dump())
    db.add(nueva_version)
    db.commit()
    db.refresh(nueva_version)
    return nueva_version


# =================================
# Endpoints de Documento-Proceso
# =================================

@router.get("/documentos/{documento_id}/procesos", response_model=List[DocumentoProcesoResponse])
def listar_procesos_documento(documento_id: UUID, db: Session = Depends(get_db)):
    """Listar procesos asociados a un documento"""
    relaciones = db.query(DocumentoProceso).filter(
        DocumentoProceso.documento_id == documento_id
    ).all()
    return relaciones


@router.post("/documentos-procesos", response_model=DocumentoProcesoResponse, status_code=status.HTTP_201_CREATED)
def asociar_documento_proceso(relacion: DocumentoProcesoCreate, db: Session = Depends(get_db)):
    """Asociar un documento con un proceso"""
    # Verificar que no exista la relación
    db_relacion = db.query(DocumentoProceso).filter(
        DocumentoProceso.documento_id == relacion.documento_id,
        DocumentoProceso.proceso_id == relacion.proceso_id
    ).first()
    if db_relacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La relación documento-proceso ya existe"
        )
    
    nueva_relacion = DocumentoProceso(**relacion.model_dump())
    db.add(nueva_relacion)
    db.commit()
    db.refresh(nueva_relacion)
    return nueva_relacion
