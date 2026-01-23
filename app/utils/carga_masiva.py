"""
Utilidades para carga masiva de usuarios desde Excel/CSV
"""
import pandas as pd
import io
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from ..models.usuario import Usuario, Area
from ..models.rol import Rol, UsuarioRol
from ..schemas.usuario import CargaMasivaErrorDetalle, CargaMasivaUsuarioExitoso
from ..utils.security import get_password_hash


COLUMNAS_REQUERIDAS = [
    'documento',
    'nombre',
    'primer_apellido',
    'correo_electronico',
    'nombre_usuario',
    'contrasena',
    'area_codigo',
    'roles'
]

COLUMNAS_OPCIONALES = [
    'segundo_nombre',
    'segundo_apellido',
    'activo'
]


def validar_archivo(file: UploadFile) -> Tuple[bool, str]:
    """Valida que el archivo sea del tipo correcto"""
    if not file.filename:
        return False, "El archivo no tiene nombre"
    
    extension = file.filename.split('.')[-1].lower()
    if extension not in ['xlsx', 'xls', 'csv']:
        return False, f"Tipo de archivo no soportado: .{extension}. Use .xlsx, .xls o .csv"
    
    # Validar tamaño (5MB máximo)
    return True, ""


def leer_archivo(file_content: bytes, filename: str) -> pd.DataFrame:
    """Lee el archivo Excel o CSV y retorna un DataFrame"""
    extension = filename.split('.')[-1].lower()
    
    if extension in ['xlsx', 'xls']:
        df = pd.read_excel(io.BytesIO(file_content))
    else:  # csv
        df = pd.read_csv(io.BytesIO(file_content))
    
    return df


def validar_columnas(df: pd.DataFrame) -> List[str]:
    """Valida que el DataFrame tenga las columnas requeridas"""
    columnas_faltantes = []
    for col in COLUMNAS_REQUERIDAS:
        if col not in df.columns:
            columnas_faltantes.append(col)
    
    return columnas_faltantes


def procesar_fila(
    fila_num: int,
    fila: pd.Series,
    db: Session,
    areas_cache: Dict[str, Area],
    roles_cache: Dict[str, Rol]
) -> Tuple[bool, Any]:
    """
    Procesa una fila del archivo
    Retorna: (exito, resultado)
    - Si exito=True, resultado es el usuario creado
    - Si exito=False, resultado es lista de errores
    """
    errores = []
    
    # Validar campos obligatorios
    if pd.isna(fila.get('documento')):
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='documento',
            valor=None,
            error='El documento es obligatorio'
        ))
    
    if pd.isna(fila.get('nombre')) or not str(fila.get('nombre')).strip():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='nombre',
            valor=str(fila.get('nombre', '')),
            error='El nombre es obligatorio'
        ))
    
    if pd.isna(fila.get('primer_apellido')) or not str(fila.get('primer_apellido')).strip():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='primer_apellido',
            valor=str(fila.get('primer_apellido', '')),
            error='El primer apellido es obligatorio'
        ))
    
    if pd.isna(fila.get('correo_electronico')) or not str(fila.get('correo_electronico')).strip():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='correo_electronico',
            valor=str(fila.get('correo_electronico', '')),
            error='El correo electrónico es obligatorio'
        ))
    
    if pd.isna(fila.get('nombre_usuario')) or not str(fila.get('nombre_usuario')).strip():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='nombre_usuario',
            valor=str(fila.get('nombre_usuario', '')),
            error='El nombre de usuario es obligatorio'
        ))
    
    if pd.isna(fila.get('contrasena')) or len(str(fila.get('contrasena', ''))) < 6:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='contrasena',
            valor='***',
            error='La contraseña debe tener al menos 6 caracteres'
        ))
    
    # Si ya hay errores, retornar
    if errores:
        return False, errores
    
    # Validar unicidad de documento
    documento = int(fila['documento'])
    if db.query(Usuario).filter(Usuario.documento == documento).first():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='documento',
            valor=str(documento),
            error=f'El documento {documento} ya existe en el sistema'
        ))
    
    # Validar unicidad de email
    email = str(fila['correo_electronico']).strip()
    if db.query(Usuario).filter(Usuario.correo_electronico == email).first():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='correo_electronico',
            valor=email,
            error=f'El correo {email} ya existe en el sistema'
        ))
    
    # Validar unicidad de username
    username = str(fila['nombre_usuario']).strip()
    if db.query(Usuario).filter(Usuario.nombre_usuario == username).first():
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='nombre_usuario',
            valor=username,
            error=f'El nombre de usuario {username} ya existe en el sistema'
        ))
    
    # Validar área
    area_codigo = str(fila.get('area_codigo', '')).strip()
    if not area_codigo:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='area_codigo',
            valor=area_codigo,
            error='El código de área es obligatorio'
        ))
    elif area_codigo not in areas_cache:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='area_codigo',
            valor=area_codigo,
            error=f'El área con código {area_codigo} no existe'
        ))
    
    # Validar roles
    roles_str = str(fila.get('roles', '')).strip()
    if not roles_str:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='roles',
            valor=roles_str,
            error='Debe especificar al menos un rol'
        ))
    else:
        roles_claves = [r.strip() for r in roles_str.split(',')]
        roles_invalidos = [r for r in roles_claves if r not in roles_cache]
        if roles_invalidos:
            errores.append(CargaMasivaErrorDetalle(
                fila=fila_num,
                campo='roles',
                valor=', '.join(roles_invalidos),
                error=f'Roles no encontrados: {", ".join(roles_invalidos)}'
            ))
    
    # Si hay errores, retornar
    if errores:
        return False, errores
    
    # Crear usuario
    try:
        nuevo_usuario = Usuario(
            documento=documento,
            nombre=str(fila['nombre']).strip(),
            segundo_nombre=str(fila.get('segundo_nombre', '')).strip() or None,
            primer_apellido=str(fila['primer_apellido']).strip(),
            segundo_apellido=str(fila.get('segundo_apellido', '')).strip() or None,
            correo_electronico=email,
            nombre_usuario=username,
            contrasena_hash=get_password_hash(str(fila['contrasena'])),
            area_id=areas_cache[area_codigo].id,
            activo=bool(fila.get('activo', True))
        )
        
        db.add(nuevo_usuario)
        db.flush()  # Para obtener el ID sin hacer commit
        
        # Asignar roles
        for rol_clave in roles_claves:
            usuario_rol = UsuarioRol(
                usuario_id=nuevo_usuario.id,
                rol_id=roles_cache[rol_clave].id
            )
            db.add(usuario_rol)
        
        return True, nuevo_usuario
        
    except Exception as e:
        errores.append(CargaMasivaErrorDetalle(
            fila=fila_num,
            campo='general',
            valor=None,
            error=f'Error al crear usuario: {str(e)}'
        ))
        return False, errores


def cargar_caches(db: Session) -> Tuple[Dict[str, Area], Dict[str, Rol]]:
    """Carga áreas y roles en memoria para acceso rápido"""
    areas = db.query(Area).all()
    roles = db.query(Rol).all()
    
    areas_cache = {area.codigo: area for area in areas}
    roles_cache = {rol.clave: rol for rol in roles}
    
    return areas_cache, roles_cache
