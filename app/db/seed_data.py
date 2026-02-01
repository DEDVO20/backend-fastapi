"""
Script para crear datos iniciales en la base de datos
"""
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.usuario import Area, Usuario, Rol, Permiso, RolPermiso, UsuarioRol
from app.models import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def crear_areas_iniciales(db: Session):
    """Crear áreas iniciales"""
    areas_data = [
        {"codigo": "DIR", "nombre": "Dirección", "descripcion": "Dirección General"},
        {"codigo": "ADM", "nombre": "Administración", "descripcion": "Área Administrativa"},
        {"codigo": "OPE", "nombre": "Operaciones", "descripcion": "Área de Operaciones"},
        {"codigo": "CAL", "nombre": "Calidad", "descripcion": "Gestión de Calidad"},
        {"codigo": "TEC", "nombre": "Tecnología", "descripcion": "Tecnología e Innovación"},
    ]
    
    for area_data in areas_data:
        area = db.query(Area).filter(Area.codigo == area_data["codigo"]).first()
        if not area:
            area = Area(**area_data)
            db.add(area)
    
    db.commit()
    print("✅ Áreas iniciales creadas")  

def crear_roles_permisos_iniciales(db: Session):
    """Crear roles y permisos iniciales (Sistema Robusto)"""
    
    # 1. Definición de Permisos Granulares
    permisos_data = [
        # --- USUARIOS Y SISTEMA ---
        {"codigo": "usuarios.gestion", "nombre": "Gestión de Usuarios", "descripcion": "Crear, editar y eliminar usuarios"},
        {"codigo": "usuarios.ver", "nombre": "Ver Usuarios", "descripcion": "Ver lista y perfiles de usuarios"},
        {"codigo": "sistema.config", "nombre": "Configuración del Sistema", "descripcion": "Gestionar variables y configuraciones globales"},
        
        # --- DOCUMENTOS ---
        {"codigo": "documentos.ver", "nombre": "Ver Documentos", "descripcion": "Ver documentos vigentes"},
        {"codigo": "documentos.crear", "nombre": "Crear Documentos", "descripcion": "Crear borradores y solicitar revisiones"},
        {"codigo": "documentos.revisar", "nombre": "Revisar Documentos", "descripcion": "Revisión técnica de documentos"},
        {"codigo": "documentos.aprobar", "nombre": "Aprobar Documentos", "descripcion": "Aprobar documentos (Jefatura/Coordinación)"},
        {"codigo": "documentos.anular", "nombre": "Anular Documentos", "descripcion": "Anular o eliminar documentos obsoletos"},
        
        # --- RIESGOS ---
        {"codigo": "riesgos.ver", "nombre": "Ver Mapa de Riesgos", "descripcion": "Visualizar riesgos y controles"},
        {"codigo": "riesgos.identificar", "nombre": "Identificar Riesgos", "descripcion": "Reportar nuevos riesgos"},
        {"codigo": "riesgos.gestion", "nombre": "Gestión de Riesgos", "descripcion": "Analizar riesgos y definir controles"},
        
        # --- CALIDAD (No Conformidades e Indicadores) ---
        {"codigo": "calidad.ver", "nombre": "Ver Tableros de Calidad", "descripcion": "Ver indicadores y reportes"},
        {"codigo": "noconformidades.reportar", "nombre": "Reportar No Conformidad", "descripcion": "Crear reporte de NC"},
        {"codigo": "noconformidades.gestion", "nombre": "Gestionar No Conformidades", "descripcion": "Análisis de causa y planes de acción"},
        {"codigo": "noconformidades.cerrar", "nombre": "Cerrar No Conformidades", "descripcion": "Verificar eficacia y cerrar NC"},
        
        # --- AUDITORÍAS ---
        {"codigo": "auditorias.ver", "nombre": "Ver Auditorías", "descripcion": "Ver programas e informes de auditoría"},
        {"codigo": "auditorias.planificar", "nombre": "Planificar Auditorías", "descripcion": "Crear programas y asignar auditores"},
        {"codigo": "auditorias.ejecutar", "nombre": "Ejecutar Auditoría", "descripcion": "Registrar hallazgos (Rol Auditor)"},
        
        # --- CAPACITACIONES Y PROCESOS ---
        {"codigo": "capacitaciones.gestion", "nombre": "Gestión de Capacitaciones", "descripcion": "Crear planes y registrar asistencias"},
        {"codigo": "procesos.admin", "nombre": "Administrar Procesos", "descripcion": "Modelar mapa de procesos y etapas"}
    ]
    
    permisos = {}
    for permiso_data in permisos_data:
        permiso = db.query(Permiso).filter(Permiso.codigo == permiso_data["codigo"]).first()
        if not permiso:
            permiso = Permiso(**permiso_data)
            db.add(permiso)
            db.flush()
            print(f"Permiso creado: {permiso_data['codigo']}")
        permisos[permiso_data["codigo"]] = permiso
    
    # 2. Definición de Roles Estructurados
    roles_data = [
        {
            "nombre": "Administrador del Sistema",
            "clave": "admin",
            "descripcion": "Superusuario con acceso total",
            "permisos": list(permisos.keys()) # Todos los permisos
        },
        {
            "nombre": "Gestor de Calidad",
            "clave": "gestor_calidad",
            "descripcion": "Administrador funcional del SGC",
            "permisos": [
                "usuarios.ver", "documentos.ver", "documentos.crear", "documentos.revisar", "documentos.aprobar", "documentos.anular",
                "riesgos.ver", "riesgos.gestion", 
                "calidad.ver", "noconformidades.reportar", "noconformidades.gestion", "noconformidades.cerrar",
                "auditorias.ver", "auditorias.planificar", "auditorias.ejecutar",
                "capacitaciones.gestion", "procesos.admin"
            ]
        },
        {
            "nombre": "Coordinador de Área",
            "clave": "coordinador",
            "descripcion": "Líder de proceso con capacidad de aprobación",
            "permisos": [
                "usuarios.ver", 
                "documentos.ver", "documentos.crear", "documentos.revisar", "documentos.aprobar", # Puede aprobar
                "riesgos.ver", "riesgos.identificar", "riesgos.gestion", # Gestiona riesgos de su área
                "calidad.ver", "noconformidades.reportar", "noconformidades.gestion", # Gestiona NC de su área
                "auditorias.ver" # Ve auditorías (si es auditado)
            ]
        },
        {
            "nombre": "Auxiliar / Analista",
            "clave": "auxiliar",
            "descripcion": "Rol operativo de soporte",
            "permisos": [
                "usuarios.ver",
                "documentos.ver", "documentos.crear", "documentos.revisar", # No aprueba
                "riesgos.ver", "riesgos.identificar", # Solo identifica
                "calidad.ver", "noconformidades.reportar", # Reporta NC
                "auditorias.ver"
            ]
        },
        {
            "nombre": "Auditor Interno/Externo",
            "clave": "auditor",
            "descripcion": "Responsable de ejecutar auditorías",
            "permisos": [
                "usuarios.ver", "documentos.ver", "procesos.admin", # Necesita ver procesos para auditar
                "auditorias.ver", "auditorias.ejecutar", # Su función principal
                "riesgos.ver", "calidad.ver" # Para consultar evidencia
            ]
        },
        {
            "nombre": "Líder SISO",
            "clave": "lider_siso",
            "descripcion": "Especialista en Seguridad y Salud Ocupacional",
            "permisos": [
                "usuarios.ver",
                "riesgos.ver", "riesgos.identificar", "riesgos.gestion", # Fuerte en riesgos
                "documentos.ver", "documentos.crear",
                "calidad.ver", "noconformidades.reportar", "noconformidades.gestion"
            ]
        }
    ]
    
    roles = {}
    for rol_data in roles_data:
        permisos_rol = rol_data.pop("permisos")
        rol = db.query(Rol).filter(Rol.clave == rol_data["clave"]).first()
        if not rol:
            rol = Rol(**rol_data)
            db.add(rol)
            db.flush()
            print(f"Rol creado: {rol_data['nombre']}")
        
        # Actualizar permisos del rol (limpiar y reasignar para asegurar sincronización)
        # Nota: En un sistema en producción esto se haría con cuidado, aquí re-sincronizamos
        # db.query(RolPermiso).filter(RolPermiso.rol_id == rol.id).delete()
        
        existing_perms = {rp.permiso_id for rp in rol.permisos}
        
        for permiso_codigo in permisos_rol:
            if permiso_codigo in permisos:
                permiso_obj = permisos[permiso_codigo]
                if permiso_obj.id not in existing_perms:
                    rol_permiso = RolPermiso(rol_id=rol.id, permiso_id=permiso_obj.id)
                    db.add(rol_permiso)
        
        roles[rol_data["clave"]] = rol
    
    db.commit()
    print("✅ Roles y permisos extendidos actualizados correctamente")
    return roles


def crear_usuario_admin(db: Session, roles: dict):
    """Crear usuario administrador por defecto"""
    # Verificar si ya existe
    admin = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
    if admin:
        print("ℹ️  Usuario admin ya existe, verificando roles...")
    else:
        # Obtener área de dirección
        area_dir = db.query(Area).filter(Area.codigo == "DIR").first()
        
        # Crear usuario admin
        admin = Usuario(
            documento=0,
            nombre="Administrador",
            primer_apellido="Sistema",
            correo_electronico="admin@sistema.com",
            nombre_usuario="admin",
            contrasena_hash=pwd_context.hash("admin123"),  # Cambiar en producción
            area_id=area_dir.id if area_dir else None,
            activo=True
        )
        db.add(admin)
        db.flush()
        print("✅ Usuario administrador creado")
    
    # Asignar rol de administrador
    if "admin" in roles:
        usuario_rol = UsuarioRol(usuario_id=admin.id, rol_id=roles["admin"].id)
        db.add(usuario_rol)
    
    db.commit()
    print("✅ Usuario administrador creado (usuario: admin, contraseña: admin123)")


def init_data(db: Session):
    """Inicializar todos los datos"""
    print("🌱 Insertando datos iniciales...")
    
    crear_areas_iniciales(db)
    roles = crear_roles_permisos_iniciales(db)
    crear_usuario_admin(db, roles)
    
    print("✅ Datos iniciales insertados correctamente!")


if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        init_data(db)
    finally:
        db.close()
