"""
Cliente de Supabase para gestión de archivos
"""
import os
from typing import Optional, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "avatars")

# Inicializar cliente
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_avatar(file_path: str, file_name: str) -> Tuple[bool, str]:
    """
    Sube un avatar a Supabase Storage
    
    Args:
        file_path: Ruta del archivo a subir
        file_name: Nombre del archivo en el bucket
        
    Returns:
        Tuple[bool, str]: (éxito, url_o_mensaje_error)
    """
    if not supabase:
        return False, "Supabase no está configurado"
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Subir archivo
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            file_name,
            file_data,
            file_options={"content-type": "image/webp"}
        )
        
        # Obtener URL pública
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
        
        return True, public_url
        
    except Exception as e:
        return False, str(e)


def delete_avatar(file_name: str) -> Tuple[bool, str]:
    """
    Elimina un avatar de Supabase Storage
    
    Args:
        file_name: Nombre del archivo a eliminar
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    if not supabase:
        return False, "Supabase no está configurado"
    
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([file_name])
        return True, "Archivo eliminado correctamente"
        
    except Exception as e:
        return False, str(e)


def get_file_name_from_url(url: str) -> Optional[str]:
    """
    Extrae el nombre del archivo de una URL de Supabase
    
    Args:
        url: URL completa del archivo
        
    Returns:
        Nombre del archivo o None
    """
    if not url:
        return None
    
    try:
        # URL format: https://project.supabase.co/storage/v1/object/public/bucket/filename
        parts = url.split('/')
        return parts[-1] if parts else None
    except:
        return None
