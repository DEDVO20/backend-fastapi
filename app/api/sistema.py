"""
Endpoints CRUD para sistema (notificaciones, configuraciones, asignaciones)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID
from datetime import datetime
import hashlib
import json

from ..database import get_db
from ..models.sistema import (
    Notificacion,
    Configuracion,
    Asignacion,
    FormularioDinamico,
    CampoFormulario,
    RespuestaFormulario,
)
from ..models.audit_log import AuditLog
from ..schemas.sistema import (
    NotificacionCreate,
    NotificacionUpdate,
    NotificacionResponse,
    ConfiguracionCreate,
    ConfiguracionUpdate,
    ConfiguracionResponse,
    AsignacionCreate,
    AsignacionResponse,
    FormularioDinamicoCreate,
    FormularioDinamicoUpdate,
    FormularioDinamicoResponse,
    CampoFormularioCreate,
    CampoFormularioUpdate,
    CampoFormularioResponse,
    RespuestaFormularioCreate,
    RespuestaFormularioUpdate,
    RespuestaFormularioResponse,
    AuditLogResponse,
)
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

router = APIRouter(prefix="/api/v1", tags=["sistema"])

ISO_AUDITORIA_CAMPOS_REQUERIDOS = {
    "clausula_iso": "Cláusula ISO 9001 aplicable",
    "criterio_auditoria": "Criterio de auditoría",
    "evidencia_objetiva": "Evidencia objetiva",
    "resultado_auditoria": "Resultado (Conforme/No conforme)",
    "conclusion_auditoria": "Conclusión de auditoría",
}
ISO_SECCIONES_VALIDAS = {
    "contexto",
    "liderazgo",
    "planificacion",
    "apoyo",
    "operacion",
    "evaluacion",
    "mejora",
}


def _validar_tipo_campo_con_opciones(tipo_campo: str, opciones):
    if tipo_campo in {"select", "radio", "checkbox", "multiselect"} and not opciones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los campos de selección requieren opciones.",
        )


def _es_formulario_iso_auditoria(formulario: FormularioDinamico) -> bool:
    return (
        str(formulario.modulo).strip().lower() == "auditorias"
        and str(formulario.entidad_tipo).strip().lower() == "auditoria"
    )


def _validar_formulario_iso_completo(db: Session, formulario: FormularioDinamico) -> None:
    if not _es_formulario_iso_auditoria(formulario):
        return

    campos = db.query(CampoFormulario).filter(
        CampoFormulario.formulario_id == formulario.id,
        CampoFormulario.activo.is_(True),
    ).all()
    nombres = {str(c.nombre).strip().lower() for c in campos}
    faltantes = [campo for campo in ISO_AUDITORIA_CAMPOS_REQUERIDOS.keys() if campo not in nombres]
    if faltantes:
        etiquetas = ", ".join(ISO_AUDITORIA_CAMPOS_REQUERIDOS[c] for c in faltantes)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El formulario de auditoría ISO 9001 no está completo. "
                f"Faltan campos obligatorios: {etiquetas}"
            ),
        )

    faltan_clausula = [c.etiqueta for c in campos if not (c.clausula_iso and str(c.clausula_iso).strip())]
    if faltan_clausula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cada pregunta debe tener cláusula ISO asignada antes de aprobar.",
        )

    secciones_invalidas = [
        c.etiqueta for c in campos if c.seccion_iso and str(c.seccion_iso).strip().lower() not in ISO_SECCIONES_VALIDAS
    ]
    if secciones_invalidas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sección ISO inválida en campos: {', '.join(secciones_invalidas)}",
        )


def _is_admin_user(current_user: Usuario) -> bool:
    # Compatibilidad con múltiples convenciones de permisos/roles existentes.
    permisos = set(getattr(current_user, "permisos_codes", []) or getattr(current_user, "permisos", []) or [])
    if "sistema.admin" in permisos:
        return True
    try:
        role_keys = {ur.rol.clave for ur in getattr(current_user, "roles", []) if getattr(ur, "rol", None)}
    except Exception:
        role_keys = set()
    return bool(role_keys.intersection({"ADMIN", "admin"}))


@router.get("/audit-log", response_model=List[AuditLogResponse])
def listar_audit_log(
    skip: int = 0,
    limit: int = 100,
    tabla: str = None,
    accion: str = None,
    usuario_id: UUID = None,
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if not _is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para consultar el audit log",
        )

    query = db.query(AuditLog)
    if tabla:
        query = query.filter(AuditLog.tabla == tabla)
    if accion:
        query = query.filter(AuditLog.accion == accion.upper().strip())
    if usuario_id:
        query = query.filter(AuditLog.usuario_id == usuario_id)
    if fecha_desde:
        query = query.filter(AuditLog.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(AuditLog.fecha <= fecha_hasta)

    return query.order_by(AuditLog.fecha.desc()).offset(skip).limit(limit).all()


# =========================
# Endpoints de Asignaciones
# =========================

@router.get("/asignaciones", response_model=List[AsignacionResponse])
def listar_asignaciones(
    skip: int = 0,
    limit: int = 100,
    area_id: UUID = None,
    usuario_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar asignaciones de responsables"""
    query = db.query(Asignacion).options(
        joinedload(Asignacion.area),
        joinedload(Asignacion.usuario)
    )
    
    if area_id:
        query = query.filter(Asignacion.area_id == area_id)
    if usuario_id:
        query = query.filter(Asignacion.usuario_id == usuario_id)
    
    asignaciones = query.offset(skip).limit(limit).all()
    return asignaciones


@router.post("/asignaciones", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
def crear_asignacion(
    asignacion: AsignacionCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva asignación de responsable"""
    # Verificar unicidad
    db_asignacion = db.query(Asignacion).filter(
        Asignacion.area_id == asignacion.area_id,
        Asignacion.usuario_id == asignacion.usuario_id
    ).first()
    
    if db_asignacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está asignado a esta área"
        )
    
    nueva_asignacion = Asignacion(**asignacion.model_dump())
    db.add(nueva_asignacion)
    
    try:
        db.commit()
        db.refresh(nueva_asignacion)
        # Recargar relaciones para la respuesta
        db.refresh(nueva_asignacion, attribute_names=['area', 'usuario'])
        return nueva_asignacion
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad al crear la asignación"
        )


@router.delete("/asignaciones/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(
    asignacion_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una asignación"""
    asignacion = db.query(Asignacion).filter(Asignacion.id == asignacion_id).first()
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    
    db.delete(asignacion)
    db.commit()
    return None


# ==========================
# Endpoints de Notificaciones
# ==========================

@router.get("/notificaciones", response_model=List[NotificacionResponse])
def listar_notificaciones(
    skip: int = 0,
    limit: int = 100,
    usuario_id: UUID = None,
    leida: bool = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar notificaciones del usuario autenticado."""
    if usuario_id and usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para consultar notificaciones de otro usuario",
        )

    query = db.query(Notificacion).filter(Notificacion.usuario_id == current_user.id)

    if leida is not None:
        query = query.filter(Notificacion.leida == leida)
    if tipo:
        query = query.filter(Notificacion.tipo == tipo)
    
    notificaciones = query.order_by(Notificacion.creado_en.desc()).offset(skip).limit(limit).all()
    return notificaciones


@router.post("/notificaciones", response_model=NotificacionResponse, status_code=status.HTTP_201_CREATED)
def crear_notificacion(
    notificacion: NotificacionCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva notificación"""
    nueva_notificacion = Notificacion(**notificacion.model_dump())
    db.add(nueva_notificacion)
    db.commit()
    db.refresh(nueva_notificacion)
    return nueva_notificacion


@router.get("/notificaciones/{notificacion_id}", response_model=NotificacionResponse)
def obtener_notificacion(
    notificacion_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una notificación propia por ID."""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == current_user.id,
    ).first()
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    return notificacion


@router.put("/notificaciones/{notificacion_id}", response_model=NotificacionResponse)
def actualizar_notificacion(
    notificacion_id: UUID,
    notificacion_update: NotificacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una notificación propia (marcar como leída)."""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == current_user.id,
    ).first()
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    update_data = notificacion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notificacion, field, value)
    
    db.commit()
    db.refresh(notificacion)
    return notificacion


@router.delete("/notificaciones/{notificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_notificacion(
    notificacion_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una notificación propia."""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == current_user.id,
    ).first()
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    db.delete(notificacion)
    db.commit()


# ============================
# Endpoints de Configuraciones
# ============================

@router.get("/configuraciones", response_model=List[ConfiguracionResponse])
def listar_configuraciones(
    skip: int = 0,
    limit: int = 100,
    categoria: str = None,
    activa: bool = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar configuraciones del sistema"""
    query = db.query(Configuracion)
    
    if categoria:
        query = query.filter(Configuracion.categoria == categoria)
    if activa is not None:
        query = query.filter(Configuracion.activa == activa)
    
    configuraciones = query.offset(skip).limit(limit).all()
    return configuraciones


@router.post("/configuraciones", response_model=ConfiguracionResponse, status_code=status.HTTP_201_CREATED)
def crear_configuracion(
    configuracion: ConfiguracionCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva configuración"""
    # Verificar clave única
    db_config = db.query(Configuracion).filter(Configuracion.clave == configuracion.clave).first()
    if db_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clave de configuración ya existe"
        )
    
    nueva_configuracion = Configuracion(**configuracion.model_dump())
    db.add(nueva_configuracion)
    db.commit()
    db.refresh(nueva_configuracion)
    return nueva_configuracion


@router.get("/configuraciones/{clave}", response_model=ConfiguracionResponse)
def obtener_configuracion(
    clave: str, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener una configuración por clave"""
    configuracion = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    return configuracion


@router.put("/configuraciones/{clave}", response_model=ConfiguracionResponse)
def actualizar_configuracion(
    clave: str,
    configuracion_update: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar una configuración"""
    configuracion = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    update_data = configuracion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(configuracion, field, value)
    
    db.commit()
    db.refresh(configuracion)
    return configuracion


@router.delete("/configuraciones/{clave}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_configuracion(
    clave: str, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar una configuración"""
    configuracion = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    db.delete(configuracion)
    db.commit()


# ==================================
# Endpoints de Formularios Dinámicos
# ==================================

@router.get("/formularios-dinamicos", response_model=List[FormularioDinamicoResponse])
def listar_formularios_dinamicos(
    skip: int = 0,
    limit: int = 100,
    modulo: str = None,
    entidad_tipo: str = None,
    proceso_id: UUID = None,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(FormularioDinamico)
    if modulo:
        query = query.filter(FormularioDinamico.modulo == modulo)
    if entidad_tipo:
        query = query.filter(FormularioDinamico.entidad_tipo == entidad_tipo)
    if proceso_id:
        query = query.filter(FormularioDinamico.proceso_id == proceso_id)
    if activo is not None:
        query = query.filter(FormularioDinamico.activo == activo)
    return query.order_by(FormularioDinamico.nombre.asc()).offset(skip).limit(limit).all()


@router.post("/formularios-dinamicos", response_model=FormularioDinamicoResponse, status_code=status.HTTP_201_CREATED)
def crear_formulario_dinamico(
    formulario: FormularioDinamicoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    existente = db.query(FormularioDinamico).filter(FormularioDinamico.codigo == formulario.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un formulario con ese código.")
    nuevo = FormularioDinamico(**formulario.model_dump())
    if _es_formulario_iso_auditoria(nuevo):
        nuevo.modulo = "auditorias"
        nuevo.entidad_tipo = "auditoria"
        nuevo.estado_workflow = "borrador"
        nuevo.activo = False
    db.add(nuevo)
    db.flush()
    if nuevo.activo:
        _validar_formulario_iso_completo(db, nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/formularios-dinamicos/{formulario_id}", response_model=FormularioDinamicoResponse)
def obtener_formulario_dinamico(
    formulario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == formulario_id).first()
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulario dinámico no encontrado.")
    return formulario


@router.put("/formularios-dinamicos/{formulario_id}", response_model=FormularioDinamicoResponse)
def actualizar_formulario_dinamico(
    formulario_id: UUID,
    formulario_update: FormularioDinamicoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == formulario_id).first()
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulario dinámico no encontrado.")

    if formulario.activo and formulario.estado_workflow == "aprobado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede editar una plantilla aprobada y activa. Cree una nueva versión.",
        )

    update_data = formulario_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(formulario, field, value)

    if _es_formulario_iso_auditoria(formulario):
        formulario.modulo = "auditorias"
        formulario.entidad_tipo = "auditoria"
    if formulario.activo and formulario.estado_workflow == "aprobado":
        _validar_formulario_iso_completo(db, formulario)

    db.commit()
    db.refresh(formulario)
    return formulario


@router.delete("/formularios-dinamicos/{formulario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_formulario_dinamico(
    formulario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == formulario_id).first()
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulario dinámico no encontrado.")
    if formulario.estado_workflow == "aprobado" and formulario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar una plantilla aprobada activa. Márquela obsoleta.",
        )
    db.delete(formulario)
    db.commit()
    return None


@router.post("/formularios-dinamicos/{formulario_id}/nueva-version", response_model=FormularioDinamicoResponse, status_code=status.HTTP_201_CREATED)
def crear_nueva_version_formulario(
    formulario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    actual = db.query(FormularioDinamico).filter(FormularioDinamico.id == formulario_id).first()
    if not actual:
        raise HTTPException(status_code=404, detail="Formulario dinámico no encontrado.")

    nuevo = FormularioDinamico(
        codigo=f"{actual.codigo}-v{actual.version + 1}",
        nombre=actual.nombre,
        descripcion=actual.descripcion,
        modulo=actual.modulo,
        entidad_tipo=actual.entidad_tipo,
        proceso_id=actual.proceso_id,
        activo=False,
        version=actual.version + 1,
        estado_workflow="borrador",
        parent_formulario_id=actual.id,
    )
    db.add(nuevo)
    db.flush()

    campos_actuales = db.query(CampoFormulario).filter(CampoFormulario.formulario_id == actual.id).order_by(CampoFormulario.orden.asc()).all()
    for c in campos_actuales:
        db.add(
            CampoFormulario(
                formulario_id=nuevo.id,
                proceso_id=c.proceso_id,
                nombre=c.nombre,
                etiqueta=c.etiqueta,
                tipo_campo=c.tipo_campo,
                requerido=c.requerido,
                opciones=c.opciones,
                orden=c.orden,
                activo=c.activo,
                validaciones=c.validaciones,
                seccion_iso=c.seccion_iso,
                clausula_iso=c.clausula_iso,
                subclausula_iso=c.subclausula_iso,
                evidencia_requerida=c.evidencia_requerida,
            )
        )

    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.post("/formularios-dinamicos/{formulario_id}/aprobar", response_model=FormularioDinamicoResponse)
def aprobar_formulario_dinamico(
    formulario_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == formulario_id).first()
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulario dinámico no encontrado.")

    _validar_formulario_iso_completo(db, formulario)

    db.query(FormularioDinamico).filter(
        FormularioDinamico.id != formulario.id,
        FormularioDinamico.modulo == formulario.modulo,
        FormularioDinamico.entidad_tipo == formulario.entidad_tipo,
        FormularioDinamico.proceso_id == formulario.proceso_id,
        FormularioDinamico.estado_workflow == "aprobado",
        FormularioDinamico.activo.is_(True),
    ).update(
        {
            "activo": False,
            "estado_workflow": "obsoleto",
            "vigente_hasta": datetime.utcnow(),
        },
        synchronize_session=False,
    )

    formulario.estado_workflow = "aprobado"
    formulario.activo = True
    formulario.aprobado_por = current_user.id
    formulario.fecha_aprobacion = datetime.utcnow()
    formulario.vigente_desde = datetime.utcnow()
    formulario.vigente_hasta = None

    db.commit()
    db.refresh(formulario)
    return formulario


# =============================
# Endpoints de Campos Formulario
# =============================

@router.get("/campos-formulario", response_model=List[CampoFormularioResponse])
def listar_campos_formulario(
    formulario_id: UUID = None,
    proceso_id: UUID = None,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(CampoFormulario)
    if formulario_id:
        query = query.filter(CampoFormulario.formulario_id == formulario_id)
    if proceso_id:
        query = query.filter(CampoFormulario.proceso_id == proceso_id)
    if activo is not None:
        query = query.filter(CampoFormulario.activo == activo)
    return query.order_by(CampoFormulario.orden.asc(), CampoFormulario.creado_en.asc()).all()


@router.post("/campos-formulario", response_model=CampoFormularioResponse, status_code=status.HTTP_201_CREATED)
def crear_campo_formulario(
    campo: CampoFormularioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _validar_tipo_campo_con_opciones(campo.tipo_campo, campo.opciones)
    if campo.seccion_iso and str(campo.seccion_iso).strip().lower() not in ISO_SECCIONES_VALIDAS:
        raise HTTPException(status_code=400, detail="seccion_iso no válida para marco ISO.")
    if campo.formulario_id:
        formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == campo.formulario_id).first()
        if not formulario:
            raise HTTPException(status_code=404, detail="Formulario dinámico no encontrado.")
        if formulario.estado_workflow == "aprobado" and formulario.activo:
            raise HTTPException(status_code=400, detail="No puede editar campos en una plantilla aprobada activa.")
        if _es_formulario_iso_auditoria(formulario):
            nombre = str(campo.nombre).strip().lower()
            if nombre in ISO_AUDITORIA_CAMPOS_REQUERIDOS and not campo.requerido:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo ISO obligatorio '{nombre}' debe marcarse como requerido.",
                )

    nuevo_campo = CampoFormulario(**campo.model_dump())
    db.add(nuevo_campo)
    db.commit()
    db.refresh(nuevo_campo)
    return nuevo_campo


@router.put("/campos-formulario/{campo_id}", response_model=CampoFormularioResponse)
def actualizar_campo_formulario(
    campo_id: UUID,
    campo_update: CampoFormularioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    campo = db.query(CampoFormulario).filter(CampoFormulario.id == campo_id).first()
    if not campo:
        raise HTTPException(status_code=404, detail="Campo no encontrado.")
    if campo.formulario_id:
        formulario_campo = db.query(FormularioDinamico).filter(FormularioDinamico.id == campo.formulario_id).first()
        if formulario_campo and formulario_campo.estado_workflow == "aprobado" and formulario_campo.activo:
            raise HTTPException(status_code=400, detail="No puede editar campos en una plantilla aprobada activa.")

    update_data = campo_update.model_dump(exclude_unset=True)
    tipo_objetivo = update_data.get("tipo_campo", campo.tipo_campo)
    opciones_objetivo = update_data.get("opciones", campo.opciones)
    _validar_tipo_campo_con_opciones(tipo_objetivo, opciones_objetivo)

    for field, value in update_data.items():
        setattr(campo, field, value)

    if campo.formulario_id:
        formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == campo.formulario_id).first()
        if formulario and _es_formulario_iso_auditoria(formulario):
            nombre = str(campo.nombre).strip().lower()
            if nombre in ISO_AUDITORIA_CAMPOS_REQUERIDOS and not campo.requerido:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El campo ISO obligatorio '{nombre}' debe mantenerse como requerido.",
                )

    db.commit()
    db.refresh(campo)
    return campo


@router.delete("/campos-formulario/{campo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_campo_formulario(
    campo_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    campo = db.query(CampoFormulario).filter(CampoFormulario.id == campo_id).first()
    if not campo:
        raise HTTPException(status_code=404, detail="Campo no encontrado.")
    if campo.formulario_id:
        formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == campo.formulario_id).first()
        if formulario and formulario.estado_workflow == "aprobado" and formulario.activo:
            raise HTTPException(status_code=400, detail="No puede eliminar campos en una plantilla aprobada activa.")
        if formulario and _es_formulario_iso_auditoria(formulario):
            nombre = str(campo.nombre).strip().lower()
            if nombre in ISO_AUDITORIA_CAMPOS_REQUERIDOS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"No puede eliminar el campo ISO obligatorio '{nombre}'. "
                        "Desactive el formulario o reemplácelo por equivalente."
                    ),
                )
    db.delete(campo)
    db.commit()
    return None


# ================================
# Endpoints de Respuestas Formulario
# ================================

@router.get("/respuestas-formulario", response_model=List[RespuestaFormularioResponse])
def listar_respuestas_formulario(
    auditoria_id: UUID = None,
    instancia_proceso_id: UUID = None,
    campo_formulario_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(RespuestaFormulario)
    if auditoria_id:
        query = query.filter(RespuestaFormulario.auditoria_id == auditoria_id)
    if instancia_proceso_id:
        query = query.filter(RespuestaFormulario.instancia_proceso_id == instancia_proceso_id)
    if campo_formulario_id:
        query = query.filter(RespuestaFormulario.campo_formulario_id == campo_formulario_id)
    return query.order_by(RespuestaFormulario.creado_en.asc()).all()


@router.post("/respuestas-formulario", response_model=RespuestaFormularioResponse, status_code=status.HTTP_201_CREATED)
def crear_respuesta_formulario(
    respuesta: RespuestaFormularioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if not respuesta.auditoria_id and not respuesta.instancia_proceso_id:
        raise HTTPException(
            status_code=400,
            detail="Debe enviar auditoria_id o instancia_proceso_id para registrar la respuesta.",
        )

    campo = db.query(CampoFormulario).filter(CampoFormulario.id == respuesta.campo_formulario_id).first()
    if not campo:
        raise HTTPException(status_code=404, detail="Campo de formulario no encontrado.")

    if campo.requerido and not (respuesta.valor and str(respuesta.valor).strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El campo '{campo.etiqueta}' es obligatorio.",
        )
    if campo.evidencia_requerida and not (respuesta.archivo_adjunto and str(respuesta.archivo_adjunto).strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El campo '{campo.etiqueta}' requiere evidencia adjunta.",
        )

    payload = respuesta.model_dump()
    if not payload.get("usuario_respuesta_id"):
        payload["usuario_respuesta_id"] = current_user.id
    if payload.get("archivo_adjunto"):
        hash_input = json.dumps(
            {
                "campo": str(respuesta.campo_formulario_id),
                "auditoria": str(respuesta.auditoria_id) if respuesta.auditoria_id else None,
                "archivo": payload.get("archivo_adjunto"),
                "valor": payload.get("valor"),
            },
            sort_keys=True,
        )
        payload["evidencia_hash"] = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        payload["evidencia_fecha"] = datetime.utcnow()
        payload["evidencia_usuario_id"] = current_user.id

    nueva_respuesta = RespuestaFormulario(**payload)
    db.add(nueva_respuesta)
    db.commit()
    db.refresh(nueva_respuesta)
    return nueva_respuesta


@router.put("/respuestas-formulario/{respuesta_id}", response_model=RespuestaFormularioResponse)
def actualizar_respuesta_formulario(
    respuesta_id: UUID,
    respuesta_update: RespuestaFormularioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    respuesta = db.query(RespuestaFormulario).filter(RespuestaFormulario.id == respuesta_id).first()
    if not respuesta:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada.")

    update_data = respuesta_update.model_dump(exclude_unset=True)
    campo = db.query(CampoFormulario).filter(CampoFormulario.id == respuesta.campo_formulario_id).first()
    if campo and campo.requerido:
        valor_objetivo = update_data.get("valor", respuesta.valor)
        if not (valor_objetivo and str(valor_objetivo).strip()):
            raise HTTPException(status_code=400, detail=f"El campo '{campo.etiqueta}' es obligatorio.")
    if campo and campo.evidencia_requerida:
        evidencia_objetivo = update_data.get("archivo_adjunto", respuesta.archivo_adjunto)
        if not (evidencia_objetivo and str(evidencia_objetivo).strip()):
            raise HTTPException(status_code=400, detail=f"El campo '{campo.etiqueta}' requiere evidencia adjunta.")

    if "usuario_respuesta_id" not in update_data:
        update_data["usuario_respuesta_id"] = current_user.id
    if update_data.get("archivo_adjunto"):
        hash_input = json.dumps(
            {
                "campo": str(respuesta.campo_formulario_id),
                "auditoria": str(respuesta.auditoria_id) if respuesta.auditoria_id else None,
                "archivo": update_data.get("archivo_adjunto"),
                "valor": update_data.get("valor", respuesta.valor),
            },
            sort_keys=True,
        )
        update_data["evidencia_hash"] = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        update_data["evidencia_fecha"] = datetime.utcnow()
        update_data["evidencia_usuario_id"] = current_user.id

    for field, value in update_data.items():
        setattr(respuesta, field, value)

    db.commit()
    db.refresh(respuesta)
    return respuesta
