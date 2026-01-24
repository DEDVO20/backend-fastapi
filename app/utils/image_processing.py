"""
Utilidades para procesamiento de imágenes
"""
import os
import io
import time
from PIL import Image
from typing import Tuple


def validate_image(file_content: bytes, max_size_mb: int = 2) -> Tuple[bool, str]:
    """
    Valida que el archivo sea una imagen válida
    
    Args:
        file_content: Contenido del archivo
        max_size_mb: Tamaño máximo en MB
        
    Returns:
        Tuple[bool, str]: (válido, mensaje_error)
    """
    # Validar tamaño
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"La imagen no puede superar {max_size_mb}MB"
    
    try:
        # Intentar abrir como imagen
        img = Image.open(io.BytesIO(file_content))
        
        # Validar formato
        if img.format not in ['JPEG', 'PNG', 'WEBP']:
            return False, "Formato no soportado. Use JPG, PNG o WEBP"
        
        # Validar dimensiones mínimas
        if img.width < 100 or img.height < 100:
            return False, "La imagen debe tener al menos 100x100 píxeles"
        
        return True, ""
        
    except Exception as e:
        return False, f"Archivo no válido: {str(e)}"


def process_avatar(file_content: bytes, usuario_id: str) -> Tuple[bool, str, bytes]:
    """
    Procesa una imagen de avatar
    
    Args:
        file_content: Contenido del archivo original
        usuario_id: ID del usuario
        
    Returns:
        Tuple[bool, str, bytes]: (éxito, nombre_archivo, contenido_procesado)
    """
    try:
        # Abrir imagen
        img = Image.open(io.BytesIO(file_content))
        
        # Convertir a RGB si es necesario
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar manteniendo aspecto (400x400)
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # Crear imagen cuadrada con padding si es necesario
        size = max(img.size)
        new_img = Image.new('RGB', (size, size), (255, 255, 255))
        new_img.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
        
        # Redimensionar a exactamente 400x400
        new_img = new_img.resize((400, 400), Image.Resampling.LANCZOS)
        
        # Guardar como WEBP
        output = io.BytesIO()
        new_img.save(output, format='WEBP', quality=85, method=6)
        output.seek(0)
        
        # Generar nombre con carpeta por usuario
        file_name = f"{usuario_id}/avatar.webp"
        
        return True, file_name, output.getvalue()
        
    except Exception as e:
        return False, str(e), b''
