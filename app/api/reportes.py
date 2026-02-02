
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario
from ..models.auditoria import Auditoria
from ..models.calidad import NoConformidad
from ..services.reportes import PDFService

router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"])

@router.get("/list")
def list_available_reports(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Devuelve listado unificado de reportes disponibles (Auditorías, NCs)"""
    
    reports = []
    
    try:
        # 1. Auditorías Completadas (o todas)
        auditorias = db.query(Auditoria).order_by(Auditoria.fecha_programada.desc().nullslast()).limit(10).all()
        for aud in auditorias:
            reports.append({
                "id": str(aud.id),
                "codigo": aud.codigo or f"AUD-{str(aud.id)[:8]}",
                "title": f"Reporte de Auditoría: {aud.codigo or 'Sin código'}",
                "category": "auditorias",
                "date": aud.fecha_programada.isoformat() if aud.fecha_programada else datetime.now().isoformat(),
                "status": aud.estado or "completado",
                "format": "PDF",
                "description": f"Auditoría de {aud.objetivo or 'gestión'}"
            })
            
        # 2. No Conformidades (Global)
        # Agregamos un item "metareporte" global
        reports.append({
            "id": "global-nc",
            "codigo": "REP-NC-2024",
            "title": "Reporte Global de No Conformidades",
            "category": "noconformidades",
            "date": datetime.now().isoformat(),
            "status": "completado",
            "format": "PDF",
            "description": "Listado completo de hallazgos no conformes"
        })
    except Exception as e:
        # Log error and return empty list instead of crashing
        print(f"Error generating reports list: {e}")
        reports = []
    
    return reports

@router.get("/auditorias/{auditoria_id}/pdf")
def descargar_reporte_auditoria(
    auditoria_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Generar y descargar PDF de una auditoría"""
    auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
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
    year: int = 2024,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    filename = f"reporte_noconformidades_{year}.pdf"
    
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(
        pdf_buffer, 
        headers=headers, 
        media_type="application/pdf"
    )
