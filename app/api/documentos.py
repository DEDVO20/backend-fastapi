"""
Endpoints CRUD para gestión de documentos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
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
    DocumentoProcesoCreate,
    DocumentoProcesoResponse
)
from ..utils.notification_service import (
    crear_notificacion_revision, 
    crear_notificacion_aprobacion,
    crear_notificacion_asignacion
)
from ..models.sistema import Notificacion
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

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
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los documentos"""
    query = db.query(Documento).options(
        joinedload(Documento.creador),
        joinedload(Documento.aprobador),
        joinedload(Documento.versiones).joinedload(VersionDocumento.creador)
    )
    
    if estado:
        query = query.filter(Documento.estado == estado)
    if tipo_documento:
        query = query.filter(Documento.tipo_documento == tipo_documento)
    
    documentos = query.offset(skip).limit(limit).all()
    return documentos


@router.post("/documentos", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_documento(
    documento: DocumentoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
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
def obtener_documento(
    documento_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un documento por ID"""
    documento = db.query(Documento).options(
        joinedload(Documento.creador),
        joinedload(Documento.aprobador),
        joinedload(Documento.versiones).joinedload(VersionDocumento.creador)
    ).filter(Documento.id == documento_id).first()
    
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
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
def eliminar_documento(
    documento_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
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
def listar_versiones_documento(
    documento_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar versiones de un documento"""
    versiones = db.query(VersionDocumento).options(
        joinedload(VersionDocumento.creador)
    ).filter(
        VersionDocumento.documento_id == documento_id
    ).order_by(VersionDocumento.creado_en.desc()).all()
    return versiones


@router.post("/versiones-documentos", response_model=VersionDocumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_version_documento(
    version: VersionDocumentoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
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
def listar_procesos_documento(
    documento_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar procesos asociados a un documento"""
    relaciones = db.query(DocumentoProceso).filter(
        DocumentoProceso.documento_id == documento_id
    ).all()
    return relaciones


@router.post("/documentos-procesos", response_model=DocumentoProcesoResponse, status_code=status.HTTP_201_CREATED)
def asociar_documento_proceso(
    relacion: DocumentoProcesoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
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


# =================================
# Endpoints de Flujo de Trabajo (Workflow)
# =================================

@router.post("/documentos/{documento_id}/solicitar-revision", status_code=status.HTTP_200_OK)
def solicitar_revision_documento(
    documento_id: UUID,
    revisor_id: UUID, # ID del usuario que revisará
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Solicitar revisión de un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Actualizar estado (opcional, dependiendo del flujo)
    documento.estado = "en_revision"
    
    # Crear notificación
    crear_notificacion_revision(
        db=db,
        usuario_id=revisor_id,
        titulo="Revisión de Documento Asignada",
        mensaje=f"Se te ha asignado la revisión del documento: {documento.titulo} ({documento.codigo})",
        referencia_tipo="documento",
        referencia_id=documento.id
    )
    
    db.commit()
    return {"message": "Solicitud de revisión enviada correctamente"}


@router.post("/documentos/{documento_id}/solicitar-aprobacion", status_code=status.HTTP_200_OK)
def solicitar_aprobacion_documento(
    documento_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Solicitar aprobación de un documento (al aprobador asignado)"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    if not documento.aprobador_id:
        raise HTTPException(status_code=400, detail="El documento no tiene un aprobador asignado")
    
    # Actualizar estado
    documento.estado = "pendiente_aprobacion"
    
    # Crear notificación
    crear_notificacion_aprobacion(
        db=db,
        usuario_id=documento.aprobador_id,
        titulo="Documento para Aprobación",
        mensaje=f"El documento {documento.codigo} requiere tu aprobación",
        referencia_tipo="documento",
        referencia_id=documento.id
    )
    
    db.commit()
    return {"message": "Solicitud de aprobación enviada correctamente"}


@router.post("/documentos/{documento_id}/aprobar", status_code=status.HTTP_200_OK)
def aprobar_documento(
    documento_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Aprobar un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # 1. Verificar Permiso "documentos.aprobar"
    # Estructura: Usuario -> UsuarioRol -> Rol -> RolPermiso -> Permiso
    tiene_permiso = False
    for usuario_rol in current_user.roles:
        for rol_permiso in usuario_rol.rol.permisos:
            if rol_permiso.permiso.codigo == "documentos.aprobar":
                tiene_permiso = True
                break
        if tiene_permiso: break
    
    if not tiene_permiso:
        raise HTTPException(status_code=403, detail="No tienes permiso para aprobar documentos")

    # 2. Verificar Asignación (Solo el aprobador designado)
    if documento.aprobador_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el aprobador asignado para este documento")

    # 3. Segregación de Funciones (El aprobador NO puede ser el creador)
    if documento.elaborador_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes aprobar tus propios documentos (Segregación de Funciones)")

    
    # Actualizar estado
    documento.estado = "aprobado"
    
    # Notificar al creador/responsable
    if documento.elaborador_id:
        # Usa el helper genérico o crea uno específico de "info"
        notificacion = Notificacion(
            usuario_id=documento.elaborador_id,
            titulo="Documento Aprobado",
            mensaje=f"El documento {documento.codigo} ha sido aprobado.",
            tipo="aprobacion",
            referencia_tipo="documento",
            referencia_id=documento.id,
            leida=False
        )
        db.add(notificacion)
    
    db.commit()
    return {"message": "Documento aprobado correctamente"}


@router.post("/documentos/{documento_id}/rechazar", status_code=status.HTTP_200_OK)
def rechazar_documento(
    documento_id: UUID,
    motivo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Rechazar un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Actualizar estado
    documento.estado = "rechazado"
    
    # Notificar al creador/responsable
    if documento.elaborador_id:
        notificacion = Notificacion(
            usuario_id=documento.elaborador_id,
            titulo="Documento Rechazado",
            mensaje=f"El documento {documento.codigo} ha sido rechazado. Motivo: {motivo}",
            tipo="asignacion", # Usamos tipo genérico o uno de 'rechazo' si existiera
            referencia_tipo="documento",
            referencia_id=documento.id,
            leida=False
        )
        db.add(notificacion)
    
    db.commit()
    return {"message": "Documento rechazado correctamente"}
