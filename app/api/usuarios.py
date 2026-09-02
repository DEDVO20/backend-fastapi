"""
Endpoints CRUD para gestión de usuarios
"""
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..models.usuario import Usuario, Area, Rol, Permiso, UsuarioRol, RolPermiso
from ..schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioWithArea,
    AreaCreate,
    AreaUpdate,
    AreaResponse,
    RolCreate,
    RolUpdate,
    RolResponse,
    PermisoResponse,
    RolPermisoCreate,
    AsignarPermisosRolRequest,
    CargaMasivaJsonRequest,
    SincronizacionRbacResponse,
)
from passlib.context import CryptContext
from ..api.dependencies import get_current_user, require_any_permission, user_has_any_permission
from ..utils.codigos import asignar_codigo

router = APIRouter(prefix="/api/v1", tags=["usuarios"])

# Configuración para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash de contraseña usando bcrypt"""
    return pwd_context.hash(password)


def _cargar_usuario(db: Session, usuario_id: UUID) -> Optional[Usuario]:
    """Carga un usuario con área, roles y permisos para serializar la respuesta."""
    return db.query(Usuario).options(
        joinedload(Usuario.area),
        joinedload(Usuario.roles).joinedload(UsuarioRol.rol).joinedload(Rol.permisos).joinedload(RolPermiso.permiso),
    ).filter(Usuario.id == usuario_id).first()


def _usuario_respuesta(usuario: Usuario) -> UsuarioWithArea:
    user_data = UsuarioWithArea.model_validate(usuario)
    user_data.permisos = usuario.permisos_codes
    return user_data


def _reemplazar_roles(db: Session, usuario_id: UUID, rol_ids: List[UUID]) -> None:
    unique_ids = list(dict.fromkeys(rol_ids))
    if unique_ids:
        encontrados = {row[0] for row in db.query(Rol.id).filter(Rol.id.in_(unique_ids)).all()}
        if len(encontrados) != len(unique_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uno o más roles no existen o no son válidos",
            )
    db.query(UsuarioRol).filter(UsuarioRol.usuario_id == usuario_id).delete(synchronize_session=False)
    db.flush()
    for rol_id in unique_ids:
        db.add(UsuarioRol(usuario_id=usuario_id, rol_id=rol_id))
    db.flush()


# ======================
# Endpoints de Áreas
# ======================

@router.get("/areas", response_model=List[AreaResponse])
def listar_areas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission([
        "areas.gestionar",
        "usuarios.crear",
        "usuarios.ver",
        "usuarios.gestion",
        "documentos.ver",
        "documentos.crear",
        "documentos.revisar",
        "procesos.ver",
        "procesos.admin",
        "calidad.ver",
        "noconformidades.reportar",
        "noconformidades.gestion",
        "sistema.config",
        "sistema.admin",
    ]))
):
    """Listar todas las áreas con sus responsables asignados"""
    from ..models.sistema import Asignacion
    
    areas = db.query(Area).options(
        joinedload(Area.asignaciones).joinedload(Asignacion.usuario)
    ).offset(skip).limit(limit).all()
    return areas


@router.post("/areas", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
def crear_area(
    area: AreaCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["areas.gestionar", "usuarios.gestion", "sistema.admin"]))
):
    """Crear una nueva área"""
    area_data = area.model_dump()
    area_data["codigo"] = asignar_codigo(db, Area, area_data.get("codigo"), "AREA-")
    nueva_area = Area(**area_data)
    db.add(nueva_area)
    db.commit()
    db.refresh(nueva_area)
    return nueva_area


@router.get("/areas/{area_id}", response_model=AreaResponse)
def obtener_area(
    area_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["areas.gestionar", "usuarios.gestion", "sistema.admin"]))
):
    """Obtener un área por ID"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada"
        )
    return area


@router.put("/areas/{area_id}", response_model=AreaResponse)
def actualizar_area(
    area_id: UUID, 
    area_update: AreaUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["areas.gestionar", "usuarios.gestion", "sistema.admin"]))
):
    """Actualizar un área"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada"
        )
    
    # Actualizar campos
    update_data = area_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(area, field, value)
    
    db.commit()
    db.refresh(area)
    return area


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_area(
    area_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["areas.gestionar", "usuarios.gestion", "sistema.admin"]))
):
    """Eliminar un área y sus relaciones"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada"
        )
    
    try:
        from ..models.usuario import Usuario
        from ..models.proceso import Proceso
        from ..models.calidad import ObjetivoCalidad
        from ..models.capacitacion import Capacitacion
        from ..models.sistema import Asignacion
        from ..models.ticket import Ticket

        # Desvincular usuarios, procesos y demás registros para poder eliminar el área
        db.query(Usuario).filter(Usuario.area_id == area_id).update(
            {Usuario.area_id: None},
            synchronize_session=False,
        )
        db.query(Proceso).filter(Proceso.area_id == area_id).update(
            {Proceso.area_id: None},
            synchronize_session=False,
        )
        db.query(ObjetivoCalidad).filter(ObjetivoCalidad.area_id == area_id).update(
            {ObjetivoCalidad.area_id: None},
            synchronize_session=False,
        )
        db.query(Capacitacion).filter(Capacitacion.area_id == area_id).update(
            {Capacitacion.area_id: None},
            synchronize_session=False,
        )
        db.query(Ticket).filter(Ticket.area_destino_id == area_id).update(
            {Ticket.area_destino_id: None},
            synchronize_session=False,
        )
        db.query(Asignacion).filter(Asignacion.area_id == area_id).delete(synchronize_session=False)
        db.flush()

        db.delete(area)
        db.commit()
        return None
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR al eliminar área {area_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el área: {str(e)}"
        )


# ======================
# Endpoints de Roles
# ======================

@router.get("/roles", response_model=List[RolResponse])
def listar_roles(
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.crear", "usuarios.gestion", "sistema.admin"]))
):
    """Listar roles activos del SGC"""
    from sqlalchemy.orm import joinedload
    roles = db.query(Rol).options(
        joinedload(Rol.permisos).joinedload(RolPermiso.permiso)
    ).filter(Rol.activo.is_(True)).offset(skip).limit(limit).all()
    return roles


@router.post("/roles/sincronizar-sgc", response_model=SincronizacionRbacResponse)
def sincronizar_catalogo_sgc(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.gestion", "sistema.admin"]))
):
    """Aplica el catálogo RBAC SGC-IUDC 2026 (roles, permisos y migración de obsoletos)."""
    from ..db.sync_rbac import sincronizar_rbac_sgc

    resultado = sincronizar_rbac_sgc(db)
    resultado.pop("roles", None)
    return resultado


@router.post("/roles", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
def crear_rol(
    rol: RolCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.gestion", "sistema.admin"]))
):
    """Crear un nuevo rol"""
    # Verificar si la clave ya existe
    db_rol = db.query(Rol).filter(Rol.clave == rol.clave).first()
    if db_rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clave del rol ya existe"
        )
    
    nuevo_rol = Rol(**rol.model_dump())
    db.add(nuevo_rol)
    db.commit()
    db.refresh(nuevo_rol)
    return nuevo_rol


@router.get("/roles/{rol_id}", response_model=RolResponse)
def obtener_rol(
    rol_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.gestion", "sistema.admin"]))
):
    """Obtener un rol por ID"""
    from sqlalchemy.orm import joinedload
    rol = db.query(Rol).options(
        joinedload(Rol.permisos).joinedload(RolPermiso.permiso)
    ).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return rol


@router.put("/roles/{rol_id}", response_model=RolResponse)
def actualizar_rol(
    rol_id: UUID, 
    rol_update: RolUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.gestion", "sistema.admin"]))
):
    """Actualizar un rol"""
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    update_data = rol_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rol, field, value)
    
    db.commit()
    db.refresh(rol)
    return rol


@router.delete("/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(
    rol_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.gestion", "sistema.admin"]))
):
    """Eliminar un rol y sus relaciones"""
    from ..db.rbac_catalog import CLAVES_ROLES_CANONICOS

    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    if (rol.clave or "").strip().lower() in CLAVES_ROLES_CANONICOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un rol canónico del SGC. Reasigne usuarios o ajuste permisos.",
        )
    
    try:
        # Verificar si hay usuarios asignados a este rol
        usuarios_count = db.query(UsuarioRol).filter(UsuarioRol.rol_id == rol_id).count()
        if usuarios_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el rol porque tiene {usuarios_count} usuario(s) asignado(s). Primero reasigne o elimine los usuarios."
            )
        
        # Eliminar permisos asociados al rol
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol_id).delete(synchronize_session=False)
        db.flush()
        
        # Eliminar el rol
        db.delete(rol)
        db.commit()
        return None
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR al eliminar rol {rol_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el rol: {str(e)}"
        )


@router.get("/permisos", response_model=List[PermisoResponse])
def listar_permisos(
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.gestion", "sistema.admin"]))
):
    """Listar permisos activos del catálogo"""
    permisos = db.query(Permiso).filter(Permiso.activo.is_(True)).offset(skip).limit(limit).all()
    return permisos


@router.post("/roles/{rol_id}/permisos", status_code=status.HTTP_201_CREATED)
def asignar_permisos_rol(
    rol_id: UUID, 
    permisos_data: AsignarPermisosRolRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.gestion", "sistema.admin"]))
):
    """Asignar permisos a un rol (reemplaza los existentes)"""
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    permiso_ids = list(dict.fromkeys(permisos_data.permiso_ids))
    if permiso_ids:
        encontrados = {row[0] for row in db.query(Permiso.id).filter(Permiso.id.in_(permiso_ids)).all()}
        if len(encontrados) != len(permiso_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uno o más permisos no existen o no son válidos",
            )

    db.query(RolPermiso).filter(RolPermiso.rol_id == rol_id).delete(synchronize_session=False)
    db.flush()

    for permiso_id in permiso_ids:
        db.add(RolPermiso(rol_id=rol_id, permiso_id=permiso_id))

    db.commit()
    return {"message": "Permisos actualizados correctamente"}


# ======================
# Endpoints de Usuarios
# ======================

@router.get("/usuarios", response_model=List[UsuarioWithArea])
def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission([
        "usuarios.ver",
        "usuarios.gestion",
        "usuarios.crear",
        "documentos.crear",
        "documentos.revisar",
        "documentos.aprobar",
        "areas.gestionar",
        "sistema.admin",
    ]))
):
    """Listar todos los usuarios"""
    query = db.query(Usuario).options(
        joinedload(Usuario.area),
        joinedload(Usuario.roles).joinedload(UsuarioRol.rol).joinedload(Rol.permisos).joinedload(RolPermiso.permiso),
    )
    
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    
    usuarios = query.offset(skip).limit(limit).all()
    return [_usuario_respuesta(usuario) for usuario in usuarios]


@router.get("/usuarios/carga-masiva/plantilla")
def descargar_plantilla_carga_masiva(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.crear", "usuarios.gestion", "sistema.admin"]))
):
    """Descarga plantilla Excel con ejemplos y catálogos de áreas/roles reales."""
    from ..utils.carga_masiva import generar_plantilla_excel

    areas = db.query(Area).order_by(Area.codigo).all()
    roles = db.query(Rol).order_by(Rol.clave).all()
    contenido = generar_plantilla_excel(areas, roles)
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_usuarios.xlsx"},
    )


@router.get("/usuarios/carga-masiva/exportar")
def exportar_usuarios_plataforma(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.ver", "usuarios.crear", "usuarios.gestion", "sistema.admin"]))
):
    """Exporta los usuarios actuales de la plataforma a Excel."""
    from ..utils.carga_masiva import generar_exportacion_usuarios

    contenido = generar_exportacion_usuarios(db)
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=usuarios_plataforma.xlsx"},
    )


@router.post("/usuarios", response_model=UsuarioWithArea, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    usuario: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.crear", "usuarios.gestion", "sistema.admin"]))
):
    """Crear un nuevo usuario"""
    # Verificar si el documento ya existe
    db_usuario_doc = db.query(Usuario).filter(Usuario.documento == usuario.documento).first()
    if db_usuario_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El documento ya está registrado"
        )
    
    # Verificar si el nombre de usuario ya existe
    db_usuario_username = db.query(Usuario).filter(Usuario.nombre_usuario == usuario.nombre_usuario).first()
    if db_usuario_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe"
        )
    
    usuario_dict = usuario.model_dump()
    contrasena = usuario_dict.pop('contrasena')
    rol_ids = usuario_dict.pop('rol_ids', [])
    
    usuario_dict['contrasena_hash'] = hash_password(contrasena)
    
    nuevo_usuario = Usuario(**usuario_dict)
    db.add(nuevo_usuario)
    db.flush()

    try:
        _reemplazar_roles(db, nuevo_usuario.id, rol_ids)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo crear el usuario: hay datos duplicados o roles inválidos",
        )

    creado = _cargar_usuario(db, nuevo_usuario.id)
    if not creado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return _usuario_respuesta(creado)


@router.get("/usuarios/{usuario_id}", response_model=UsuarioWithArea)
def obtener_usuario(
    usuario_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.ver", "usuarios.gestion", "sistema.admin"]))
):
    """Obtener un usuario por ID con sus permisos"""
    usuario = _cargar_usuario(db, usuario_id)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return _usuario_respuesta(usuario)


@router.put("/usuarios/{usuario_id}", response_model=UsuarioWithArea)
def actualizar_usuario(
    usuario_id: UUID, 
    usuario_update: UsuarioUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.editar", "usuarios.gestion", "sistema.admin"]))
):
    """Actualizar un usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    update_data = usuario_update.model_dump(exclude_unset=True)
    rol_ids = update_data.pop("rol_ids", None)
    contrasena = update_data.pop("contrasena", None)

    if "documento" in update_data and update_data["documento"] is not None:
        duplicado = db.query(Usuario).filter(
            Usuario.documento == update_data["documento"],
            Usuario.id != usuario_id,
        ).first()
        if duplicado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El documento ya está registrado",
            )

    if update_data.get("nombre_usuario"):
        duplicado = db.query(Usuario).filter(
            Usuario.nombre_usuario == update_data["nombre_usuario"],
            Usuario.id != usuario_id,
        ).first()
        if duplicado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya existe",
            )

    try:
        if rol_ids is not None:
            _reemplazar_roles(db, usuario_id, rol_ids)
            db.expire(usuario, ["roles"])

        if contrasena:
            update_data["contrasena_hash"] = hash_password(contrasena)

        for field, value in update_data.items():
            setattr(usuario, field, value)

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo actualizar el usuario: hay datos duplicados o referencias inválidas",
        )
    except Exception as e:
        db.rollback()
        print(f"ERROR al actualizar usuario {usuario_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el usuario: {str(e)}",
        )

    usuario = _cargar_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return _usuario_respuesta(usuario)


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.eliminar", "usuarios.gestion", "sistema.admin"]))
):
    """Eliminar un usuario de forma permanente. Si hay FKs bloqueantes, se desactiva."""
    if current_user.id == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede eliminar su propio usuario mientras tiene la sesión activa",
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    from ..models.ticket import Ticket
    from ..models.historial import HistorialEstado
    from ..models.sistema import Asignacion, Notificacion

    try:
        db.query(Ticket).filter(Ticket.asignado_a == usuario_id).update(
            {Ticket.asignado_a: None},
            synchronize_session=False,
        )
        db.query(Ticket).filter(Ticket.solicitante_id == usuario_id).delete(synchronize_session=False)
        db.query(HistorialEstado).filter(HistorialEstado.usuario_id == usuario_id).delete(synchronize_session=False)
        db.query(UsuarioRol).filter(UsuarioRol.usuario_id == usuario_id).delete(synchronize_session=False)
        db.query(Asignacion).filter(Asignacion.usuario_id == usuario_id).delete(synchronize_session=False)
        db.query(Notificacion).filter(Notificacion.usuario_id == usuario_id).delete(synchronize_session=False)

        db.query(Usuario).filter(Usuario.id == usuario_id).delete(synchronize_session=False)
        db.commit()
        return None
    except IntegrityError:
        db.rollback()
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        usuario.activo = False
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"ERROR al eliminar usuario {usuario_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el usuario: {str(e)}",
        )


# ======================
# Carga Masiva de Usuarios
# ======================

def _carga_masiva_http(df, db: Session):
    from ..utils.carga_masiva import ejecutar_carga

    try:
        return ejecutar_carga(df, db)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando el archivo: {str(e)}",
        )


@router.post("/usuarios/carga-masiva/json", response_model=dict)
def carga_masiva_usuarios_json(
    payload: CargaMasivaJsonRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.crear", "usuarios.gestion", "sistema.admin"]))
):
    """Carga masiva desde filas JSON (el Excel se lee en el navegador)."""
    from ..utils.carga_masiva import leer_filas_json

    try:
        df = leer_filas_json(payload.filas)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return _carga_masiva_http(df, db)


@router.post("/usuarios/carga-masiva", response_model=dict)
async def carga_masiva_usuarios(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.crear", "usuarios.gestion", "sistema.admin"]))
):
    """
    Carga masiva de usuarios desde archivo Excel o CSV
    
    Formato del archivo:
    - documento, nombre, segundo_nombre, primer_apellido, segundo_apellido
    - correo_electronico, nombre_usuario, contrasena
    - area_codigo, roles (separados por coma), activo
    """
    from ..utils.carga_masiva import validar_archivo, leer_archivo

    valido, mensaje = validar_archivo(file)
    if not valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )

    contenido = await file.read()
    if not contenido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío"
        )
    if len(contenido) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no puede superar los 5MB"
        )

    try:
        df = leer_archivo(contenido, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _carga_masiva_http(df, db)


# ======================
# Foto de Perfil
# ======================

@router.post("/usuarios/{usuario_id}/foto-perfil")
async def subir_foto_perfil(
    usuario_id: UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.editar", "usuarios.gestion", "sistema.admin", "documentos.ver", "documentos.crear", "auditorias.ver", "calidad.ver", "capacitaciones.gestion"]))
):
    """Subir o actualizar foto de perfil del usuario"""
    from fastapi import UploadFile
    import tempfile
    import os
    from ..utils.image_processing import validate_image, process_avatar
    from ..utils.supabase_client import upload_avatar, delete_avatar, get_file_name_from_url
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    es_mi_perfil = usuario.id == current_user.id
    puede_editar_usuarios = user_has_any_permission(current_user, ["usuarios.editar", "usuarios.gestion", "sistema.admin"])
    if not es_mi_perfil and not puede_editar_usuarios:
        raise HTTPException(status_code=403, detail="No autorizado para actualizar esta foto de perfil")
    
    try:
        file_content = await file.read()
        valido, mensaje = validate_image(file_content)
        if not valido:
            raise HTTPException(status_code=400, detail=mensaje)
        
        exito, file_name_or_error, processed_content = process_avatar(file_content, str(usuario_id))
        if not exito:
            raise HTTPException(status_code=500, detail=f"Error procesando imagen: {file_name_or_error}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webp') as tmp_file:
            tmp_file.write(processed_content)
            tmp_path = tmp_file.name
        
        try:
            exito_upload, url_or_error = upload_avatar(tmp_path, file_name_or_error)
            if not exito_upload:
                raise HTTPException(status_code=500, detail=f"Error subiendo imagen: {url_or_error}")
            
            if usuario.foto_url:
                old_file_name = get_file_name_from_url(usuario.foto_url)
                if old_file_name:
                    delete_avatar(old_file_name)
            
            usuario.foto_url = url_or_error
            db.commit()
            db.refresh(usuario)
            
            return {"message": "Foto actualizada", "foto_url": url_or_error}
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/usuarios/{usuario_id}/foto-perfil")
def eliminar_foto_perfil(
    usuario_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["usuarios.editar", "usuarios.gestion", "sistema.admin", "documentos.ver", "documentos.crear", "auditorias.ver", "calidad.ver", "capacitaciones.gestion"]))
):
    """Eliminar foto de perfil del usuario"""
    from ..utils.supabase_client import delete_avatar, get_file_name_from_url
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    es_mi_perfil = usuario.id == current_user.id
    puede_editar_usuarios = user_has_any_permission(current_user, ["usuarios.editar", "usuarios.gestion", "sistema.admin"])
    if not es_mi_perfil and not puede_editar_usuarios:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar esta foto de perfil")
    
    if not usuario.foto_url:
        raise HTTPException(status_code=400, detail="No tiene foto de perfil")
    
    try:
        file_name = get_file_name_from_url(usuario.foto_url)
        if file_name:
            delete_avatar(file_name)
        
        usuario.foto_url = None
        db.commit()
        return {"message": "Foto eliminada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
