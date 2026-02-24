"""
Endpoints para analítica y dashboards
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from ..database import get_db
from ..api.dependencies import require_any_permission
from ..models.usuario import Usuario

# Models for aggregation
from ..models.calidad import NoConformidad, ObjetivoCalidad, Indicador
from ..models.riesgo import Riesgo
from ..models.documento import Documento
from ..models.auditoria import Auditoria, HallazgoAuditoria
from ..models.competencia import BrechaCompetencia
from ..models.proceso import Proceso, EtapaProceso

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
ESTADOS_BRECHA_ABIERTA = ("abierta", "pendiente", "en_capacitacion")

@router.get("/calidad")
def get_calidad_metrics(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["calidad.ver", "sistema.admin"]))
):
    """Métricas generales de Calidad para el Dashboard"""
    
    # 1. No Conformidades por Estado
    nc_stats = db.query(
        NoConformidad.estado, func.count(NoConformidad.id)
    ).group_by(NoConformidad.estado).all()
    
    # 2. Objetivos de Calidad (Activos vs Total)
    total_objetivos = db.query(func.count(ObjetivoCalidad.id)).scalar()
    
    # 3. Indicadores
    total_indicadores = db.query(func.count(Indicador.id)).scalar()
    
    return {
        "noconformidades": {state: count for state, count in nc_stats},
        "objetivos_total": total_objetivos,
        "indicadores_total": total_indicadores
    }

@router.get("/riesgos/stats")
def get_riesgos_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["riesgos.ver", "riesgos.gestion", "sistema.admin"]))
):
    """Estadísticas de Riesgos"""
    total_riesgos = db.query(func.count(Riesgo.id)).scalar()
    
    return {
        "total_riesgos": total_riesgos
    }

@router.get("/riesgos/heatmap")
def get_riesgos_heatmap(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["riesgos.ver", "riesgos.gestion", "sistema.admin"]))
):
    """Datos para la Matriz de Calor de Riesgos (Probabilidad vs Impacto)"""
    
    # Agrupar por probabilidad e impacto
    # Asumiendo que el modelo Riesgo tiene campos 'probabilidad' e 'impacto' (int o str)
    # Si son numéricos 1-5, perfecto.
    
    heatmap_data = db.query(
        Riesgo.probabilidad, 
        Riesgo.impacto, 
        func.count(Riesgo.id)
    ).group_by(Riesgo.probabilidad, Riesgo.impacto).all()
    
    # Formatear para frontend: Lista de {x: prob, y: imp, value: count}
    matrix = []
    for prob, imp, count in heatmap_data:
        matrix.append({
            "probabilidad": prob,
            "impacto": imp,
            "cantidad": count
        })
        
    return matrix

@router.get("/documentos/stats")
def get_documentos_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["documentos.ver", "sistema.admin"]))
):
    """Estadísticas de Documentos"""
    
    # 1. Documentos por Estado
    doc_stats = db.query(
        Documento.estado, func.count(Documento.id)
    ).group_by(Documento.estado).all()
    
    return {
        "por_estado": {state: count for state, count in doc_stats}
    }

@router.get("/auditorias/stats")
def get_auditorias_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["auditorias.ver", "sistema.admin"]))
):
    """Estadísticas de Auditorías y Hallazgos"""
    
    # Hallazgos por Tipo
    hallazgos_stats = db.query(
        HallazgoAuditoria.tipo_hallazgo, func.count(HallazgoAuditoria.id)
    ).group_by(HallazgoAuditoria.tipo_hallazgo).all()
    
    total_auditorias = db.query(func.count(Auditoria.id)).scalar()
    
    return {
        "hallazgos_por_tipo": {tipo: count for tipo, count in hallazgos_stats},
        "total_auditorias": total_auditorias
    }


@router.get("/competencias/riesgo-humano")
def get_competencias_riesgo_humano(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["capacitaciones.gestion", "riesgos.gestion", "sistema.admin"])),
):
    """KPIs estratégicos de brechas de competencia y riesgo humano."""
    brechas_abiertas = db.query(func.count(BrechaCompetencia.id)).filter(
        BrechaCompetencia.estado.in_(ESTADOS_BRECHA_ABIERTA),
        BrechaCompetencia.activo.is_(True),
    ).scalar() or 0

    brechas_criticas = db.query(func.count(BrechaCompetencia.id)).filter(
        BrechaCompetencia.estado.in_(ESTADOS_BRECHA_ABIERTA),
        BrechaCompetencia.riesgo_id.isnot(None),
        BrechaCompetencia.activo.is_(True),
    ).scalar() or 0

    total_riesgos = db.query(func.count(Riesgo.id)).filter(Riesgo.activo.is_(True)).scalar() or 0
    riesgos_con_incremento = db.query(func.count(Riesgo.id)).filter(
        Riesgo.activo.is_(True),
        Riesgo.nivel_residual.isnot(None),
        Riesgo.probabilidad.isnot(None),
        Riesgo.impacto.isnot(None),
        Riesgo.nivel_residual > (Riesgo.probabilidad * Riesgo.impacto),
    ).scalar() or 0

    procesos_totales = db.query(func.count(Proceso.id)).filter(Proceso.activo.is_(True)).scalar() or 0
    procesos_vulnerables = db.query(func.count(func.distinct(EtapaProceso.proceso_id))).join(
        BrechaCompetencia,
        BrechaCompetencia.etapa_id == EtapaProceso.id,
    ).filter(
        EtapaProceso.activo.is_(True),
        BrechaCompetencia.estado.in_(ESTADOS_BRECHA_ABIERTA),
    ).scalar() or 0

    indice_riesgo_humano = round((brechas_criticas / max(total_riesgos, 1)) * 100, 2)
    cobertura_competencias = round(((total_riesgos - riesgos_con_incremento) / max(total_riesgos, 1)) * 100, 2)

    return {
        "brechas_abiertas": int(brechas_abiertas),
        "brechas_criticas": int(brechas_criticas),
        "riesgos_con_incremento_por_factor_humano": int(riesgos_con_incremento),
        "indice_riesgo_humano": indice_riesgo_humano,
        "procesos_vulnerables": int(procesos_vulnerables),
        "total_procesos": int(procesos_totales),
        "cobertura_competencias": cobertura_competencias,
    }
