"""
Endpoints CRUD para gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status
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
    db: Session = Depends(get_db)
):
    """Listar todas las áreas"""
    areas = db.query(Area).offset(skip).limit(limit).all()
    return areas


@router.post("/areas", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
def crear_area(area: AreaCreate, db: Session = Depends(get_db)):
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
def obtener_area(area_id: UUID, db: Session = Depends(get_db)):
    """Obtener un área por ID"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada"
        )
    return area


@router.put("/areas/{area_id}", response_model=AreaResponse)
def actualizar_area(area_id: UUID, area_update: AreaUpdate, db: Session = Depends(get_db)):
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
def eliminar_area(area_id: UUID, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """Listar todos los roles"""
    roles = db.query(Rol).offset(skip).limit(limit).all()
    return roles


@router.post("/roles", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
def crear_rol(rol: RolCreate, db: Session = Depends(get_db)):
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
def obtener_rol(rol_id: UUID, db: Session = Depends(get_db)):
    """Obtener un rol por ID"""
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return rol


@router.put("/roles/{rol_id}", response_model=RolResponse)
def actualizar_rol(rol_id: UUID, rol_update: RolUpdate, db: Session = Depends(get_db)):
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
def eliminar_rol(rol_id: UUID, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """Listar todos los permisos"""
    permisos = db.query(Permiso).offset(skip).limit(limit).all()
    return permisos


@router.post("/roles/{rol_id}/permisos", status_code=status.HTTP_201_CREATED)
def asignar_permisos_rol(
    rol_id: UUID, 
    permisos_data: dict,  # Espera {"permisoIds": ["id1", "id2"]}
    db: Session = Depends(get_db)
):
    """Asignar permisos a un rol (reemplaza los existentes)"""
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    
    # Limpiar permisos existentes
    db.query(RolPermiso).filter(RolPermiso.rol_id == rol_id).delete()
    
    # Asignar nuevos permisos
    permiso_ids = permisos_data.get("permisoIds", [])
    for permiso_id in permiso_ids:
        nuevo_rol_permiso = RolPermiso(rol_id=rol_id, permiso_id=permiso_id)
        db.add(nuevo_rol_permiso)
    
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
    db: Session = Depends(get_db)
):
    """Listar todos los usuarios"""
    query = db.query(Usuario)
    
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    
    usuarios = query.offset(skip).limit(limit).all()
    return usuarios


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
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
def obtener_usuario(usuario_id: UUID, db: Session = Depends(get_db)):
    """Obtener un usuario por ID"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario


@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(usuario_id: UUID, usuario_update: UsuarioUpdate, db: Session = Depends(get_db)):
    """Actualizar un usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar campos
    update_data = usuario_update.model_dump(exclude_unset=True)
    
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
def eliminar_usuario(usuario_id: UUID, db: Session = Depends(get_db)):
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
