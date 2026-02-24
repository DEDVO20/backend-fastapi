from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status
from typing import List, Optional

from ...models.auditoria import Auditoria, HallazgoAuditoria, ProgramaAuditoria
from ...models.calidad import NoConformidad, AccionCorrectiva
from ...models.historial import HistorialEstado
from ...models.sistema import CampoFormulario, RespuestaFormulario
from ...models.usuario import Usuario

class AuditoriaService:

    @staticmethod
    def iniciar_auditoria(db: Session, auditoria_id: UUID, usuario_id: UUID) -> Auditoria:
        auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
        if not auditoria:
            raise HTTPException(status_code=404, detail="Auditoría no encontrada")
            
        if auditoria.estado != 'planificada':
            raise HTTPException(status_code=400, detail=f"No se puede iniciar una auditoría en estado {auditoria.estado}")
            
        if not auditoria.auditor_lider_id:
            raise HTTPException(status_code=400, detail="Debe asignar un Auditor Líder antes de iniciar")
            
        # Actualizar estado
        estado_anterior = auditoria.estado
        auditoria.estado = 'en_curso'
        auditoria.fecha_inicio = datetime.now()

        # Primera auditoría iniciada del programa -> programa en ejecución
        if auditoria.programa_id:
            programa = db.query(ProgramaAuditoria).filter(ProgramaAuditoria.id == auditoria.programa_id).first()
            if programa and programa.estado == 'aprobado':
                programa.estado = 'en_ejecucion'
        
        # Registrar historial
        historial = HistorialEstado(
            entidad_tipo='auditoria',
            entidad_id=auditoria.id,
            estado_anterior=estado_anterior,
            estado_nuevo='en_curso',
            usuario_id=usuario_id,
            comentario="Inicio de ejecución de auditoría"
        )
        db.add(historial)
        db.commit()
        db.refresh(auditoria)
        return auditoria

    @staticmethod
    def finalizar_auditoria(db: Session, auditoria_id: UUID, usuario_id: UUID) -> Auditoria:
        auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
        if not auditoria:
            raise HTTPException(status_code=404, detail="Auditoría no encontrada")
            
        if auditoria.estado != 'en_curso':
            raise HTTPException(status_code=400, detail="Solo se pueden finalizar auditorías en curso")
            
        # Validar hallazgos
        hallazgos_count = db.query(HallazgoAuditoria).filter(HallazgoAuditoria.auditoria_id == auditoria.id).count()
        if hallazgos_count == 0:
            # Podría ser una advertencia, pero ISO suele requerir evidencia de conformidad también
            pass 
            
        estado_anterior = auditoria.estado
        auditoria.estado = 'completada'
        auditoria.fecha_fin = datetime.now()
        
        # Generar informe preliminar si está vacío
        if not auditoria.informe_final:
            auditoria.informe_final = f"Auditoría finalizada el {datetime.now().strftime('%Y-%m-%d')}. Total hallazgos: {hallazgos_count}."
        
        historial = HistorialEstado(
            entidad_tipo='auditoria',
            entidad_id=auditoria.id,
            estado_anterior=estado_anterior,
            estado_nuevo='completada',
            usuario_id=usuario_id,
            comentario="Finalización de auditoría"
        )
        db.add(historial)
        db.commit()
        db.refresh(auditoria)
        return auditoria

    @staticmethod
    def cerrar_auditoria(db: Session, auditoria_id: UUID, usuario_id: UUID) -> Auditoria:
        auditoria = db.query(Auditoria).filter(Auditoria.id == auditoria_id).first()
        if not auditoria:
             raise HTTPException(status_code=404, detail="Auditoría no encontrada")

        if not auditoria.informe_final:
            raise HTTPException(status_code=400, detail="Debe adjuntar el informe final antes de cerrar")

        # Validación ISO de checklist aplicado
        if not auditoria.formulario_checklist_id or not auditoria.formulario_checklist_version:
            raise HTTPException(
                status_code=400,
                detail="La auditoría debe tener un checklist de formulario versionado aplicado.",
            )

        campos = db.query(CampoFormulario).filter(
            CampoFormulario.formulario_id == auditoria.formulario_checklist_id,
            CampoFormulario.activo.is_(True),
        ).all()
        respuestas = db.query(RespuestaFormulario).filter(
            RespuestaFormulario.auditoria_id == auditoria_id,
        ).all()
        respuestas_por_campo = {r.campo_formulario_id: r for r in respuestas}

        faltantes = []
        faltantes_conclusion = False
        faltantes_evidencia = []
        for campo in campos:
            respuesta = respuestas_por_campo.get(campo.id)
            valor = (respuesta.valor or "").strip() if respuesta else ""
            evidencia = (respuesta.archivo_adjunto or "").strip() if respuesta else ""

            if campo.requerido and not valor:
                faltantes.append(campo.etiqueta)
            if campo.nombre and campo.nombre.strip().lower() == "conclusion_auditoria" and not valor:
                faltantes_conclusion = True
            if campo.evidencia_requerida and not evidencia:
                faltantes_evidencia.append(campo.etiqueta)

        if faltantes:
            raise HTTPException(
                status_code=400,
                detail=f"No puede cerrar: hay campos obligatorios vacíos ({len(faltantes)}).",
            )
        if faltantes_conclusion:
            raise HTTPException(
                status_code=400,
                detail="No puede cerrar: falta la conclusión de auditoría.",
            )
        if faltantes_evidencia:
            raise HTTPException(
                status_code=400,
                detail=f"No puede cerrar: hay campos que exigen evidencia adjunta ({len(faltantes_evidencia)}).",
            )
             
        # Verificar que no haya hallazgos abiertos (especialmente No Conformidades sin cerrar)
        hallazgos_abiertos = db.query(HallazgoAuditoria).filter(
            HallazgoAuditoria.auditoria_id == auditoria_id,
            HallazgoAuditoria.estado != 'cerrado'
        ).count()
        
        if hallazgos_abiertos > 0:
            raise HTTPException(status_code=400, detail="No se puede cerrar la auditoría con hallazgos abiertos")

        # Validar que no existan No Conformidades abiertas asociadas
        nc_abiertas = db.query(NoConformidad).join(
            HallazgoAuditoria, HallazgoAuditoria.no_conformidad_id == NoConformidad.id
        ).filter(
            HallazgoAuditoria.auditoria_id == auditoria_id,
            NoConformidad.estado != 'cerrada'
        ).count()
        if nc_abiertas > 0:
            raise HTTPException(status_code=400, detail="No se puede cerrar la auditoría con No Conformidades abiertas")

        # Hallazgos con NC deben tener al menos una acción correctiva asociada
        hallazgos_con_nc = db.query(HallazgoAuditoria).filter(
            HallazgoAuditoria.auditoria_id == auditoria_id,
            HallazgoAuditoria.no_conformidad_id.isnot(None),
        ).all()
        for h in hallazgos_con_nc:
            acciones = db.query(AccionCorrectiva).filter(
                AccionCorrectiva.no_conformidad_id == h.no_conformidad_id,
            ).count()
            if acciones == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No puede cerrar: el hallazgo {h.codigo} no tiene acción correctiva registrada.",
                )

        estado_anterior = auditoria.estado
        auditoria.estado = 'cerrada'
        if not auditoria.fecha_fin:
            auditoria.fecha_fin = datetime.now()
        
        historial = HistorialEstado(
            entidad_tipo='auditoria',
            entidad_id=auditoria.id,
            estado_anterior=estado_anterior,
            estado_nuevo='cerrada',
            usuario_id=usuario_id,
            comentario="Cierre formal de auditoría"
        )
        db.add(historial)
        db.commit()
        db.refresh(auditoria)
        return auditoria
