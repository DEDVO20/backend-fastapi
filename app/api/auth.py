"""
Endpoints de autenticación
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..models.usuario import Usuario
from ..schemas.auth import LoginRequest, TokenResponse, UsuarioAuth
from ..schemas.usuario import UsuarioWithArea
from ..utils.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ..api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["autenticacion"])


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario y generar token JWT
    
    Credenciales por defecto:
    - Usuario: admin
    - Contraseña: admin123
    """
    # Buscar usuario por nombre de usuario
    usuario = db.query(Usuario).filter(
        Usuario.nombre_usuario == login_data.nombre_usuario
    ).first()
    
    # Verificar que el usuario existe
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(login_data.password, usuario.contrasena_hash):
    
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    # Crear token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(usuario.id)},
        expires_delta=access_token_expires
    )
    
    # Preparar datos del usuario para la respuesta
    usuario_data = {
        "id": str(usuario.id),
        "nombre_usuario": usuario.nombre_usuario,
        "email": usuario.correo_electronico,
        "nombre_completo": f"{usuario.nombre} {usuario.primer_apellido}",
        "activo": usuario.activo,
        "foto_url": usuario.foto_url
    }
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        usuario=usuario_data
    )


@router.get("/me", response_model=UsuarioWithArea)
def get_me(current_user: Usuario = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado actual
    """
    return current_user


@router.post("/logout")
def logout(current_user: Usuario = Depends(get_current_user)):
    """
    Cerrar sesión (en JWT stateless esto es principalmente para el cliente)
    El cliente debe eliminar el token del localStorage
    """
    return {
        "message": "Sesión cerrada exitosamente",
        "usuario": current_user.nombre_usuario
    }
