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
    aprobado_por: UUID = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los documentos"""
    print(f"DEBUG: listar_documentos - filters: estado={estado}, aprobado_por={aprobado_por}")
    
    query = db.query(Documento).options(
        joinedload(Documento.creador),
        joinedload(Documento.aprobador),
        joinedload(Documento.versiones).joinedload(VersionDocumento.creador)
    )
    
    if estado:
        query = query.filter(Documento.estado == estado)
    if tipo_documento:
        query = query.filter(Documento.tipo_documento == tipo_documento)
    if aprobado_por:
        query = query.filter(Documento.aprobado_por == aprobado_por)
    
    documentos = query.offset(skip).limit(limit).all()
    print(f"DEBUG: Found {len(documentos)} documents")
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
    
    # Crear el documento y asignar el creador automáticamente
    documento_data = documento.model_dump()
    documento_data['creado_por'] = current_user.id
    
    nuevo_documento = Documento(**documento_data)
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
    
    # PROTECCIÓN: No permitir cambiar el creador (creado_por) nunca
    if 'creado_por' in update_data:
        del update_data['creado_por']
    
    # PROTECCIÓN: Solo el creador o admin puede cambiar el aprobador
    if 'aprobado_por' in update_data:
        if documento.creado_por != current_user.id:
            # Verificar si tiene permiso de admin
            tiene_permiso_admin = False
            for usuario_rol in current_user.roles:
                for rol_permiso in usuario_rol.rol.permisos:
                    if rol_permiso.permiso.codigo in ["documentos.administrar", "admin.all"]:
                        tiene_permiso_admin = True
                        break
                if tiene_permiso_admin:
                    break
            
            if not tiene_permiso_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo el creador del documento o un administrador puede asignar el aprobador"
                )
    
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
    """Eliminar un documento y sus relaciones"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    try:
        # Eliminar versiones del documento
        db.query(VersionDocumento).filter(
            VersionDocumento.documento_id == documento_id
        ).delete(synchronize_session=False)
        
        # Eliminar relaciones con procesos
        db.query(DocumentoProceso).filter(
            DocumentoProceso.documento_id == documento_id
        ).delete(synchronize_session=False)
        
        # Eliminar notificaciones relacionadas
        db.query(Notificacion).filter(
            Notificacion.referencia_tipo == "documento",
            Notificacion.referencia_id == documento_id
        ).delete(synchronize_session=False)
        
        db.flush()
        
        # Eliminar el documento
        db.delete(documento)
        db.commit()
        return None
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR al eliminar documento {documento_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el documento: {str(e)}"
        )


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
    # Asignar el creador automáticamente
    version_data = version.model_dump()
    version_data['creado_por'] = current_user.id
    
    nueva_version = VersionDocumento(**version_data)
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
    
    # Verificar que el usuario actual sea el creador del documento
    if documento.creado_por != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el creador del documento puede solicitar revisión"
        )
    
    # Actualizar estado
    documento.estado = "en_revision"
    
    # Crear notificación (CORREGIDO: usar 'nombre' en lugar de 'titulo')
    crear_notificacion_revision(
        db=db,
        usuario_id=revisor_id,
        titulo="Revisión de Documento Asignada",
        mensaje=f"Se te ha asignado la revisión del documento: {documento.nombre} ({documento.codigo})",
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
    
    # CORREGIDO: verificar que tenga un aprobador asignado (campo aprobado_por)
    if not documento.aprobado_por:
        raise HTTPException(status_code=400, detail="El documento no tiene un aprobador asignado. Edite el documento para asignar un aprobador.")
    
    # Actualizar estado
    documento.estado = "pendiente_aprobacion"
    
    # Crear notificación (CORREGIDO: usar nombre del documento y campo correcto de usuario)
    crear_notificacion_aprobacion(
        db=db,
        usuario_id=documento.aprobado_por,
        titulo="Documento para Aprobación",
        mensaje=f"El documento '{documento.nombre}' ({documento.codigo}) requiere tu aprobación",
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

    # 2. Verificar Asignación (Solo el aprobador designado) - CORREGIDO: aprobado_por
    if documento.aprobado_por != current_user.id:
        # Permitir bypass a administradores globales si es necesario, pero por ahora estricto
        raise HTTPException(status_code=403, detail="No eres el aprobador asignado para este documento")

    # 3. Segregación de Funciones (El aprobador NO puede ser el creador) - CORREGIDO: creado_por
    if documento.creado_por == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes aprobar tus propios documentos (Segregación de Funciones)")

    
    # Actualizar estado y fecha
    documento.estado = "aprobado"
    documento.fecha_aprobacion = datetime.now()
    
    # Notificar al creador/responsable - CORREGIDO: creado_por
    if documento.creado_por:
        notificacion = Notificacion(
            usuario_id=documento.creado_por,
            titulo="Documento Aprobado",
            mensaje=f"El documento '{documento.nombre}' ({documento.codigo}) ha sido aprobado.",
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
    
    # Notificar al creador/responsable - CORREGIDO: creado_por
    if documento.creado_por:
        notificacion = Notificacion(
            usuario_id=documento.creado_por,
            titulo="Documento Rechazado",
            mensaje=f"El documento '{documento.nombre}' ({documento.codigo}) ha sido rechazado. Motivo: {motivo}",
            tipo="rechazo", 
            referencia_tipo="documento",
            referencia_id=documento.id,
            leida=False
        )
        db.add(notificacion)
    
    db.commit()
    return {"message": "Documento rechazado correctamente"}
