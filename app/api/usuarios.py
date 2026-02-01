"""
Endpoints CRUD para gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from typing import List
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
    RolPermisoCreate
)
from passlib.context import CryptContext
from ..api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["usuarios"])

# Configuración para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash de contraseña usando bcrypt"""
    return pwd_context.hash(password)


# ======================
# Endpoints de Áreas
# ======================

@router.get("/areas", response_model=List[AreaResponse])
def listar_areas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todas las áreas"""
    areas = db.query(Area).offset(skip).limit(limit).all()
    return areas


@router.post("/areas", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
def crear_area(
    area: AreaCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una nueva área"""
    # Verificar si el código ya existe
    db_area = db.query(Area).filter(Area.codigo == area.codigo).first()
    if db_area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de área ya existe"
        )
    
    # Crear nueva área
    nueva_area = Area(**area.model_dump())
    db.add(nueva_area)
    db.commit()
    db.refresh(nueva_area)
    return nueva_area


@router.get("/areas/{area_id}", response_model=AreaResponse)
def obtener_area(
    area_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un área"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada"
        )
    
    db.delete(area)
    db.commit()
    return None


# ======================
# Endpoints de Roles
# ======================

@router.get("/roles", response_model=List[RolResponse])
def listar_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los roles"""
    from sqlalchemy.orm import joinedload
    roles = db.query(Rol).options(
        joinedload(Rol.permisos).joinedload(RolPermiso.permiso)
    ).offset(skip).limit(limit).all()
    return roles


@router.post("/roles", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
def crear_rol(
    rol: RolCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un rol por ID"""
    from sqlalchemy.orm import joinedload
    rol = db.query(Rol).options(joinedload(Rol.permisos)).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    print(f"DEBUG: obtener_rol {rol.nombre} - Permisos encontrados: {len(rol.permisos)}")
    return rol


@router.put("/roles/{rol_id}", response_model=RolResponse)
def actualizar_rol(
    rol_id: UUID, 
    rol_update: RolUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un rol"""
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    db.delete(rol)
    db.commit()
    return None


@router.get("/permisos", response_model=List[PermisoResponse])
def listar_permisos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los permisos"""
    permisos = db.query(Permiso).offset(skip).limit(limit).all()
    return permisos


@router.post("/roles/{rol_id}/permisos", status_code=status.HTTP_201_CREATED)
def asignar_permisos_rol(
    rol_id: UUID, 
    permisos_data: dict,  # Espera {"permisoIds": ["id1", "id2"]}
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Asignar permisos a un rol (reemplaza los existentes)"""
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Limpiar permisos existentes
    db.query(RolPermiso).filter(RolPermiso.rol_id == rol_id).delete(synchronize_session=False)
    db.flush()
    
    # Asignar nuevos permisos (deduplicados)
    permiso_ids = list(set(permisos_data.get("permisoIds", [])))
    print(f"DEBUG: Asignando {len(permiso_ids)} permisos (únicos) al rol {rol_id}")
    
    for permiso_id in permiso_ids:
        nuevo_rol_permiso = RolPermiso(rol_id=rol_id, permiso_id=permiso_id)
        db.add(nuevo_rol_permiso)
    
    db.commit()
    print(f"DEBUG: Guardado exitoso para rol {rol_id}")
    return {"message": "Permisos actualizados correctamente"}


# ======================
# Endpoints de Usuarios
# ======================

@router.get("/usuarios", response_model=List[UsuarioWithArea])
def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db)
):
    """Listar todos los usuarios"""
    query = db.query(Usuario)
    
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    
    usuarios = query.offset(skip).limit(limit).all()
    return usuarios


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    usuario: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    
    # Crear nuevo usuario
    usuario_dict = usuario.model_dump()
    contrasena = usuario_dict.pop('contrasena')
    rol_ids = usuario_dict.pop('rol_ids', [])
    
    usuario_dict['contrasena_hash'] = hash_password(contrasena)
    
    nuevo_usuario = Usuario(**usuario_dict)
    db.add(nuevo_usuario)
    db.flush()  # Para obtener el ID del usuario
    
    # Asignar roles
    for rol_id in rol_ids:
        usuario_rol = UsuarioRol(usuario_id=nuevo_usuario.id, rol_id=rol_id)
        db.add(usuario_rol)
        
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.get("/usuarios/{usuario_id}", response_model=UsuarioWithArea)
def obtener_usuario(
    usuario_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un usuario por ID con sus permisos"""
    from sqlalchemy.orm import joinedload
    from ..models.usuario import UsuarioRol, Rol, RolPermiso
    usuario = db.query(Usuario).options(
        joinedload(Usuario.area),
        joinedload(Usuario.roles).joinedload(UsuarioRol.rol).joinedload(Rol.permisos).joinedload(RolPermiso.permiso)
    ).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Mapear permisos manualmente para asegurar consistencia
    user_data = UsuarioWithArea.model_validate(usuario)
    user_data.permisos = usuario.permisos_codes
    return user_data


@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: UUID, 
    usuario_update: UsuarioUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar campos
    update_data = usuario_update.model_dump(exclude_unset=True)
    
    # Manejar roles si se proporcionan
    rol_ids = update_data.pop('rol_ids', None)
    if rol_ids is not None:
        from ..models.usuario import UsuarioRol
        # Eliminar roles anteriores
        db.query(UsuarioRol).filter(UsuarioRol.usuario_id == usuario_id).delete()
        # Agregar nuevos
        for rol_id in rol_ids:
            nuevo_rol = UsuarioRol(usuario_id=usuario_id, rol_id=rol_id)
            db.add(nuevo_rol)
    
    # Si se proporciona nueva contraseña, hashearla
    if 'contrasena' in update_data:
        contrasena = update_data.pop('contrasena')
        update_data['contrasena_hash'] = hash_password(contrasena)
    
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un usuario (eliminación suave - marcar como inactivo)"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Eliminación suave
    usuario.activo = False
    db.commit()
    return None


# ======================
# Carga Masiva de Usuarios
# ======================

@router.post("/usuarios/carga-masiva", response_model=dict)
async def carga_masiva_usuarios(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Carga masiva de usuarios desde archivo Excel o CSV
    
    Formato del archivo:
    - documento, nombre, segundo_nombre, primer_apellido, segundo_apellido
    - correo_electronico, nombre_usuario, contrasena
    - area_codigo, roles (separados por coma), activo
    """
    from fastapi import UploadFile
    from ..utils.carga_masiva import (
        validar_archivo,
        leer_archivo,
        validar_columnas,
        procesar_fila,
        cargar_caches
    )
    from ..schemas.usuario import (
        CargaMasivaResultado,
        CargaMasivaUsuarioExitoso,
        CargaMasivaErrorDetalle
    )
    
    # Validar archivo
    valido, mensaje = validar_archivo(file)
    if not valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )
    
    try:
        # Leer contenido del archivo
        contenido = await file.read()
        
        # Leer archivo como DataFrame
        df = leer_archivo(contenido, file.filename)
        
        # Validar columnas
        columnas_faltantes = validar_columnas(df)
        if columnas_faltantes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Columnas faltantes en el archivo: {', '.join(columnas_faltantes)}"
            )
        
        # Validar límite de filas
        if len(df) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no puede contener más de 1000 usuarios"
            )
        
        # Cargar caches de áreas y roles
        areas_cache, roles_cache = cargar_caches(db)
        
        # Procesar cada fila
        exitosos = []
        errores = []
        
        for idx, fila in df.iterrows():
            fila_num = idx + 2  # +2 porque idx empieza en 0 y hay header
            
            exito, resultado = procesar_fila(
                fila_num,
                fila,
                db,
                areas_cache,
                roles_cache
            )
            
            if exito:
                # resultado es el usuario creado
                exitosos.append(CargaMasivaUsuarioExitoso(
                    fila=fila_num,
                    nombre_usuario=resultado.nombre_usuario,
                    nombre_completo=f"{resultado.nombre} {resultado.primer_apellido}",
                    correo_electronico=resultado.correo_electronico
                ))
            else:
                # resultado es lista de errores
                errores.extend(resultado)
        
        # Si hay errores, hacer rollback
        if errores:
            db.rollback()
        else:
            db.commit()
        
        # Preparar respuesta
        resultado = CargaMasivaResultado(
            total_procesados=len(df),
            exitosos=len(exitosos),
            errores=len(errores),
            detalles_exitosos=exitosos,
            detalles_errores=errores
        )
        
        return resultado.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando el archivo: {str(e)}"
        )


# ======================
# Foto de Perfil
# ======================

@router.post("/usuarios/{usuario_id}/foto-perfil")
async def subir_foto_perfil(
    usuario_id: UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar foto de perfil del usuario"""
    from ..utils.supabase_client import delete_avatar, get_file_name_from_url
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
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
