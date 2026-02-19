from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.competencia import Competencia, EvaluacionCompetencia, BrechaCompetencia
from ..models.sistema import Notificacion
from ..models.usuario import Usuario
from ..utils.audit import registrar_auditoria


class CompetenciaService:
    NIVELES_ORDEN = {"basico": 1, "intermedio": 2, "avanzado": 3}

    def __init__(self, db: Session):
        self.db = db

    def _normalizar_nivel(self, nivel: str | None) -> str | None:
        return nivel.strip().lower() if nivel else None

    def _obtener_nivel_requerido(self, usuario_id: UUID, competencia_id: UUID, nivel_requerido_input: str | None) -> str | None:
        if nivel_requerido_input:
            return self._normalizar_nivel(nivel_requerido_input)

        brecha = self.db.query(BrechaCompetencia).filter(
            BrechaCompetencia.usuario_id == usuario_id,
            BrechaCompetencia.competencia_id == competencia_id,
            BrechaCompetencia.estado.in_(["pendiente", "en_capacitacion"]),
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
                BrechaCompetencia.estado.in_(["pendiente", "en_capacitacion"]),
            ).first()
            if brecha:
                brecha.nivel_actual = evaluacion.nivel
                brecha.nivel_requerido = nivel_requerido
                brecha.estado = "pendiente"
            else:
                self.db.add(
                    BrechaCompetencia(
                        usuario_id=evaluacion.usuario_id,
                        competencia_id=evaluacion.competencia_id,
                        nivel_requerido=nivel_requerido,
                        nivel_actual=evaluacion.nivel,
                        estado="pendiente",
                    )
                )
            self._generar_alerta_capacitacion(evaluacion.usuario_id, evaluacion.competencia_id)
        else:
            brechas = self.db.query(BrechaCompetencia).filter(
                BrechaCompetencia.usuario_id == evaluacion.usuario_id,
                BrechaCompetencia.competencia_id == evaluacion.competencia_id,
                BrechaCompetencia.estado.in_(["pendiente", "en_capacitacion"]),
            ).all()
            for brecha in brechas:
                brecha.estado = "resuelta"
                brecha.nivel_actual = evaluacion.nivel
                brecha.fecha_resolucion = datetime.now(timezone.utc)

        registrar_auditoria(
            self.db,
            tabla="evaluaciones_competencia",
            registro_id=evaluacion.id,
            accion="CREATE",
            usuario_id=usuario_id,
            cambios=evaluacion_data,
        )

        self.db.commit()
        self.db.refresh(evaluacion)
        return evaluacion
