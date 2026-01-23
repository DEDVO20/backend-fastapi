"""
Script para crear usuarios de prueba
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.usuario import Usuario, Area
from app.utils.security import get_password_hash


def create_test_users():
    """Crear usuarios de prueba"""
    db = SessionLocal()
    
    try:
        print("👥 Creando usuarios de prueba...")
        
        # Obtener áreas existentes
        areas = db.query(Area).all()
        
        if not areas:
            print("⚠️  No hay áreas. Ejecuta primero seed_data.py")
            return
        
        area_dir = next((a for a in areas if a.codigo == "DIR"), areas[0])
        area_cal = next((a for a in areas if a.codigo == "CAL"), areas[0])
        area_ops = next((a for a in areas if a.codigo == "OPE"), areas[0])
        
        # Verificar que admin ya existe
        admin = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        if admin:
            print("✓ Usuario admin ya existe")
        
        # Usuarios de prueba
        usuarios = [
            {
                "nombre_usuario": "jperez",
                "email": "jperez@empresa.com",
                "nombre_completo": "Juan Pérez",
                "password": "password123",
                "cargo": "Gerente de Calidad",
                "area_id": area_cal.id if area_cal else None,
                "telefono": "+1234567890",
                "activo": True
            },
            {
                "nombre_usuario": "mgarcia",
                "email": "mgarcia@empresa.com",
                "nombre_completo": "María García",
                "password": "password123",
                "cargo": "Supervisor de Operaciones",
                "area_id": area_ops.id if area_ops else None,
                "telefono": "+1234567891",
                "activo": True
            },
            {
                "nombre_usuario": "rlopez",
                "email": "rlopez@empresa.com",
                "nombre_completo": "Roberto López",
                "password": "password123",
                "cargo": "Auditor Interno",
                "area_id": area_cal.id if area_cal else None,
                "telefono": "+1234567892",
                "activo": True
            },
            {
                "nombre_usuario": "amartinez",
                "email": "amartinez@empresa.com",
                "nombre_completo": "Ana Martínez",
                "password": "password123",
                "cargo": "Analista de Calidad",
                "area_id": area_cal.id if area_cal else None,
                "telefono": "+1234567893",
                "activo": True
            },
            {
                "nombre_usuario": "lsanchez",
                "email": "lsanchez@empresa.com",
                "nombre_completo": "Luis Sánchez",
                "password": "password123",
                "cargo": "Técnico de Producción",
                "area_id": area_ops.id if area_ops else None,
                "telefono": "+1234567894",
                "activo": True
            }
        ]
        
        created = 0
        for user_data in usuarios:
            # Verificar si ya existe
            existing = db.query(Usuario).filter(
                Usuario.nombre_usuario == user_data["nombre_usuario"]
            ).first()
            
            if existing:
                print(f"  ℹ️  Usuario {user_data['nombre_usuario']} ya existe, omitiendo...")
                continue
            
            # Extraer password y hashear
            password = user_data.pop("password")
            user_data["password_hash"] = get_password_hash(password)
            
            # Crear usuario
            usuario = Usuario(**user_data)
            db.add(usuario)
            created += 1
            print(f"  ✓ Creado: {user_data['nombre_usuario']} - {user_data['nombre_completo']}")
        
        db.commit()
        
        print(f"\n✅ Proceso completado!")
        print(f"   - {created} nuevos usuarios creados")
        print(f"   - Total usuarios en sistema: {db.query(Usuario).count()}")
        print(f"\n🔑 Credenciales de prueba:")
        print(f"   Usuario: admin | Contraseña: admin123")
        print(f"   Usuario: jperez | Contraseña: password123")
        print(f"   Usuario: mgarcia | Contraseña: password123")
        print(f"   (otros usuarios también usan: password123)")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("   CREAR USUARIOS DE PRUEBA")
    print("=" * 60)
    create_test_users()
