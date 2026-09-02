"""
Endpoints CRUD para gestión de documentos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.documento import Documento, VersionDocumento, DocumentoProceso
from ..models.usuario import UsuarioRol, Rol, RolPermiso
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
    notificar_asignacion,
)
from ..models.sistema import Notificacion
from ..api.dependencies import require_any_permission, user_has_any_permission
from ..models.usuario import Usuario
from ..utils.codigos import asignar_codigo, prefijo_documento

router = APIRouter(prefix="/api/v1", tags=["documentos"])


def _siguiente_version(version: Optional[str]) -> str:
    raw = (version or "1.0").strip().replace(",", ".") or "1.0"
    partes = [p for p in raw.split(".") if p != ""]
    try:
        mayor = int(partes[0]) if partes else 1
        menor = int(partes[1]) if len(partes) > 1 else 0
        return f"{mayor}.{menor + 1}"
    except ValueError:
        return "1.1"


def _cargar_usuario_con_permisos(db: Session, usuario_id: UUID) -> Optional[Usuario]:
    return db.query(Usuario).options(
        joinedload(Usuario.roles).joinedload(UsuarioRol.rol).joinedload(Rol.permisos).joinedload(RolPermiso.permiso)
    ).filter(Usuario.id == usuario_id).first()


def _asegurar_rol_documento(db: Session, usuario_id: Optional[UUID], permisos: List[str], etiqueta: str) -> None:
    if not usuario_id:
        return
    usuario = _cargar_usuario_con_permisos(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario asignado como {etiqueta} no existe",
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario asignado como {etiqueta} está inactivo",
        )
    if not user_has_any_permission(usuario, permisos):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se puede asignar como {etiqueta} a usuarios con el permiso correspondiente ({', '.join(permisos)})",
        )


def _archivar_version(db: Session, documento: Documento, usuario_id: UUID, descripcion: str) -> None:
    db.add(VersionDocumento(
        documento_id=documento.id,
        version=documento.version_actual or "1.0",
        descripcion_cambios=descripcion,
        ruta_archivo=documento.ruta_archivo,
        creado_por=usuario_id,
    ))


# ==========================
# Endpoints de Documentos
# ==========================

@router.get("/documentos", response_model=List[DocumentoResponse])
def listar_documentos(
    skip: int = 0,
    limit: int = 1000,
    estado: str = None,
    tipo_documento: str = None,
    aprobado_por: UUID = None,
    revisado_por: UUID = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission([
        "documentos.ver",
        "documentos.crear",
        "documentos.revisar",
        "documentos.aprobar",
        "documentos.anular",
        "calidad.ver",
        "auditorias.ver",
        "auditorias.planificar",
        "auditorias.ejecutar",
        "riesgos.identificar",
        "riesgos.ver",
        "riesgos.gestion",
        "capacitaciones.gestion",
        "usuarios.ver",
        "usuarios.gestion",
        "noconformidades.reportar",
        "noconformidades.gestion",
        "noconformidades.cerrar",
        "procesos.admin",
        "sistema.config",
        "sistema.admin",
    ]))
):
    """Listar todos los documentos"""
    print(f"DEBUG: listar_documentos - filters: estado={estado}, aprobado_por={aprobado_por}, revisado_por={revisado_por}")
    
    query = db.query(Documento).options(
        joinedload(Documento.creador),
        joinedload(Documento.aprobador),
        joinedload(Documento.revisor),
        joinedload(Documento.versiones).joinedload(VersionDocumento.creador)
    )
    
    puede_ver_todo_documentos = user_has_any_permission(
        current_user,
        ["documentos.ver", "documentos.crear", "documentos.revisar", "documentos.aprobar", "documentos.anular", "sistema.admin"],
    )

    if not puede_ver_todo_documentos:
        query = query.filter(Documento.estado == "aprobado")
        if estado and estado != "aprobado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes consultar documentos públicos aprobados",
            )

    if estado:
        query = query.filter(Documento.estado == estado)
    if tipo_documento:
        query = query.filter(Documento.tipo_documento == tipo_documento)
    if aprobado_por:
        query = query.filter(Documento.aprobado_por == aprobado_por)
    if revisado_por:
        query = query.filter(Documento.revisado_por == revisado_por)
    
    documentos = query.offset(skip).limit(limit).all()
    print(f"DEBUG: Found {len(documentos)} documents")
    return documentos


@router.post("/documentos", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_documento(
    documento: DocumentoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.crear", "sistema.admin"]))
):
    """Crear un nuevo documento"""
    documento_data = documento.model_dump()
    prefix = prefijo_documento(documento.tipo_documento)
    documento_data["creado_por"] = current_user.id
    _asegurar_rol_documento(db, documento_data.get("revisado_por"), ["documentos.revisar"], "revisor")
    _asegurar_rol_documento(db, documento_data.get("aprobado_por"), ["documentos.aprobar"], "aprobador")
    nuevo_documento = None
    ultimo_error = None
    for intento in range(6):
        documento_data["codigo"] = asignar_codigo(
            db,
            Documento,
            None if intento else documento_data.get("codigo"),
            prefix,
        )
        try:
            nuevo_documento = Documento(**documento_data)
            db.add(nuevo_documento)
            db.commit()
            db.refresh(nuevo_documento)
            ultimo_error = None
            break
        except IntegrityError as exc:
            db.rollback()
            mensaje = str(getattr(exc, "orig", exc)).lower()
            if "codigo" not in mensaje:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se pudo guardar el documento. Verifique los datos e intente de nuevo.",
                ) from exc
            ultimo_error = exc
    if nuevo_documento is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo asignar un código único al documento. Intente guardar de nuevo.",
        ) from ultimo_error
    notificar_asignacion(
        db,
        usuario_id=getattr(nuevo_documento, "revisado_por", None),
        titulo="Documento asignado para revisión",
        mensaje=f"Se te asignó revisar el documento {nuevo_documento.codigo}",
        referencia_tipo="documento",
        referencia_id=nuevo_documento.id,
        actor_id=current_user.id,
        tipo="revision",
    )
    notificar_asignacion(
        db,
        usuario_id=getattr(nuevo_documento, "aprobado_por", None),
        titulo="Documento asignado para aprobación",
        mensaje=f"Se te asignó aprobar el documento {nuevo_documento.codigo}",
        referencia_tipo="documento",
        referencia_id=nuevo_documento.id,
        actor_id=current_user.id,
        tipo="aprobacion",
    )
    return nuevo_documento


@router.get("/documentos/{documento_id}", response_model=DocumentoResponse)
def obtener_documento(
    documento_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission([
        "documentos.ver",
        "documentos.crear",
        "documentos.revisar",
        "documentos.aprobar",
        "documentos.anular",
        "calidad.ver",
        "auditorias.ver",
        "auditorias.planificar",
        "auditorias.ejecutar",
        "riesgos.identificar",
        "riesgos.ver",
        "riesgos.gestion",
        "capacitaciones.gestion",
        "usuarios.ver",
        "usuarios.gestion",
        "noconformidades.reportar",
        "noconformidades.gestion",
        "noconformidades.cerrar",
        "procesos.admin",
        "sistema.config",
        "sistema.admin",
    ]))
):
    """Obtener un documento por ID"""
    documento = db.query(Documento).options(
        joinedload(Documento.creador),
        joinedload(Documento.aprobador),
        joinedload(Documento.revisor),
        joinedload(Documento.versiones).joinedload(VersionDocumento.creador)
    ).filter(Documento.id == documento_id).first()
    
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )

    puede_ver_todo_documentos = user_has_any_permission(
        current_user,
        ["documentos.ver", "documentos.crear", "documentos.revisar", "documentos.aprobar", "documentos.anular", "sistema.admin"],
    )
    if not puede_ver_todo_documentos and documento.estado != "aprobado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes consultar documentos públicos aprobados",
        )

    return documento


@router.put("/documentos/{documento_id}", response_model=DocumentoResponse)
def actualizar_documento(
    documento_id: UUID,
    documento_update: DocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.revisar", "sistema.admin"]))
):
    """Actualizar un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    try:
        update_data = documento_update.model_dump(exclude_unset=True)
        anterior_revisor = documento.revisado_por
        anterior_aprobador = documento.aprobado_por
        version_anterior = documento.version_actual or "1.0"

        if 'creado_por' in update_data:
            del update_data['creado_por']

        es_admin = user_has_any_permission(current_user, ["sistema.admin"])
        es_creador = documento.creado_por == current_user.id

        if 'aprobado_por' in update_data:
            if not es_creador and not es_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo el creador del documento o un administrador puede asignar el aprobador"
                )
            _asegurar_rol_documento(db, update_data.get("aprobado_por"), ["documentos.aprobar"], "aprobador")

        if 'revisado_por' in update_data:
            if not es_creador and not es_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo el creador del documento o un administrador puede asignar el revisor"
                )
            _asegurar_rol_documento(db, update_data.get("revisado_por"), ["documentos.revisar"], "revisor")

        version_enviada = str(update_data.get("version_actual") or "").strip()
        if not version_enviada or version_enviada == str(version_anterior or "").strip():
            update_data["version_actual"] = _siguiente_version(version_anterior)

        _archivar_version(
            db,
            documento,
            current_user.id,
            f"Versión {version_anterior} archivada antes de actualizar a {update_data.get('version_actual', _siguiente_version(version_anterior))}",
        )

        for field, value in update_data.items():
            setattr(documento, field, value)
        
        db.commit()
        db.refresh(documento)
        notificar_asignacion(
            db,
            usuario_id=documento.revisado_por,
            titulo="Documento asignado para revisión",
            mensaje=f"Se te asignó revisar el documento {documento.codigo}",
            referencia_tipo="documento",
            referencia_id=documento.id,
            actor_id=current_user.id,
            anterior_usuario_id=anterior_revisor,
            tipo="revision",
        )
        notificar_asignacion(
            db,
            usuario_id=documento.aprobado_por,
            titulo="Documento asignado para aprobación",
            mensaje=f"Se te asignó aprobar el documento {documento.codigo}",
            referencia_tipo="documento",
            referencia_id=documento.id,
            actor_id=current_user.id,
            anterior_usuario_id=anterior_aprobador,
            tipo="aprobacion",
        )
        return documento

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR CRÍTICO al actualizar documento {documento_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno (Render Debug): {str(e)}"
        )


@router.delete("/documentos/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_documento(
    documento_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.anular", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["documentos.ver", "documentos.revisar", "documentos.crear", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["documentos.crear", "documentos.revisar", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["documentos.ver", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["documentos.crear", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["documentos.crear", "sistema.admin"]))
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

    _asegurar_rol_documento(db, revisor_id, ["documentos.revisar"], "revisor")
    documento.revisado_por = revisor_id
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
    current_user: Usuario = Depends(require_any_permission(["documentos.crear", "sistema.admin"]))
):
    """Solicitar aprobación de un documento (al aprobador asignado)"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # CORREGIDO: verificar que tenga un aprobador asignado (campo aprobado_por)
    if not documento.aprobado_por:
        raise HTTPException(status_code=400, detail="El documento no tiene un aprobador asignado. Edite el documento para asignar un aprobador.")

    _asegurar_rol_documento(db, documento.aprobado_por, ["documentos.aprobar"], "aprobador")
    
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
    current_user: Usuario = Depends(require_any_permission(["documentos.aprobar", "sistema.admin"]))
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
    current_user: Usuario = Depends(require_any_permission(["documentos.aprobar", "sistema.admin"]))
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
