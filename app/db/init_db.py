"""
Script para inicializar la base de datos y crear tablas
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, engine
from models import *  # Importar todos los modelos


def init_db():
    """Crear todas las tablas en la base de datos"""
    print("🔨 Creando tablas en la base de datos...")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente!")
        
        # Mostrar las tablas creadas
        print("\n📋 Tablas creadas:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        raise


def drop_all_tables():
    """Eliminar todas las tablas (usar con precaución!)"""
    print("⚠️  ADVERTENCIA: Eliminando todas las tablas...")
    
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ Tablas eliminadas exitosamente!")
    except Exception as e:
        print(f"❌ Error al eliminar tablas: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestión de base de datos")
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Eliminar todas las tablas antes de crearlas'
    )
    
    args = parser.parse_args()
    
    if args.drop:
        response = input("¿Estás seguro de que quieres eliminar todas las tablas? (si/no): ")
        if response.lower() == 'si':
            drop_all_tables()
            init_db()
        else:
            print("Operación cancelada")
    else:
        init_db()
