"""
Endpoints para analítica y dashboards
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from ..database import get_db
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario

# Models for aggregation
from ..models.calidad import NoConformidad, ObjetivoCalidad, Indicador
from ..models.riesgo import Riesgo
from ..models.documento import Documento
from ..models.auditoria import Auditoria, HallazgoAuditoria

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/calidad")
def get_calidad_metrics(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
):
    """Estadísticas de Riesgos"""
    total_riesgos = db.query(func.count(Riesgo.id)).scalar()
    
    return {
        "total_riesgos": total_riesgos
    }

@router.get("/riesgos/heatmap")
def get_riesgos_heatmap(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
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
