from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

class PDFGenerator:
    @staticmethod
    def generar_informe_auditoria(auditoria_data: dict, hallazgos: list):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1E3A8A'),
            alignment=1 # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#2563EB')
        )

        normal_style = styles['Normal']

        # 1. Encabezado
        story.append(Paragraph(f"Informe de Auditoría: {auditoria_data.get('codigo', 'N/A')}", title_style))
        story.append(Paragraph(f"<b>Fecha de Generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
        story.append(Spacer(1, 20))

        # 2. Información General
        story.append(Paragraph("Información General", heading_style))
        
        data_general = [
            ["Nombre:", auditoria_data.get('nombre', '')],
            ["Tipo:", auditoria_data.get('tipo', '').upper()],
            ["Estado:", auditoria_data.get('estado', '').replace('_', ' ').title()],
            ["Auditor Líder:", auditoria_data.get('auditor_lider', 'N/A')],
            ["Fecha Inicio:", auditoria_data.get('fecha_inicio', 'N/A')],
            ["Fecha Fin:", auditoria_data.get('fecha_fin', 'N/A')],
        ]
        
        t_general = Table(data_general, colWidths=[2*inch, 4*inch])
        t_general.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1E3A8A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(t_general)
        story.append(Spacer(1, 20))

        # 3. Alcance y Objetivos
        story.append(Paragraph("Alcance y Objetivos", heading_style))
        story.append(Paragraph("<b>Alcance:</b>", styles['Heading4']))
        story.append(Paragraph(auditoria_data.get('alcance', 'No definido'), normal_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>Objetivo:</b>", styles['Heading4']))
        story.append(Paragraph(auditoria_data.get('objetivo', 'No definido'), normal_style))
        story.append(Spacer(1, 20))

        # 4. Resumen de Hallazgos
        story.append(Paragraph("Hallazgos Detectados", heading_style))
        
        if not hallazgos:
            story.append(Paragraph("No se registraron hallazgos en esta auditoría.", normal_style))
        else:
            # Cabecera tabla hallazgos
            data_hallazgos = [["Código", "Tipo", "Descripción", "Estado", "Gravedad"]]
            
            for h in hallazgos:
                descripcion_corta = (h.get('descripcion')[:50] + '...') if len(h.get('descripcion', '')) > 50 else h.get('descripcion', '')
                data_hallazgos.append([
                    h.get('codigo', 'N/A'),
                    h.get('tipo', '').title(),
                    descripcion_corta,
                    h.get('estado', '').title(),
                    h.get('gravedad', 'N/A').title()
                ])

            t_hallazgos = Table(data_hallazgos, colWidths=[1*inch, 1*inch, 2.5*inch, 1*inch, 1*inch])
            t_hallazgos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F1F5F9')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t_hallazgos)

        # 5. Conclusiones (Espacio para firma)
        story.append(Spacer(1, 40))
        story.append(Paragraph("Conclusiones y Cierre", heading_style))
        story.append(Paragraph("_____________________________________________", normal_style))
        story.append(Paragraph(f"Firma Auditor Líder: {auditoria_data.get('auditor_lider', '')}", normal_style))

        doc.build(story)
        buffer.seek(0)
        return buffer
