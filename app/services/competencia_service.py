from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.competencia import Competencia, EvaluacionCompetencia, BrechaCompetencia
from ..models.sistema import Notificacion
from ..models.proceso import EtapaCompetencia, EtapaProceso, ResponsableProceso
from ..models.usuario import Usuario
from .competency_risk_automation_service import CompetencyRiskAutomationService
from ..utils.audit import registrar_auditoria


class CompetenciaService:
    NIVELES_ORDEN = {"basico": 1, "intermedio": 2, "avanzado": 3}
    ESTADOS_BRECHA_ABIERTA = ("abierta", "pendiente", "en_capacitacion")

    def __init__(self, db: Session):
        self.db = db

    def _normalizar_nivel(self, nivel: str | None) -> str | None:
        return nivel.strip().lower() if nivel else None

    def _obtener_nivel_requerido(self, usuario_id: UUID, competencia_id: UUID, nivel_requerido_input: str | None) -> str | None:
        if nivel_requerido_input:
            return self._normalizar_nivel(nivel_requerido_input)

        nivel_etapa = (
            self.db.query(EtapaCompetencia.nivel_requerido)
            .join(EtapaProceso, EtapaProceso.id == EtapaCompetencia.etapa_id)
            .join(ResponsableProceso, ResponsableProceso.proceso_id == EtapaProceso.proceso_id)
            .filter(
                ResponsableProceso.usuario_id == usuario_id,
                EtapaCompetencia.competencia_id == competencia_id,
                EtapaCompetencia.activo.is_(True),
                EtapaProceso.activo.is_(True),
                ResponsableProceso.activo.is_(True),
            )
            .order_by(EtapaProceso.orden.asc())
            .first()
        )
        if nivel_etapa:
            return self._normalizar_nivel(nivel_etapa[0])

        brecha = self.db.query(BrechaCompetencia).filter(
            BrechaCompetencia.usuario_id == usuario_id,
            BrechaCompetencia.competencia_id == competencia_id,
            BrechaCompetencia.estado.in_(self.ESTADOS_BRECHA_ABIERTA),
        ).order_by(BrechaCompetencia.creado_en.desc()).first()
        return self._normalizar_nivel(brecha.nivel_requerido) if brecha else None

    def _generar_alerta_capacitacion(self, usuario_id: UUID, competencia_id: UUID) -> None:
        self.db.add(
            Notificacion(
                usuario_id=usuario_id,
                titulo="Brecha de competencia detectada",
                mensaje=f"Se detectó una brecha en la competencia {competencia_id}. Se requiere plan de capacitación.",
                tipo="warning",
                referencia_tipo="brecha_competencia",
                referencia_id=competencia_id,
            )
        )

    def evaluar_competencia(self, evaluacion_data: dict, usuario_id: UUID) -> EvaluacionCompetencia:
        nivel_requerido_input = evaluacion_data.pop("nivel_requerido", None)
        usuario = self.db.query(Usuario).filter(Usuario.id == evaluacion_data["usuario_id"]).first()
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario not found")

        competencia = self.db.query(Competencia).filter(Competencia.id == evaluacion_data["competencia_id"]).first()
        if not competencia:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competencia not found")

        if not evaluacion_data.get("evaluador_id"):
            evaluacion_data["evaluador_id"] = usuario_id

        evaluacion = EvaluacionCompetencia(**evaluacion_data)
        self.db.add(evaluacion)
        self.db.flush()

        nivel_actual = self._normalizar_nivel(evaluacion.nivel)
        nivel_requerido = self._obtener_nivel_requerido(
            evaluacion.usuario_id,
            evaluacion.competencia_id,
            nivel_requerido_input,
        )

        if (
            nivel_requerido
            and nivel_actual in self.NIVELES_ORDEN
            and nivel_requerido in self.NIVELES_ORDEN
            and self.NIVELES_ORDEN[nivel_actual] < self.NIVELES_ORDEN[nivel_requerido]
        ):
            brecha = self.db.query(BrechaCompetencia).filter(
                BrechaCompetencia.usuario_id == evaluacion.usuario_id,
                BrechaCompetencia.competencia_id == evaluacion.competencia_id,
                BrechaCompetencia.estado.in_(self.ESTADOS_BRECHA_ABIERTA),
            ).first()
            if brecha:
                brecha.nivel_actual = evaluacion.nivel
                brecha.nivel_requerido = nivel_requerido
                brecha.estado = "abierta"
            else:
                self.db.add(
                    BrechaCompetencia(
                        usuario_id=evaluacion.usuario_id,
                        competencia_id=evaluacion.competencia_id,
                        nivel_requerido=nivel_requerido,
                        nivel_actual=evaluacion.nivel,
                        estado="abierta",
                    )
                )
            self._generar_alerta_capacitacion(evaluacion.usuario_id, evaluacion.competencia_id)
        else:
            brechas = self.db.query(BrechaCompetencia).filter(
                BrechaCompetencia.usuario_id == evaluacion.usuario_id,
                BrechaCompetencia.competencia_id == evaluacion.competencia_id,
                BrechaCompetencia.estado.in_(self.ESTADOS_BRECHA_ABIERTA),
            ).all()
            for brecha in brechas:
                brecha.estado = "cerrada"
                brecha.nivel_actual = evaluacion.nivel
                brecha.fecha_resolucion = evaluacion.fecha_evaluacion

        registrar_auditoria(
            self.db,
            tabla="evaluaciones_competencia",
            registro_id=evaluacion.id,
            accion="CREATE",
            usuario_id=usuario_id,
            cambios=evaluacion_data,
        )

        # Reglas automáticas certificables:
        # proceso -> etapa -> competencia -> brecha -> riesgo residual -> acción preventiva
        automation = CompetencyRiskAutomationService(self.db)
        automation.reevaluar_usuario_por_competencia(evaluacion.usuario_id, evaluacion.competencia_id)

        self.db.commit()
        self.db.refresh(evaluacion)
        return evaluacion
