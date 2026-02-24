from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.capacitacion import Capacitacion, AsistenciaCapacitacion
from ..models.competencia import BrechaCompetencia, EvaluacionCompetencia
from .competency_risk_automation_service import CompetencyRiskAutomationService
from ..utils.audit import registrar_auditoria


class CapacitacionService:
    ESTADOS_BRECHA_ABIERTA = ("abierta", "pendiente", "en_capacitacion")

    def __init__(self, db: Session):
        self.db = db

    def cerrar_capacitacion(self, capacitacion_id: UUID, usuario_id: UUID) -> Capacitacion:
        cap = self.db.query(Capacitacion).filter(Capacitacion.id == capacitacion_id).first()
        if not cap:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capacitación no encontrada")

        if cap.estado == "cerrada":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La capacitación ya está cerrada")

        asistencias_aprobadas = self.db.query(AsistenciaCapacitacion).filter(
            AsistenciaCapacitacion.capacitacion_id == capacitacion_id,
            AsistenciaCapacitacion.asistio.is_(True),
            AsistenciaCapacitacion.evaluacion_aprobada.is_(True),
        ).all()

        ahora = datetime.now(timezone.utc)
        for asistencia in asistencias_aprobadas:
            brechas = self.db.query(BrechaCompetencia).filter(
                BrechaCompetencia.usuario_id == asistencia.usuario_id,
                BrechaCompetencia.capacitacion_id == capacitacion_id,
                BrechaCompetencia.estado.in_(self.ESTADOS_BRECHA_ABIERTA),
            ).all()

            for brecha in brechas:
                # Generar evidencia de cierre en evaluación de competencia.
                self.db.add(
                    EvaluacionCompetencia(
                        usuario_id=asistencia.usuario_id,
                        competencia_id=brecha.competencia_id,
                        nivel=brecha.nivel_requerido,
                        estado="desarrollada",
                        fecha_evaluacion=ahora,
                        evaluador_id=usuario_id,
                        observaciones=f"Actualizada por cierre de capacitación {cap.codigo}",
                    )
                )
                brecha.nivel_actual = brecha.nivel_requerido
                brecha.estado = "cerrada"
                brecha.fecha_resolucion = ahora

        cap.estado = "cerrada"
        cap.fecha_fin = cap.fecha_fin or ahora
        registrar_auditoria(
            self.db,
            tabla="capacitaciones",
            registro_id=cap.id,
            accion="CERRAR",
            usuario_id=usuario_id,
            cambios={"estado": "cerrada"},
        )
        automation = CompetencyRiskAutomationService(self.db)
        for asistencia in asistencias_aprobadas:
            for brecha in self.db.query(BrechaCompetencia).filter(
                BrechaCompetencia.usuario_id == asistencia.usuario_id,
                BrechaCompetencia.capacitacion_id == capacitacion_id,
            ).all():
                automation.reevaluar_usuario_por_competencia(asistencia.usuario_id, brecha.competencia_id)
        self.db.commit()
        self.db.refresh(cap)
        return cap
