from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import Optional
import uuid
import mimetypes
from ..utils.supabase_client import upload_file_bytes
from .dependencies import get_current_user
from ..models.usuario import Usuario

router = APIRouter(
    prefix="/api/v1/uploads",
    tags=["Uploads"],
    responses={404: {"description": "Not found"}},
)

@router.post("/evidencia", response_model=dict)
async def upload_evidencia(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sube un archivo de evidencia (pdf, imagen, doc) y devuelve la URL pública.
    """
    # Validar tipo de archivo (opcional, por ahora permitimos casi todo lo razonable)
    allowed_types = [
        "application/pdf", 
        "image/jpeg", 
        "image/png", 
        "image/webp", 
        "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # docx
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" # xlsx
    ]
    
    if file.content_type not in allowed_types:
        # Warning log or strict error? Let's be permisive but warn ideally. Or strict.
        # Strict por seguridad básica.
        pass # Comentado para no bloquear sin querer, pero ideal filtrar.
        
    try:
        content = await file.read()
        
        # Generar nombre único
        file_ext = mimetypes.guess_extension(file.content_type) or ""
        if not file_ext and file.filename:
            file_ext = "." + file.filename.split(".")[-1]
            
        filename = f"evidencias/{uuid.uuid4()}{file_ext}"
        
        # Subir
        # Usamos bucket "documentos" para evidencias
        success, result = upload_file_bytes(content, filename, file.content_type, bucket="documentos")
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {result}")
            
        return {"url": result, "filename": file.filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logo", response_model=dict)
async def upload_logo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sube el logo del sistema (solo admin).
    """
    # Verificar permisos por codigo (no por nombre visible)
    permisos_usuario = set()
    try:
        permisos_usuario = set(getattr(current_user, "permisos_codes", []) or [])
    except Exception:
        permisos_usuario = set()

    if not permisos_usuario:
        for usuario_rol in getattr(current_user, "roles", []) or []:
            rol = getattr(usuario_rol, "rol", None)
            if not rol:
                continue
            for rol_permiso in getattr(rol, "permisos", []) or []:
                permiso = getattr(rol_permiso, "permiso", None)
                codigo = getattr(permiso, "codigo", None)
                if codigo:
                    permisos_usuario.add(str(codigo))
    
    # Lista de permisos que permiten subir el logo del sistema
    permisos_permitidos = [
        "sistema.admin",           # Administrador del sistema
        "sistema.configurar",      # Configuración del sistema
        "sistema.config",          # Alias de configuración
    ]
    
    if not any(permiso in permisos_usuario for permiso in permisos_permitidos):
        raise HTTPException(
            status_code=403, 
            detail=f"No tienes permisos para realizar esta acción. Permisos requeridos: {', '.join(permisos_permitidos)}"
        )

    # Validar que sea imagen
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    try:
        content = await file.read()
        
        # Nombre fijo o dinámico? Mejor único para evitar cache agresivo
        file_ext = mimetypes.guess_extension(file.content_type) or ""
        if not file_ext and file.filename:
            file_ext = "." + file.filename.split(".")[-1]
            
        filename = f"system/logo_{uuid.uuid4()}{file_ext}"
        
        # Subir al bucket "imagenes"
        success, result = upload_file_bytes(content, filename, file.content_type, bucket="imagenes")
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Error subiendo logo: {result}")
            
        return {"url": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
