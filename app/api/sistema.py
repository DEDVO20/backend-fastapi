"""
Endpoints CRUD para sistema (notificaciones, configuraciones, asignaciones)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import UUID
from datetime import datetime

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


def _validar_tipo_campo_con_opciones(tipo_campo: str, opciones):
    if tipo_campo in {"select", "radio", "checkbox", "multiselect"} and not opciones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los campos de selección requieren opciones.",
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
    """Listar notificaciones"""
    query = db.query(Notificacion)
    
    if usuario_id:
        query = query.filter(Notificacion.usuario_id == usuario_id)
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
    """Obtener una notificación por ID"""
    notificacion = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
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
    """Actualizar una notificación (marcar como leída)"""
    notificacion = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
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
    """Eliminar una notificación"""
    notificacion = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
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
    db.add(nuevo)
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

    update_data = formulario_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(formulario, field, value)

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
    db.delete(formulario)
    db.commit()
    return None


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
    if campo.formulario_id:
        formulario = db.query(FormularioDinamico).filter(FormularioDinamico.id == campo.formulario_id).first()
        if not formulario:
            raise HTTPException(status_code=404, detail="Formulario dinámico no encontrado.")

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

    update_data = campo_update.model_dump(exclude_unset=True)
    tipo_objetivo = update_data.get("tipo_campo", campo.tipo_campo)
    opciones_objetivo = update_data.get("opciones", campo.opciones)
    _validar_tipo_campo_con_opciones(tipo_objetivo, opciones_objetivo)

    for field, value in update_data.items():
        setattr(campo, field, value)

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

    payload = respuesta.model_dump()
    if not payload.get("usuario_respuesta_id"):
        payload["usuario_respuesta_id"] = current_user.id

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
    if "usuario_respuesta_id" not in update_data:
        update_data["usuario_respuesta_id"] = current_user.id

    for field, value in update_data.items():
        setattr(respuesta, field, value)

    db.commit()
    db.refresh(respuesta)
    return respuesta
