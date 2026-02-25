"""
Dependencias de autenticación y autorización.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Iterable, Set

from ..database import get_db
from ..models.usuario import Usuario
from ..utils.security import decode_access_token

# Esquema de seguridad Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Obtener usuario actual desde el token JWT
    
    Args:
        credentials: Credenciales HTTP Bearer
        db: Sesión de base de datos
    
    Returns:
        Usuario autenticado
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extraer token
        token = credentials.credentials
        
        # Decodificar token
        usuario_id = decode_access_token(token)
        
        if usuario_id is None:
            raise credentials_exception
        
        # Buscar usuario en base de datos
        # Pre-cargar relación con área, roles y permisos para el RBAC
        from sqlalchemy.orm import joinedload
        from ..models.usuario import UsuarioRol, Rol, RolPermiso
        
        usuario = db.query(Usuario).options(
            joinedload(Usuario.area),
            joinedload(Usuario.roles).joinedload(UsuarioRol.rol).joinedload(Rol.permisos).joinedload(RolPermiso.permiso)
        ).filter(Usuario.id == usuario_id).first()
        
        if usuario is None:
            raise credentials_exception
        
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        return usuario
        
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
    except Exception as e:
        # Capturar errores de base de datos u otros errores inesperados
        print(f"ERROR en get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al validar credenciales"
        )


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Verificar que el usuario actual esté activo
    
    Args:
        current_user: Usuario actual
    
    Returns:
        Usuario activo
    
    Raises:
        HTTPException: Si el usuario está inactivo
    """
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user


PERMISSION_ALIASES: dict[str, set[str]] = {
    "sistema.config": {"sistema.config", "sistema.configurar"},
    "usuarios.gestion": {"usuarios.gestion", "usuarios.crear", "usuarios.editar", "usuarios.eliminar"},
    "areas.gestionar": {"areas.gestionar", "procesos.admin"},
    "noconformidades.gestion": {"noconformidades.gestion", "no_conformidades.gestionar", "acciones_correctivas.gestionar"},
    "noconformidades.reportar": {"noconformidades.reportar"},
    "noconformidades.cerrar": {"noconformidades.cerrar"},
    "riesgos.gestion": {"riesgos.gestion", "riesgos.administrar"},
    "capacitaciones.gestion": {"capacitaciones.gestion", "capacitaciones.gestionar"},
}


def _expand_permission_codes(required_permissions: Iterable[str]) -> Set[str]:
    expanded: Set[str] = set()
    for code in required_permissions:
        expanded.update(PERMISSION_ALIASES.get(code, {code}))
    return expanded


def user_has_any_permission(current_user: Usuario, required_permissions: Iterable[str]) -> bool:
    user_perms = set(getattr(current_user, "permisos_codes", []) or [])
    if "sistema.admin" in user_perms:
        return True
    return bool(user_perms.intersection(_expand_permission_codes(required_permissions)))


def require_any_permission(required_permissions: list[str]):
    async def dependency(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if not user_has_any_permission(current_user, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para esta operación",
            )
        return current_user

    return dependency
