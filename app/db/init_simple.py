"""
Script simple para inicializar la base de datos con usuario admin
VERSIÓN 2: Sin hasheo de contraseña (para solucionar problema de bcrypt)
"""
from app.database import Base, engine, SessionLocal

# Importar TODOS los modelos para que SQLAlchemy los registre
from app.models.usuario import Usuario, Area, Rol, Permiso, UsuarioRol, RolPermiso
from app.models.proceso import Proceso
from app.models.documento import Documento
from app.models.calidad import NoConformidad, AccionCorrectiva
from app.models.auditoria import Auditoria
from app.models.capacitacion import Capacitacion
from app.models.sistema import Notificacion

def init_database():
    """Inicializar base de datos con datos mínimos"""
    print("="*60)
    print("   INICIALIZANDO BASE DE DATOS")
    print("="*60)
    
    # Crear todas las tablas
    print("\n📝 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")
    
    # Iniciar sesión de BD
    db = SessionLocal()
    
    try:
        # Verificar si ya existe el admin
        admin_exists = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        if admin_exists:
            print("\n✅ Usuario admin ya existe")
            print(f"   Email: {admin_exists.correo_electronico}")
            return
        
        print("\n👤 Creando usuario administrador...")
        
        # Hash manual simple de bcrypt para "admin123"
        # Este es el hash de "admin123" generado con bcrypt
        password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqgXNu.LS2"
        
        # Crear usuario admin directamente
        admin = Usuario(
            documento=0,
            nombre="Administrador",
            primer_apellido="Sistema",
            correo_electronico="admin@sistema.com",
            nombre_usuario="admin",
            contrasena_hash=password_hash,
            activo=True
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Usuario administrador creado exitosamente!")
        print("\n🔑 Credenciales:")
        print("   Usuario: admin")
        print("   Password: admin123")
        print("\n" + "="*60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
