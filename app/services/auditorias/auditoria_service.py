from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status
from typing import List, Optional

from ...models.auditoria import Auditoria, HallazgoAuditoria, ProgramaAuditoria
from ...models.calidad import NoConformidad
from ...models.historial import HistorialEstado
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
