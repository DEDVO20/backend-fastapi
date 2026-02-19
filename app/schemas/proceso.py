"""
Schemas Pydantic mejorados para procesos ISO 9001:2015
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from enum import Enum


# ==================== ENUMS ISO 9001 ====================

class TipoProceso(str, Enum):
    """Tipos de proceso según ISO 9001"""
    ESTRATEGICO = "estrategico"
    OPERATIVO = "operativo"
    APOYO = "apoyo"
    MEDICION = "medicion"


class EtapaPHVA(str, Enum):
    """Ciclo PHVA (Plan-Do-Check-Act / Planear-Hacer-Verificar-Actuar)"""
    PLANEAR = "planear"
    HACER = "hacer"
    VERIFICAR = "verificar"
    ACTUAR = "actuar"


class EstadoProceso(str, Enum):
    """Estados del ciclo de vida de un proceso"""
    BORRADOR = "borrador"
    REVISION = "revision"
    ACTIVO = "activo"
    SUSPENDIDO = "suspendido"
    OBSOLETO = "obsoleto"


class EstadoInstancia(str, Enum):
    """Estados de una instancia de proceso"""
    INICIADO = "iniciado"
    EN_PROGRESO = "en_progreso"
    PAUSADO = "pausado"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"


class TipoAccion(str, Enum):
    """Tipos de acción de mejora"""
    CORRECTIVA = "correctiva"
    PREVENTIVA = "preventiva"
    MEJORA = "mejora"


class TipoEtapaProceso(str, Enum):
    """Tipos de etapa para flujo Entrada->Actividad->Salida"""
    ENTRADA = "entrada"
    TRANSFORMACION = "transformacion"
    VERIFICACION = "verificacion"
    DECISION = "decision"
    SALIDA = "salida"


# ==================== PROCESO SCHEMAS ====================

class ProcesoBase(BaseModel):
    """Schema base para procesos"""
    codigo: str = Field(..., max_length=100, description="Código único del proceso (ej: PR-COM-001)")
    nombre: str = Field(..., max_length=300, description="Nombre descriptivo del proceso")
    area_id: Optional[UUID] = Field(None, description="Área organizacional responsable")
    objetivo: Optional[str] = Field(None, description="Objetivo del proceso según ISO 9001")
    alcance: Optional[str] = Field(None, description="Alcance y límites del proceso")
    etapa_phva: Optional[EtapaPHVA] = Field(None, description="Etapa del ciclo PHVA")
    tipo_proceso: Optional[TipoProceso] = Field(None, description="Clasificación del proceso")
    responsable_id: Optional[UUID] = Field(None, description="Dueño del proceso")
    estado: EstadoProceso = Field(default=EstadoProceso.BORRADOR, description="Estado actual")
    version: Optional[str] = Field(None, max_length=20, description="Versión del proceso (ej: 2.1)")
    fecha_aprobacion: Optional[date] = Field(None, description="Fecha de aprobación")
    proxima_revision: Optional[date] = Field(None, description="Fecha de próxima revisión")
    restringido: bool = Field(default=False, description="Acceso restringido")
    
    # Campos adicionales ISO 9001
    entradas: Optional[str] = Field(None, description="Entradas del proceso")
    salidas: Optional[str] = Field(None, description="Salidas del proceso")
    recursos_necesarios: Optional[str] = Field(None, description="Recursos necesarios")
    criterios_desempeno: Optional[str] = Field(None, description="Criterios de desempeño")
    riesgos_oportunidades: Optional[str] = Field(None, description="Riesgos y oportunidades identificados")
    
    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        """Validar formato de código"""
        if not v or len(v) < 3:
            raise ValueError('El código debe tener al menos 3 caracteres')
        return v.upper().strip()
    
    @field_validator('version')
    @classmethod
    def validar_version(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de versión"""
        if v and not v.replace('.', '').isdigit():
            raise ValueError('La versión debe tener formato numérico (ej: 1.0, 2.1)')
        return v


class ProcesoCreate(ProcesoBase):
    """Schema para crear un proceso"""
    pass


class ProcesoUpdate(BaseModel):
    """Schema para actualizar un proceso"""
    codigo: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=300)
    area_id: Optional[UUID] = None
    objetivo: Optional[str] = None
    alcance: Optional[str] = None
    etapa_phva: Optional[EtapaPHVA] = None
    tipo_proceso: Optional[TipoProceso] = None
    responsable_id: Optional[UUID] = None
    estado: Optional[EstadoProceso] = None
    version: Optional[str] = Field(None, max_length=20)
    fecha_aprobacion: Optional[date] = None
    proxima_revision: Optional[date] = None
    restringido: Optional[bool] = None
    entradas: Optional[str] = None
    salidas: Optional[str] = None
    recursos_necesarios: Optional[str] = None
    criterios_desempeno: Optional[str] = None
    riesgos_oportunidades: Optional[str] = None


class ProcesoResponse(ProcesoBase):
    """Schema de respuesta para proceso"""
    id: UUID
    creado_por: Optional[UUID] = None
    creado_en: datetime
    actualizado_en: datetime
    
    # Información relacionada (opcional)
    area_nombre: Optional[str] = None
    responsable_nombre: Optional[str] = None
    total_etapas: Optional[int] = 0
    total_indicadores: Optional[int] = 0
    total_riesgos: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)


class ProcesoDetallado(ProcesoResponse):
    """Schema de respuesta detallada con relaciones"""
    etapas: List['EtapaProcesoResponse'] = []
    indicadores_count: int = 0
    riesgos_count: int = 0
    documentos_count: int = 0


# ==================== ETAPA PROCESO SCHEMAS ====================

class EtapaProcesoBase(BaseModel):
    """Schema base para etapas de proceso"""
    proceso_id: UUID
    nombre: str = Field(..., max_length=200, description="Nombre de la etapa")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    orden: int = Field(default=1, ge=1, description="Orden de ejecución")
    responsable_id: Optional[UUID] = Field(None, description="Responsable de la etapa")
    tiempo_estimado: Optional[int] = Field(None, ge=0, description="Tiempo estimado en minutos")
    activa: bool = Field(default=True, description="Etapa activa")
    
    # Campos adicionales
    criterios_aceptacion: Optional[str] = Field(None, description="Criterios de aceptación")
    documentos_requeridos: Optional[str] = Field(None, description="Documentos necesarios")
    es_critica: bool = Field(default=False, description="Punto de control crítico")
    tipo_etapa: Optional[TipoEtapaProceso] = Field(default=TipoEtapaProceso.TRANSFORMACION, description="Tipo de etapa")
    etapa_phva: Optional[EtapaPHVA] = Field(default=None, description="Etapa PHVA de la actividad")
    entradas: Optional[str] = Field(None, description="Entradas que recibe la etapa")
    salidas: Optional[str] = Field(None, description="Salidas que produce la etapa")
    controles: Optional[str] = Field(None, description="Controles aplicados")
    registros_requeridos: Optional[str] = Field(None, description="Registros generados por la etapa")


class EtapaProcesoCreate(EtapaProcesoBase):
    """Schema para crear etapa de proceso"""
    pass


class EtapaProcesoUpdate(BaseModel):
    """Schema para actualizar etapa de proceso"""
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    orden: Optional[int] = Field(None, ge=1)
    responsable_id: Optional[UUID] = None
    tiempo_estimado: Optional[int] = Field(None, ge=0)
    activa: Optional[bool] = None
    criterios_aceptacion: Optional[str] = None
    documentos_requeridos: Optional[str] = None
    es_critica: Optional[bool] = None
    tipo_etapa: Optional[TipoEtapaProceso] = None
    etapa_phva: Optional[EtapaPHVA] = None
    entradas: Optional[str] = None
    salidas: Optional[str] = None
    controles: Optional[str] = None
    registros_requeridos: Optional[str] = None


class EtapaProcesoResponse(EtapaProcesoBase):
    """Schema de respuesta para etapa de proceso"""
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    responsable_nombre: Optional[str] = None
    hallazgos_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class EtapaProcesoOrdenItem(BaseModel):
    """Item para reordenamiento de etapas"""
    id: UUID
    orden: int = Field(..., ge=1)


# ==================== INSTANCIA PROCESO SCHEMAS ====================

class InstanciaProcesoBase(BaseModel):
    """Schema base para instancias de proceso"""
    proceso_id: UUID
    codigo_instancia: str = Field(..., max_length=100, description="Código único de la instancia")
    descripcion: Optional[str] = Field(None, description="Descripción de la ejecución")
    estado: EstadoInstancia = Field(default=EstadoInstancia.INICIADO)
    fecha_inicio: datetime = Field(default_factory=datetime.now)
    fecha_fin: Optional[datetime] = None
    iniciado_por: Optional[UUID] = None
    observaciones: Optional[str] = None


class InstanciaProcesoCreate(InstanciaProcesoBase):
    """Schema para crear instancia de proceso"""
    pass


class InstanciaProcesoUpdate(BaseModel):
    """Schema para actualizar instancia de proceso"""
    descripcion: Optional[str] = None
    estado: Optional[EstadoInstancia] = None
    fecha_fin: Optional[datetime] = None
    observaciones: Optional[str] = None


class InstanciaProcesoResponse(InstanciaProcesoBase):
    """Schema de respuesta para instancia de proceso"""
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    proceso_nombre: Optional[str] = None
    iniciador_nombre: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== ACCION PROCESO SCHEMAS ====================

class AccionProcesoBase(BaseModel):
    """Schema base para acciones de mejora en procesos"""
    proceso_id: UUID
    codigo: str = Field(..., max_length=100, description="Código de la acción")
    nombre: str = Field(..., max_length=200, description="Nombre de la acción")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    tipo_accion: TipoAccion = Field(..., description="Tipo de acción")
    origen: Optional[str] = Field(None, max_length=100, description="Origen de la acción")
    responsable_id: Optional[UUID] = None
    fecha_planificada: Optional[datetime] = None
    fecha_implementacion: Optional[datetime] = None
    fecha_verificacion: Optional[datetime] = None
    estado: str = Field(default='planificada', max_length=50)
    efectividad: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None


class AccionProcesoCreate(AccionProcesoBase):
    """Schema para crear acción de proceso"""
    pass


class AccionProcesoUpdate(BaseModel):
    """Schema para actualizar acción de proceso"""
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    tipo_accion: Optional[TipoAccion] = None
    origen: Optional[str] = Field(None, max_length=100)
    responsable_id: Optional[UUID] = None
    fecha_planificada: Optional[datetime] = None
    fecha_implementacion: Optional[datetime] = None
    fecha_verificacion: Optional[datetime] = None
    estado: Optional[str] = Field(None, max_length=50)
    efectividad: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None


class AccionProcesoResponse(AccionProcesoBase):
    """Schema de respuesta para acción de proceso"""
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    proceso_nombre: Optional[str] = None
    responsable_nombre: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS DE ESTADÍSTICAS ====================

class ProcesoEstadisticas(BaseModel):
    """Estadísticas de procesos"""
    total_procesos: int
    por_tipo: dict
    por_estado: dict
    por_etapa_phva: dict
    procesos_proximos_revision: int
    procesos_sin_responsable: int
