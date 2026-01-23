"""
Script para crear datos de prueba adicionales en la base de datos
Incluye ejemplos de todos los módulos del sistema
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import *
from app.utils.security import get_password_hash
from datetime import datetime, timedelta
from decimal import Decimal
import uuid


def create_test_data():
    """Crear datos de prueba completos"""
    db = SessionLocal()
    
    try:
        print("🌱 Creando datos de prueba...")
        
        # Obtener datos base existentes
        areas = db.query(Area).all()
        usuarios = db.query(Usuario).all()
        
        if not areas or not usuarios:
            print("⚠️  Ejecuta primero seed_data.py para crear datos básicos")
            return
        
        admin = usuarios[0]  # Usuario admin
        area_calidad = next((a for a in areas if a.codigo == "CAL"), areas[0])
        area_ops = next((a for a in areas if a.codigo == "OPE"), areas[0])
        
        # ========================
        # PROCESOS
        # ========================
        print("\n📋 Creando procesos...")
        
        proceso1 = Proceso(
            codigo="PROC-001",
            nombre="Gestión de Ventas",
            descripcion="Proceso de gestión comercial y ventas",
            objetivo="Maximizar la satisfacción del cliente",
            tipo_proceso="operativo",
            responsable_id=admin.id,
            area_id=area_ops.id,
            estado="activo"
        )
        
        proceso2 = Proceso(
            codigo="PROC-002",
            nombre="Control de Calidad",
            descripcion="Inspección y aseguramiento de calidad",
            objetivo="Garantizar productos conformes",
            tipo_proceso="calidad",
            responsable_id=admin.id,
            area_id=area_calidad.id,
            estado="activo"
        )
        
        db.add_all([proceso1, proceso2])
        db.flush()
        
        # Etapas de proceso
        etapa1 = EtapaProceso(
            proceso_id=proceso1.id,
            nombre="Prospección",
            descripcion="Identificar clientes potenciales",
            orden=1,
            duracion_estimada=5,
            responsable_id=admin.id
        )
        
        etapa2 = EtapaProceso(
            proceso_id=proceso1.id,
            nombre="Negociación",
            descripcion="Propuesta y negociación",
            orden=2,
            duracion_estimada=10,
            responsable_id=admin.id
        )
        
        db.add_all([etapa1, etapa2])
        
        # ========================
        # DOCUMENTOS
        # ========================
        print("📄 Creando documentos...")
        
        doc1 = Documento(
            codigo="DOC-001",
            titulo="Manual de Calidad",
            descripcion="Manual del sistema de gestión de calidad",
            tipo_documento="manual",
            categoria="calidad",
            version_actual="1.0",
            estado="vigente",
            propietario_id=admin.id,
            proceso_id=proceso2.id
        )
        
        doc2 = Documento(
            codigo="DOC-002",
            titulo="Procedimiento de Ventas",
            descripcion="Procedimiento operativo de ventas",
            tipo_documento="procedimiento",
            categoria="operativo",
            version_actual="1.0",
            estado="vigente",
            propietario_id=admin.id,
            proceso_id=proceso1.id
        )
        
        db.add_all([doc1, doc2])
        db.flush()
        
        # Versiones
        version1 = VersionDocumento(
            documento_id=doc1.id,
            numero_version="1.0",
            descripcion_cambios="Versión inicial",
            creado_por_id=admin.id
        )
        
        db.add(version1)
        
        # ========================
        # CALIDAD
        # ========================
        print("📊 Creando indicadores...")
        
        indicador1 = Indicador(
            codigo="IND-001",
            nombre="Satisfacción del Cliente",
            descripcion="Mide la satisfacción general",
            tipo_indicador="eficacia",
            categoria="cliente",
            unidad_medida="%",
            meta=Decimal("95.00"),
            frecuencia_medicion="mensual",
            responsable_id=admin.id,
            area_id=area_calidad.id,
            estado="activo"
        )
        
        indicador2 = Indicador(
            codigo="IND-002",
            nombre="Tasa de Defectos",
            descripcion="Productos no conformes",
            tipo_indicador="eficiencia",
            categoria="produccion",
            unidad_medida="ppm",
            meta=Decimal("100.00"),
            frecuencia_medicion="semanal",
            responsable_id=admin.id,
            area_id=area_calidad.id,
            estado="activo"
        )
        
        db.add_all([indicador1, indicador2])
        
        # No conformidades
        print("⚠️  Creando no conformidades...")
        
        nc1 = NoConformidad(
            codigo="NC-001",
            descripcion="Producto con dimensiones fuera de especificación",
            tipo="producto",
            fuente="inspeccion",
            severidad="mayor",
            estado="abierta",
            fecha_deteccion=datetime.utcnow() - timedelta(days=5),
            detectado_por_id=admin.id,
            area_afectada_id=area_ops.id
        )
        
        nc2 = NoConformidad(
            codigo="NC-002",
            descripcion="Documentación de proceso incompleta",
            tipo="sistema",
            fuente="auditoria",
            severidad="menor",
            estado="en_tratamiento",
            fecha_deteccion=datetime.utcnow() - timedelta(days=10),
            detectado_por_id=admin.id,
            area_afectada_id=area_calidad.id
        )
        
        db.add_all([nc1, nc2])
        db.flush()
        
        # Acciones correctivas
        print("🔧 Creando acciones correctivas...")
        
        ac1 = AccionCorrectiva(
            codigo="AC-001",
            descripcion="Calibrar equipo de medición",
            tipo_accion="correctiva",
            no_conformidad_id=nc1.id,
            causa_raiz="Descalibración del equipo",
            estado="en_progreso",
            prioridad="alta",
            fecha_programada=datetime.utcnow() + timedelta(days=7),
            responsable_id=admin.id
        )
        
        db.add(ac1)
        
        # Objetivos de calidad
        print("🎯 Creando objetivos de calidad...")
        
        obj1 = ObjetivoCalidad(
            codigo="OBJ-001",
            nombre="Reducir Defectos 20%",
            descripcion="Reducir tasa de defectos en 20% este año",
            tipo_objetivo="mejora",
            categoria="calidad",
            meta_numerica=Decimal("20.00"),
            unidad_medida="%",
            fecha_inicio=datetime.utcnow() - timedelta(days=30),
            fecha_fin=datetime.utcnow() + timedelta(days=335),
            responsable_id=admin.id,
            area_id=area_calidad.id,
            estado="en_progreso"
        )
        
        db.add(obj1)
        
        # ========================
        # AUDITORÍAS
        # ========================
        print("🔍 Creando auditorías...")
        
        auditoria1 = Auditoria(
            codigo="AUD-001",
            titulo="Auditoría Interna Q1",
            tipo_auditoria="interna",
            alcance="Sistema de gestión de calidad",
            fecha_programada=datetime.utcnow() + timedelta(days=15),
            duracion_dias=2,
            lider_auditoria_id=admin.id,
            area_auditada_id=area_calidad.id,
            estado="programada"
        )
        
        auditoria2 = Auditoria(
            codigo="AUD-002",
            titulo="Auditoría de Procesos",
            tipo_auditoria="proceso",
            alcance="Procesos operativos",
            fecha_programada=datetime.utcnow() + timedelta(days=30),
            duracion_dias=3,
            lider_auditoria_id=admin.id,
            area_auditada_id=area_ops.id,
            estado="programada"
        )
        
        db.add_all([auditoria1, auditoria2])
        
        # ========================
        # RIESGOS
        # ========================
        print("⚡ Creando riesgos...")
        
        riesgo1 = Riesgo(
            codigo="RISK-001",
            nombre="Fallo de proveedor crítico",
            descripcion="Proveedor único de materia prima",
            categoria="operacional",
            tipo_riesgo="amenaza",
            probabilidad=3,
            impacto=4,
            nivel_riesgo="alto",
            estado="activo",
            responsable_id=admin.id,
            area_id=area_ops.id,
            proceso_id=proceso1.id
        )
        
        riesgo2 = Riesgo(
            codigo="RISK-002",
            nombre="Pérdida de certificación",
            descripcion="Riesgo de perder certificación ISO",
            categoria="cumplimiento",
            tipo_riesgo="amenaza",
            probabilidad=2,
            impacto=5,
            nivel_riesgo="alto",
            estado="activo",
            responsable_id=admin.id,
            area_id=area_calidad.id
        )
        
        db.add_all([riesgo1, riesgo2])
        db.flush()
        
        # Controles de riesgo
        control1 = ControlRiesgo(
            riesgo_id=riesgo1.id,
            nombre="Diversificación de proveedores",
            descripcion="Identificar y calificar proveedores alternativos",
            tipo_control="preventivo",
            estado="implementado",
            responsable_id=admin.id,
            fecha_implementacion=datetime.utcnow() - timedelta(days=60)
        )
        
        db.add(control1)
        
        # ========================
        # CAPACITACIONES
        # ========================
        print("🎓 Creando capacitaciones...")
        
        cap1 = Capacitacion(
            codigo="CAP-001",
            nombre="ISO 9001:2015 Fundamentos",
            descripcion="Introducción a la norma ISO 9001",
            tipo_capacitacion="tecnica",
            modalidad="presencial",
            duracion_horas=8,
            instructor="Consultor Externo",
            fecha_programada=datetime.utcnow() + timedelta(days=20),
            lugar="Sala de capacitación",
            estado="programada",
            objetivo="Conocer requisitos de ISO 9001",
            responsable_id=admin.id
        )
        
        cap2 = Capacitacion(
            codigo="CAP-002",
            nombre="Auditorías Internas",
            descripcion="Técnicas de auditoría interna",
            tipo_capacitacion="gestion",
            modalidad="virtual",
            duracion_horas=16,
            instructor="Instructor Certificado",
            fecha_programada=datetime.utcnow() + timedelta(days=40),
            estado="programada",
            objetivo="Formar auditores internos",
            responsable_id=admin.id
        )
        
        db.add_all([cap1, cap2])
        
        # ========================
        # SISTEMA (Tickets, Notificaciones)
        # ========================
        print("🎫 Creando tickets...")
        
        ticket1 = Ticket(
            codigo="TK-001",
            titulo="Solicitud de Calibración",
            descripcion="Requiere calibración de balanza analítica",
            categoria="mantenimiento",
            prioridad="media",
            estado="abierto",
            solicitante_id=admin.id,
            fecha_limite=datetime.utcnow() + timedelta(days=10)
        )
        
        ticket2 = Ticket(
            codigo="TK-002",
            titulo="Actualización de Procedimiento",
            descripcion="Actualizar procedimiento de compras",
            categoria="documentacion",
            prioridad="baja",
            estado="abierto",
            solicitante_id=admin.id,
            asignado_a=admin.id,
            fecha_limite=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add_all([ticket1, ticket2])
        
        # Notificaciones
        print("🔔 Creando notificaciones...")
        
        notif1 = Notificacion(
            usuario_id=admin.id,
            titulo="Nueva No Conformidad",
            mensaje="Se detectó una nueva no conformidad NC-001",
            tipo="alerta",
            leida=False,
            referencia_tipo="no_conformidad",
            referencia_id=nc1.id
        )
        
        notif2 = Notificacion(
            usuario_id=admin.id,
            titulo="Auditoría Programada",
            mensaje="Auditoría interna programada para dentro de 15 días",
            tipo="informacion",
            leida=False,
            referencia_tipo="auditoria",
            referencia_id=auditoria1.id
        )
        
        db.add_all([notif1, notif2])
        
        # Configuraciones
        print("⚙️  Creando configuraciones...")
        
        config1 = Configuracion(
            clave="sistema.nombre",
            valor="Sistema de Gestión de Calidad",
            descripcion="Nombre del sistema",
            tipo_dato="string",
            categoria="general"
        )
        
        config2 = Configuracion(
            clave="notificaciones.email.habilitado",
            valor="true",
            descripcion="Habilitar notificaciones por email",
            tipo_dato="boolean",
            categoria="notificaciones"
        )
        
        db.add_all([config1, config2])
        
        # Commit de todos los cambios
        db.commit()
        
        print("\n✅ Datos de prueba creados exitosamente!")
        print("\n📊 Resumen:")
        print(f"   - 2 Procesos")
        print(f"   - 2 Etapas de proceso")
        print(f"   - 2 Documentos + 1 Versión")
        print(f"   - 2 Indicadores")
        print(f"   - 2 No Conformidades")
        print(f"   - 1 Acción Correctiva")
        print(f"   - 1 Objetivo de Calidad")
        print(f"   - 2 Auditorías")
        print(f"   - 2 Riesgos + 1 Control")
        print(f"   - 2 Capacitaciones")
        print(f"   - 2 Tickets")
        print(f"   - 2 Notificaciones")
        print(f"   - 2 Configuraciones")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al crear datos de prueba: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("   CREAR DATOS DE PRUEBA - Sistema de Gestión de Calidad")
    print("=" * 60)
    create_test_data()
