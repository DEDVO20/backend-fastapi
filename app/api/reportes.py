import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import StreamingResponse
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..api.dependencies import require_any_permission
from ..models.usuario import Usuario
from ..models.auditoria import Auditoria
from ..models.calidad import NoConformidad
from ..services.reportes import PDFService

router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"])
logger = logging.getLogger(__name__)

@router.get("/list")
def list_available_reports(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["auditorias.ver", "noconformidades.gestion", "sistema.admin"]))
) -> List[Dict[str, Any]]:
    """Devuelve listado unificado de reportes disponibles (Auditorías, NCs)"""

    now = datetime.now()
    reports: List[Dict[str, Any]] = []

    try:
        # 1. Auditorías (ordenadas por fecha planificada)
        auditorias = (
            db.query(Auditoria)
            .order_by(Auditoria.fecha_planificada.desc().nullslast())
            .limit(10)
            .all()
        )
        for aud in auditorias:
            report_date = aud.fecha_planificada.isoformat() if aud.fecha_planificada else now.isoformat()
            reports.append({
                "id": str(aud.id),
                "codigo": aud.codigo or f"AUD-{str(aud.id)[:8]}",
                "title": f"Reporte de Auditoría: {aud.codigo or 'Sin código'}",
                "category": "auditorias",
                "date": report_date,
                "status": aud.estado or "completado",
                "format": "PDF",
                "description": f"Auditoría de {aud.objetivo or 'gestión'}"
            })
    except Exception:
        logger.exception("Error generating auditoria reports list")

    # 2. No Conformidades (Global)
    # Se agrega siempre para no perder la funcionalidad si fallan auditorías.
    reports.append({
        "id": "global-nc",
        "codigo": f"REP-NC-{now.year}",
        "title": "Reporte Global de No Conformidades",
        "category": "noconformidades",
        "date": now.isoformat(),
        "status": "completado",
        "format": "PDF",
        "description": "Listado completo de hallazgos no conformes"
    })

    return reports

@router.get("/auditorias/{auditoria_id}/pdf")
def descargar_reporte_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["auditorias.ver", "sistema.admin"]))
):
    """Generar y descargar PDF de una auditoría"""
    auditoria = db.query(Auditoria).options(
        joinedload(Auditoria.hallazgos),
        joinedload(Auditoria.auditor_lider),
    ).filter(Auditoria.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
        
    pdf_buffer = PDFService.generate_auditoria_report(auditoria)
    filename = f"auditoria_{auditoria.codigo or 'report'}.pdf"
    
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(
        pdf_buffer, 
        headers=headers, 
        media_type="application/pdf"
    )

@router.get("/noconformidades/pdf")
def descargar_reporte_noconformidades(
    estado: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any_permission(["noconformidades.gestion", "noconformidades.cerrar", "sistema.admin"]))
):
    """Generar PDF de listado de No Conformidades"""
    query = db.query(NoConformidad)
    
    if estado:
        query = query.filter(NoConformidad.estado == estado)
    
    # Optional: Filter by year if Fecha Deteccion exists
    # if year:
    #    query = query.filter(extract('year', NoConformidad.fecha_deteccion) == year)
        
    ncs = query.order_by(NoConformidad.fecha_deteccion.desc()).all()
    
    pdf_buffer = PDFService.generate_noconformidades_report(ncs)
    report_year = year or datetime.now().year
    filename = f"reporte_noconformidades_{report_year}.pdf"
    
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(
        pdf_buffer, 
        headers=headers, 
        media_type="application/pdf"
    )
