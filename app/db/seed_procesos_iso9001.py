"""
Seeder de procesos ISO 9001:2015
Crea procesos de ejemplo siguiendo los requisitos de la norma
"""
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.models.proceso import Proceso, EtapaProceso
from app.models.usuario import Area, Usuario


def crear_procesos_iso9001(db: Session):
    """
    Crear procesos de ejemplo siguiendo ISO 9001:2015
    
    Estructura de procesos según ISO 9001:
    - Procesos Estratégicos
    - Procesos Operativos (Clave)
    - Procesos de Apoyo
    - Procesos de Medición y Mejora
    """
    
    # Obtener áreas
    area_direccion = db.query(Area).filter(Area.codigo == "DIR").first()
    area_calidad = db.query(Area).filter(Area.codigo == "CAL").first()
    area_operaciones = db.query(Area).filter(Area.codigo == "OPE").first()
    area_admin = db.query(Area).filter(Area.codigo == "ADM").first()
    
    # Obtener usuario admin como responsable por defecto
    admin = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
    
    if not admin:
        print("⚠️  No se encontró usuario admin. Creando procesos sin responsable.")
    
    # ==================== PROCESOS ESTRATÉGICOS ====================
    
    procesos_estrategicos = [
        {
            "codigo": "PE-DIR-001",
            "nombre": "Planificación Estratégica",
            "area_id": area_direccion.id if area_direccion else None,
            "objetivo": "Establecer la dirección estratégica de la organización, definiendo objetivos, políticas y recursos necesarios para el cumplimiento de la misión y visión institucional.",
            "alcance": "Desde el análisis del contexto organizacional hasta la definición de objetivos estratégicos y su despliegue en la organización.",
            "etapa_phva": "planear",
            "tipo_proceso": "estrategico",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.0",
            "fecha_aprobacion": date.today() - timedelta(days=180),
            "proxima_revision": date.today() + timedelta(days=185),
            "entradas": "Contexto organizacional, Necesidades y expectativas de partes interesadas, Resultados de revisiones anteriores",
            "salidas": "Plan estratégico, Objetivos de calidad, Política de calidad, Asignación de recursos",
            "recursos_necesarios": "Equipo directivo, Información del mercado, Datos históricos, Herramientas de análisis estratégico",
            "criterios_desempeno": "Cumplimiento de objetivos estratégicos (≥90%), Satisfacción de partes interesadas, Indicadores financieros",
            "riesgos_oportunidades": "Riesgo: Cambios en el entorno regulatorio. Oportunidad: Nuevos mercados emergentes"
        },
        {
            "codigo": "PE-DIR-002",
            "nombre": "Revisión por la Dirección",
            "area_id": area_direccion.id if area_direccion else None,
            "objetivo": "Asegurar la conveniencia, adecuación, eficacia y alineación continua del Sistema de Gestión de Calidad con la dirección estratégica de la organización.",
            "alcance": "Revisión periódica del desempeño del SGC, análisis de resultados y toma de decisiones para la mejora continua.",
            "etapa_phva": "verificar",
            "tipo_proceso": "estrategico",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.0",
            "fecha_aprobacion": date.today() - timedelta(days=150),
            "proxima_revision": date.today() + timedelta(days=215),
            "entradas": "Resultados de auditorías, Desempeño de procesos, Satisfacción del cliente, No conformidades y acciones correctivas",
            "salidas": "Decisiones de mejora, Cambios en el SGC, Necesidades de recursos, Acciones de seguimiento",
            "recursos_necesarios": "Alta dirección, Representante de la dirección, Datos del SGC, Sala de reuniones",
            "criterios_desempeno": "Frecuencia de revisiones (mínimo 2/año), Implementación de decisiones (≥85%), Mejora de indicadores clave",
            "riesgos_oportunidades": "Riesgo: Falta de seguimiento a decisiones. Oportunidad: Identificación temprana de mejoras"
        },
        {
            "codigo": "PE-CAL-001",
            "nombre": "Gestión de Riesgos y Oportunidades",
            "area_id": area_calidad.id if area_calidad else None,
            "objetivo": "Identificar, analizar, evaluar y tratar los riesgos y oportunidades que puedan afectar la conformidad de productos/servicios y la satisfacción del cliente.",
            "alcance": "Desde la identificación de riesgos hasta la implementación de controles y seguimiento de su eficacia.",
            "etapa_phva": "planear",
            "tipo_proceso": "estrategico",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "2.0",
            "fecha_aprobacion": date.today() - timedelta(days=90),
            "proxima_revision": date.today() + timedelta(days=275),
            "entradas": "Contexto de la organización, Procesos del SGC, Requisitos legales, Lecciones aprendidas",
            "salidas": "Matriz de riesgos, Plan de tratamiento, Controles implementados, Indicadores de riesgo",
            "recursos_necesarios": "Equipo multidisciplinario, Metodología de análisis de riesgos, Software de gestión de riesgos",
            "criterios_desempeno": "Cobertura de procesos críticos (100%), Efectividad de controles (≥80%), Reducción de incidentes",
            "riesgos_oportunidades": "Riesgo: Subestimación de riesgos emergentes. Oportunidad: Innovación a partir de análisis de oportunidades"
        }
    ]
    
    # ==================== PROCESOS OPERATIVOS ====================
    
    procesos_operativos = [
        {
            "codigo": "PO-COM-001",
            "nombre": "Gestión de Compras",
            "area_id": area_operaciones.id if area_operaciones else None,
            "objetivo": "Asegurar la adquisición oportuna de bienes y servicios que cumplan los requisitos establecidos, garantizando la calidad y optimizando costos.",
            "alcance": "Desde la identificación de necesidades de compra hasta la recepción, evaluación de proveedores y pago.",
            "etapa_phva": "hacer",
            "tipo_proceso": "operativo",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.5",
            "fecha_aprobacion": date.today() - timedelta(days=120),
            "proxima_revision": date.today() + timedelta(days=245),
            "entradas": "Requisiciones de compra, Especificaciones técnicas, Presupuesto aprobado, Lista de proveedores aprobados",
            "salidas": "Órdenes de compra, Productos/servicios recibidos, Evaluación de proveedores, Registros de compras",
            "recursos_necesarios": "Personal de compras, Sistema de gestión de compras, Criterios de evaluación de proveedores",
            "criterios_desempeno": "Cumplimiento de entregas a tiempo (≥95%), Conformidad de productos (≥98%), Ahorro en compras (≥5% anual)",
            "riesgos_oportunidades": "Riesgo: Dependencia de proveedores únicos. Oportunidad: Alianzas estratégicas con proveedores clave"
        },
        {
            "codigo": "PO-PRO-001",
            "nombre": "Producción y Prestación del Servicio",
            "area_id": area_operaciones.id if area_operaciones else None,
            "objetivo": "Ejecutar las actividades de producción/prestación del servicio bajo condiciones controladas, asegurando la conformidad con los requisitos del cliente.",
            "alcance": "Desde la recepción de la orden de trabajo hasta la entrega del producto/servicio al cliente.",
            "etapa_phva": "hacer",
            "tipo_proceso": "operativo",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "2.1",
            "fecha_aprobacion": date.today() - timedelta(days=60),
            "proxima_revision": date.today() + timedelta(days=305),
            "entradas": "Órdenes de trabajo, Especificaciones del cliente, Materias primas/insumos, Personal capacitado",
            "salidas": "Productos/servicios conformes, Registros de producción, Productos no conformes (si aplica)",
            "recursos_necesarios": "Infraestructura de producción, Personal competente, Equipos calibrados, Procedimientos documentados",
            "criterios_desempeno": "Conformidad del producto (≥99%), Productividad (unidades/hora), Tiempo de ciclo, Índice de rechazos (<1%)",
            "riesgos_oportunidades": "Riesgo: Fallas en equipos críticos. Oportunidad: Automatización de procesos repetitivos"
        },
        {
            "codigo": "PO-VEN-001",
            "nombre": "Gestión Comercial y Ventas",
            "area_id": area_operaciones.id if area_operaciones else None,
            "objetivo": "Identificar oportunidades de negocio, gestionar la relación con clientes y asegurar la satisfacción mediante productos/servicios que cumplan sus requisitos.",
            "alcance": "Desde la prospección de clientes hasta el cierre de ventas y seguimiento postventa.",
            "etapa_phva": "hacer",
            "tipo_proceso": "operativo",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.0",
            "fecha_aprobacion": date.today() - timedelta(days=200),
            "proxima_revision": date.today() + timedelta(days=165),
            "entradas": "Estrategia comercial, Base de datos de clientes, Catálogo de productos/servicios, Presupuestos",
            "salidas": "Contratos/pedidos, Requisitos del cliente documentados, Pronósticos de ventas, Retroalimentación del cliente",
            "recursos_necesarios": "Equipo comercial, CRM, Material promocional, Canales de comunicación",
            "criterios_desempeno": "Cumplimiento de metas de ventas (≥90%), Satisfacción del cliente (≥4.5/5), Tasa de conversión (≥25%)",
            "riesgos_oportunidades": "Riesgo: Pérdida de clientes clave. Oportunidad: Expansión a nuevos segmentos de mercado"
        }
    ]
    
    # ==================== PROCESOS DE APOYO ====================
    
    procesos_apoyo = [
        {
            "codigo": "PA-RH-001",
            "nombre": "Gestión del Talento Humano",
            "area_id": area_admin.id if area_admin else None,
            "objetivo": "Asegurar que la organización cuente con el personal competente necesario para el funcionamiento eficaz del SGC y el logro de los objetivos.",
            "alcance": "Desde el reclutamiento y selección hasta la capacitación, evaluación del desempeño y desarrollo del personal.",
            "etapa_phva": "hacer",
            "tipo_proceso": "apoyo",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.2",
            "fecha_aprobacion": date.today() - timedelta(days=100),
            "proxima_revision": date.today() + timedelta(days=265),
            "entradas": "Perfiles de cargo, Necesidades de personal, Presupuesto de RRHH, Evaluaciones de desempeño",
            "salidas": "Personal competente, Registros de capacitación, Evaluaciones de desempeño, Plan de desarrollo",
            "recursos_necesarios": "Equipo de RRHH, Sistema de gestión de personal, Programas de capacitación, Evaluadores",
            "criterios_desempeno": "Cumplimiento del plan de capacitación (≥90%), Competencia del personal (≥85%), Rotación de personal (<15%)",
            "riesgos_oportunidades": "Riesgo: Pérdida de personal clave. Oportunidad: Desarrollo de talento interno"
        },
        {
            "codigo": "PA-MAN-001",
            "nombre": "Mantenimiento de Infraestructura",
            "area_id": area_operaciones.id if area_operaciones else None,
            "objetivo": "Mantener la infraestructura y equipos en condiciones óptimas para asegurar la continuidad operativa y la conformidad de productos/servicios.",
            "alcance": "Mantenimiento preventivo, correctivo y predictivo de instalaciones, equipos y sistemas.",
            "etapa_phva": "hacer",
            "tipo_proceso": "apoyo",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.0",
            "fecha_aprobacion": date.today() - timedelta(days=80),
            "proxima_revision": date.today() + timedelta(days=285),
            "entradas": "Plan de mantenimiento, Equipos e infraestructura, Solicitudes de mantenimiento, Recursos asignados",
            "salidas": "Equipos operativos, Registros de mantenimiento, Indicadores de disponibilidad, Repuestos utilizados",
            "recursos_necesarios": "Personal técnico, Herramientas y repuestos, Sistema de gestión de mantenimiento, Proveedores especializados",
            "criterios_desempeno": "Disponibilidad de equipos (≥95%), Cumplimiento del plan de mantenimiento (≥90%), MTBF (Mean Time Between Failures)",
            "riesgos_oportunidades": "Riesgo: Fallas imprevistas en equipos críticos. Oportunidad: Implementación de mantenimiento predictivo"
        },
        {
            "codigo": "PA-TI-001",
            "nombre": "Gestión de Tecnologías de Información",
            "area_id": area_admin.id if area_admin else None,
            "objetivo": "Proveer y mantener los sistemas de información necesarios para soportar los procesos del SGC y la toma de decisiones basada en datos.",
            "alcance": "Desde la identificación de necesidades tecnológicas hasta la implementación, mantenimiento y seguridad de sistemas de información.",
            "etapa_phva": "hacer",
            "tipo_proceso": "apoyo",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "2.0",
            "fecha_aprobacion": date.today() - timedelta(days=45),
            "proxima_revision": date.today() + timedelta(days=320),
            "entradas": "Requisitos de sistemas, Políticas de seguridad, Presupuesto TI, Solicitudes de soporte",
            "salidas": "Sistemas operativos, Datos disponibles y seguros, Soporte técnico, Infraestructura TI actualizada",
            "recursos_necesarios": "Personal TI, Hardware y software, Licencias, Proveedores de servicios TI",
            "criterios_desempeno": "Disponibilidad de sistemas (≥99%), Tiempo de respuesta a incidentes (<4 horas), Satisfacción de usuarios (≥4/5)",
            "riesgos_oportunidades": "Riesgo: Ciberataques y pérdida de datos. Oportunidad: Transformación digital y automatización"
        }
    ]
    
    # ==================== PROCESOS DE MEDICIÓN Y MEJORA ====================
    
    procesos_medicion = [
        {
            "codigo": "PM-AUD-001",
            "nombre": "Auditorías Internas de Calidad",
            "area_id": area_calidad.id if area_calidad else None,
            "objetivo": "Determinar si el SGC es conforme con los requisitos de la norma ISO 9001 y con los requisitos propios de la organización, y si se implementa y mantiene eficazmente.",
            "alcance": "Planificación, ejecución, reporte y seguimiento de auditorías internas del SGC.",
            "etapa_phva": "verificar",
            "tipo_proceso": "medicion",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.3",
            "fecha_aprobacion": date.today() - timedelta(days=130),
            "proxima_revision": date.today() + timedelta(days=235),
            "entradas": "Programa de auditorías, Norma ISO 9001, Procedimientos del SGC, Resultados de auditorías anteriores",
            "salidas": "Informes de auditoría, No conformidades identificadas, Oportunidades de mejora, Plan de acciones correctivas",
            "recursos_necesarios": "Auditores internos competentes, Listas de verificación, Evidencias documentales, Tiempo asignado",
            "criterios_desempeno": "Cumplimiento del programa de auditorías (100%), Hallazgos cerrados a tiempo (≥90%), Mejora en procesos auditados",
            "riesgos_oportunidades": "Riesgo: Falta de independencia de auditores. Oportunidad: Identificación proactiva de mejoras"
        },
        {
            "codigo": "PM-IND-001",
            "nombre": "Seguimiento y Medición de Procesos",
            "area_id": area_calidad.id if area_calidad else None,
            "objetivo": "Monitorear y medir el desempeño de los procesos del SGC para demostrar su capacidad de alcanzar los resultados planificados.",
            "alcance": "Definición de indicadores, recolección de datos, análisis de resultados y toma de acciones de mejora.",
            "etapa_phva": "verificar",
            "tipo_proceso": "medicion",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.0",
            "fecha_aprobacion": date.today() - timedelta(days=70),
            "proxima_revision": date.today() + timedelta(days=295),
            "entradas": "Objetivos de calidad, Procesos del SGC, Datos de desempeño, Requisitos de medición",
            "salidas": "Indicadores de desempeño, Tableros de control, Análisis de tendencias, Acciones de mejora",
            "recursos_necesarios": "Sistema de indicadores, Herramientas de análisis de datos, Responsables de procesos, Software de BI",
            "criterios_desempeno": "Cobertura de procesos críticos (100%), Actualización de indicadores (mensual), Cumplimiento de metas (≥85%)",
            "riesgos_oportunidades": "Riesgo: Datos inexactos o incompletos. Oportunidad: Toma de decisiones basada en datos"
        },
        {
            "codigo": "PM-MEJ-001",
            "nombre": "Mejora Continua",
            "area_id": area_calidad.id if area_calidad else None,
            "objetivo": "Mejorar continuamente la conveniencia, adecuación y eficacia del SGC mediante el análisis de datos, acciones correctivas y preventivas.",
            "alcance": "Identificación de oportunidades de mejora, implementación de acciones y evaluación de su eficacia.",
            "etapa_phva": "actuar",
            "tipo_proceso": "medicion",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.1",
            "fecha_aprobacion": date.today() - timedelta(days=110),
            "proxima_revision": date.today() + timedelta(days=255),
            "entradas": "No conformidades, Resultados de auditorías, Quejas de clientes, Análisis de datos, Sugerencias de mejora",
            "salidas": "Acciones correctivas/preventivas, Proyectos de mejora, Cambios en el SGC, Lecciones aprendidas",
            "recursos_necesarios": "Equipo de mejora, Metodologías de mejora (PDCA, Six Sigma), Recursos para implementación",
            "criterios_desempeno": "Acciones implementadas a tiempo (≥85%), Eficacia de acciones (≥80%), Reducción de no conformidades recurrentes",
            "riesgos_oportunidades": "Riesgo: Falta de seguimiento a acciones. Oportunidad: Innovación y diferenciación competitiva"
        },
        {
            "codigo": "PM-SAT-001",
            "nombre": "Medición de Satisfacción del Cliente",
            "area_id": area_calidad.id if area_calidad else None,
            "objetivo": "Determinar el nivel de satisfacción de los clientes con los productos/servicios entregados y utilizar esta información para la mejora.",
            "alcance": "Desde el diseño de instrumentos de medición hasta el análisis de resultados y toma de acciones.",
            "etapa_phva": "verificar",
            "tipo_proceso": "medicion",
            "responsable_id": admin.id if admin else None,
            "estado": "activo",
            "version": "1.0",
            "fecha_aprobacion": date.today() - timedelta(days=50),
            "proxima_revision": date.today() + timedelta(days=315),
            "entradas": "Base de clientes, Encuestas de satisfacción, Quejas y reclamos, Datos de servicio postventa",
            "salidas": "Índice de satisfacción del cliente, Análisis de brechas, Planes de acción, Retroalimentación a procesos",
            "recursos_necesarios": "Herramientas de encuesta, Personal de análisis, Sistema CRM, Canales de comunicación",
            "criterios_desempeno": "Tasa de respuesta a encuestas (≥30%), Índice de satisfacción (≥4.5/5), Tiempo de respuesta a quejas (<48 horas)",
            "riesgos_oportunidades": "Riesgo: Baja tasa de respuesta. Oportunidad: Fidelización de clientes y mejora de imagen"
        }
    ]
    
    # Combinar todos los procesos
    todos_los_procesos = (
        procesos_estrategicos + 
        procesos_operativos + 
        procesos_apoyo + 
        procesos_medicion
    )
    
    # Crear procesos en la base de datos
    procesos_creados = []
    for proceso_data in todos_los_procesos:
        # Verificar si ya existe
        proceso_existente = db.query(Proceso).filter(
            Proceso.codigo == proceso_data["codigo"]
        ).first()
        
        if not proceso_existente:
            proceso = Proceso(**proceso_data)
            db.add(proceso)
            db.flush()
            procesos_creados.append(proceso)
            print(f"✅ Proceso creado: {proceso.codigo} - {proceso.nombre}")
        else:
            print(f"ℹ️  Proceso ya existe: {proceso_data['codigo']}")
    
    db.commit()
    print(f"\n✅ Se crearon {len(procesos_creados)} procesos ISO 9001:2015")
    
    return procesos_creados


def crear_etapas_ejemplo(db: Session):
    """Crear etapas de ejemplo para algunos procesos"""
    
    # Obtener proceso de Gestión de Compras
    proceso_compras = db.query(Proceso).filter(Proceso.codigo == "PO-COM-001").first()
    
    if proceso_compras:
        etapas_compras = [
            {
                "proceso_id": proceso_compras.id,
                "nombre": "Identificación de Necesidad",
                "descripcion": "Identificar y documentar la necesidad de compra",
                "orden": 1,
                "tiempo_estimado": 60,
                "criterios_aceptacion": "Requisición aprobada por el responsable del área",
                "documentos_requeridos": "Formato de requisición de compra"
            },
            {
                "proceso_id": proceso_compras.id,
                "nombre": "Selección de Proveedores",
                "descripcion": "Evaluar y seleccionar proveedores según criterios establecidos",
                "orden": 2,
                "tiempo_estimado": 120,
                "criterios_aceptacion": "Mínimo 3 cotizaciones evaluadas",
                "documentos_requeridos": "Matriz de evaluación de proveedores, Cotizaciones"
            },
            {
                "proceso_id": proceso_compras.id,
                "nombre": "Emisión de Orden de Compra",
                "descripcion": "Generar y enviar orden de compra al proveedor seleccionado",
                "orden": 3,
                "tiempo_estimado": 30,
                "criterios_aceptacion": "Orden de compra firmada y enviada",
                "documentos_requeridos": "Orden de compra"
            },
            {
                "proceso_id": proceso_compras.id,
                "nombre": "Recepción y Verificación",
                "descripcion": "Recibir productos/servicios y verificar conformidad",
                "orden": 4,
                "tiempo_estimado": 90,
                "criterios_aceptacion": "Productos conformes con especificaciones",
                "documentos_requeridos": "Acta de recepción, Informe de inspección"
            },
            {
                "proceso_id": proceso_compras.id,
                "nombre": "Pago y Cierre",
                "descripcion": "Procesar pago y cerrar la orden de compra",
                "orden": 5,
                "tiempo_estimado": 60,
                "criterios_aceptacion": "Pago realizado y documentado",
                "documentos_requeridos": "Comprobante de pago, Factura"
            }
        ]
        
        for etapa_data in etapas_compras:
            etapa_existente = db.query(EtapaProceso).filter(
                EtapaProceso.proceso_id == etapa_data["proceso_id"],
                EtapaProceso.nombre == etapa_data["nombre"]
            ).first()
            
            if not etapa_existente:
                etapa = EtapaProceso(**etapa_data)
                db.add(etapa)
                print(f"  ✅ Etapa creada: {etapa.nombre}")
        
        db.commit()
        print(f"✅ Etapas creadas para proceso: {proceso_compras.nombre}")


def init_procesos_iso9001(db: Session):
    """Inicializar procesos ISO 9001"""
    print("\n🌱 Creando procesos ISO 9001:2015...")
    
    procesos = crear_procesos_iso9001(db)
    crear_etapas_ejemplo(db)
    
    print("\n✅ Procesos ISO 9001:2015 creados exitosamente!")
    print(f"📊 Total de procesos: {len(procesos)}")
    print("\n📋 Tipos de procesos creados:")
    print("   - Estratégicos: 3")
    print("   - Operativos: 3")
    print("   - Apoyo: 3")
    print("   - Medición y Mejora: 4")


if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        init_procesos_iso9001(db)
    finally:
        db.close()
