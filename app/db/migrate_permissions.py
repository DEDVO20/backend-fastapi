"""
Script para registrar todos los permisos del sistema en la base de datos.
Basado en los módulos funcionales requeridos para ISO 9001.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal
from app.models.usuario import Permiso

def migrar_permisos():
    db = SessionLocal()
    
    permisos_data = [
        # Usuarios y Roles
        {"nombre": "Ver Usuarios", "codigo": "usuarios.ver", "descripcion": "Listar y consultar perfiles de empleados"},
        {"nombre": "Crear Usuarios", "codigo": "usuarios.crear", "descripcion": "Registrar nuevos colaboradores"},
        {"nombre": "Editar Usuarios", "codigo": "usuarios.editar", "descripcion": "Modificar datos y estados de cuenta"},
        {"nombre": "Eliminar Usuarios", "codigo": "usuarios.eliminar", "descripcion": "Borrar registros de usuarios"},
        {"nombre": "Administrar Roles", "codigo": "roles.administrar", "descripcion": "Crear roles y asignar permisos"},
        
        # Áreas
        {"nombre": "Ver Áreas", "codigo": "areas.ver", "descripcion": "Consultar organigrama y departamentos"},
        {"nombre": "Gestionar Áreas", "codigo": "areas.gestionar", "descripcion": "Crear áreas y asignar responsables"},
        
        # Gestión Documental
        {"nombre": "Ver Documentos", "codigo": "documentos.ver", "descripcion": "Lectura de manuales y procedimientos"},
        {"nombre": "Crear Documentos", "codigo": "documentos.crear", "descripcion": "Subir borradores de documentos"},
        {"nombre": "Editar Documentos", "codigo": "documentos.editar", "descripcion": "Modificar versiones existentes"},
        {"nombre": "Aprobar Documentos", "codigo": "documentos.aprobar", "descripcion": "Validar y publicar documentos oficiales"},
        {"nombre": "Eliminar Documentos", "codigo": "documentos.eliminar", "descripcion": "Gestionar obsolescencia documental"},
        
        # Gestión de Calidad
        {"nombre": "Ver Indicadores", "codigo": "indicadores.ver", "descripcion": "Visualizar tableros de mando y KPIs"},
        {"nombre": "Medir Indicadores", "codigo": "indicadores.medir", "descripcion": "Ingresar mediciones periódicas"},
        {"nombre": "Gestionar No Conformidades", "codigo": "no_conformidades.gestionar", "descripcion": "Apertura y seguimiento de hallazgos"},
        {"nombre": "Gestionar Acciones Correctivas", "codigo": "acciones_correctivas.gestionar", "descripcion": "Planes de acción y cierre de hallazgos"},
        {"nombre": "Seguimiento de Objetivos", "codigo": "objetivos.seguimiento", "descripcion": "Monitoreo de metas de calidad"},
        
        # Procesos y Auditorías
        {"nombre": "Gestionar Procesos", "codigo": "procesos.gestionar", "descripcion": "Editar mapa de procesos y etapas"},
        {"nombre": "Planificar Auditorías", "codigo": "auditorias.planificar", "descripcion": "Creación del plan anual de auditorías"},
        {"nombre": "Ejecutar Auditorías", "codigo": "auditorias.ejecutar", "descripcion": "Registro de hallazgos en campo"},
        
        # Riesgos y Capacitaciones
        {"nombre": "Administrar Riesgos", "codigo": "riesgos.administrar", "descripcion": "Identificación y valoración de riesgos"},
        {"nombre": "Gestionar Capacitaciones", "codigo": "capacitaciones.gestionar", "descripcion": "Planes de formación y asistencia"},
        
        # Sistema
        {"nombre": "Administrar Sistema", "codigo": "sistema.admin", "descripcion": "Acceso total (Superusuario)"},
        {"nombre": "Configurar Sistema", "codigo": "sistema.configurar", "descripcion": "Cambio de parámetros globales"},
        {"nombre": "Gestionar Migraciones", "codigo": "sistema.migraciones", "descripcion": "Control de actualizaciones de base de datos"},
        {"nombre": "Soporte Técnico", "codigo": "tickets.soporte", "descripcion": "Gestión de solicitudes de ayuda interna"},
    ]

    print("🚀 Iniciando migración de permisos...")
    
    contador_creados = 0
    contador_existentes = 0
    
    try:
        for p_data in permisos_data:
            # Verificar si ya existe el permiso por su código
            permiso = db.query(Permiso).filter(Permiso.codigo == p_data["codigo"]).first()
            
            if not permiso:
                nuevo_permiso = Permiso(**p_data)
                db.add(nuevo_permiso)
                contador_creados += 1
                print(f"  + Creado: {p_data['codigo']}")
            else:
                # Actualizar descripción si ya existe
                permiso.nombre = p_data["nombre"]
                permiso.descripcion = p_data["descripcion"]
                contador_existentes += 1
        
        db.commit()
        print("\n✅ Migración completada con éxito")
        print(f"  - Permisos creados: {contador_creados}")
        print(f"  - Permisos existentes/actualizados: {contador_existentes}")
        print(f"  - Total en sistema: {contador_creados + contador_existentes}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante la migración: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrar_permisos()
