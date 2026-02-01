
from io import BytesIO
from typing import List, Any, Dict
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from ..models.auditoria import Auditoria, HallazgoAuditoria
from ..models.calidad import NoConformidad

class PDFService:
    @staticmethod
    def create_header_flowables(title: str, subtitle: str = "") -> List[Any]:
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        subtitle_style = styles['Heading2']
        subtitle_style.alignment = 1 # Center
        
        flowables = []
        flowables.append(Paragraph(title, title_style))
        if subtitle:
            flowables.append(Paragraph(subtitle, subtitle_style))
        flowables.append(Spacer(1, 0.25 * inch))
        return flowables

    @staticmethod
    def generate_auditoria_report(auditoria: Auditoria) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        flowables = []
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']

        # Header
        flowables.extend(PDFService.create_header_flowables(
            f"Informe de Auditoría: {auditoria.codigo}",
            f"Fecha: {auditoria.fecha_programada}"
        ))

        # Metadata Table
        data = [
            ["ID Auditoría", str(auditoria.id)],
            ["Código", auditoria.codigo],
            ["Objetivo", auditoria.objetivo],
            ["Alcance", auditoria.alcance],
            ["Auditor Líder", auditoria.auditor_lider.nombre_completo if auditoria.auditor_lider else "N/A"],
            ["Estado", auditoria.estado],
            ["Criterios", auditoria.criterios or "N/A"],
        ]
        
        t = Table(data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        flowables.append(t)
        flowables.append(Spacer(1, 0.25 * inch))

        # Hallazgos
        flowables.append(Paragraph("Hallazgos", styles['Heading2']))
        
        if auditoria.hallazgos:
            hallazgos_data = [["Descripción", "Tipo", "Gravedad"]]
            for h in auditoria.hallazgos:
                hallazgos_data.append([
                    Paragraph(h.descripcion, normal_style), # Wrap text
                    h.tipo_hallazgo,
                    h.gravedad or "-"
                ])
            
            h_table = Table(hallazgos_data, colWidths=[4*inch, 1.5*inch, 1*inch])
            h_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            flowables.append(h_table)
        else:
            flowables.append(Paragraph("No se registraron hallazgos.", normal_style))

        doc.build(flowables)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_noconformidades_report(ncs: List[NoConformidad]) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        flowables = []
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']

        # Header
        flowables.extend(PDFService.create_header_flowables(
            "Reporte de No Conformidades",
            f"Generado: {datetime.now().strftime('%Y-%m-%d')}"
        ))

        # Table
        data = [["Código", "Descripción", "Estado", "Responsable"]]
        for nc in ncs:
            resp = nc.responsable.nombre_completo if nc.responsable else "Sin asignar"
            # Truncate description or wrap
            desc = Paragraph(nc.descripcion[:200] + ("..." if len(nc.descripcion) > 200 else ""), normal_style)
            
            data.append([
                nc.codigo or "N/A",
                desc,
                nc.estado,
                resp
            ])

        t = Table(data, colWidths=[1*inch, 3.5*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        flowables.append(t)
        doc.build(flowables)
        buffer.seek(0)
        return buffer
