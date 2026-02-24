from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ..models.competencia import BrechaCompetencia, EvaluacionCompetencia
from ..models.proceso import (
    AccionProceso,
    EtapaCompetencia,
    EtapaProceso,
    InstanciaProceso,
    ParticipanteProceso,
    ResponsableProceso,
)
from ..models.riesgo import Riesgo, RiesgoCompetenciaCritica
from ..models.sistema import Notificacion


class CompetencyRiskAutomationService:
    NIVELES_ORDEN = {"basico": 1, "intermedio": 2, "avanzado": 3}
    ESTADOS_BRECHA_ABIERTA = ("abierta", "pendiente", "en_capacitacion")
    UMBRAL_CRITICO_SCORE = 15

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _normalizar_nivel(nivel: str | None) -> str | None:
        return nivel.strip().lower() if nivel else None

    def _nivel_usuario(self, usuario_id: UUID, competencia_id: UUID) -> str | None:
        evaluacion = (
            self.db.query(EvaluacionCompetencia)
            .filter(
                EvaluacionCompetencia.usuario_id == usuario_id,
                EvaluacionCompetencia.competencia_id == competencia_id,
                EvaluacionCompetencia.activo.is_(True),
            )
            .order_by(EvaluacionCompetencia.fecha_evaluacion.desc(), EvaluacionCompetencia.creado_en.desc())
            .first()
        )
        return self._normalizar_nivel(evaluacion.nivel) if evaluacion else None

    @staticmethod
    def _score_riesgo(riesgo: Riesgo) -> int:
        if riesgo.probabilidad and riesgo.impacto:
            return int(riesgo.probabilidad) * int(riesgo.impacto)
        return 0

    def _es_riesgo_critico(self, riesgo: Riesgo) -> bool:
        return self._score_riesgo(riesgo) >= self.UMBRAL_CRITICO_SCORE

    def _cerrar_brechas_activas(
        self,
        usuario_id: UUID,
        competencia_id: UUID,
        etapa_id: UUID | None = None,
        riesgo_id: UUID | None = None,
        nivel_actual: str | None = None,
    ) -> None:
        query = self.db.query(BrechaCompetencia).filter(
            BrechaCompetencia.usuario_id == usuario_id,
            BrechaCompetencia.competencia_id == competencia_id,
            BrechaCompetencia.estado.in_(self.ESTADOS_BRECHA_ABIERTA),
        )
        if etapa_id:
            query = query.filter(BrechaCompetencia.etapa_id == etapa_id)
        if riesgo_id:
            query = query.filter(BrechaCompetencia.riesgo_id == riesgo_id)

        ahora = datetime.now(timezone.utc)
        for brecha in query.all():
            brecha.estado = "cerrada"
            if nivel_actual:
                brecha.nivel_actual = nivel_actual
            brecha.fecha_resolucion = ahora

    def _upsert_brecha(
        self,
        usuario_id: UUID,
        competencia_id: UUID,
        nivel_requerido: str,
        nivel_actual: str,
        etapa_id: UUID | None = None,
        riesgo_id: UUID | None = None,
        nivel_riesgo: str | None = None,
    ) -> BrechaCompetencia:
        brecha = (
            self.db.query(BrechaCompetencia)
            .filter(
                BrechaCompetencia.usuario_id == usuario_id,
                BrechaCompetencia.competencia_id == competencia_id,
                BrechaCompetencia.etapa_id == etapa_id,
                BrechaCompetencia.riesgo_id == riesgo_id,
                BrechaCompetencia.estado.in_(self.ESTADOS_BRECHA_ABIERTA),
            )
            .first()
        )
        if brecha:
            brecha.nivel_actual = nivel_actual
            brecha.nivel_requerido = nivel_requerido
            brecha.nivel_riesgo = nivel_riesgo
            brecha.estado = "abierta"
            return brecha

        brecha = BrechaCompetencia(
            usuario_id=usuario_id,
            competencia_id=competencia_id,
            etapa_id=etapa_id,
            riesgo_id=riesgo_id,
            nivel_requerido=nivel_requerido,
            nivel_actual=nivel_actual,
            nivel_riesgo=nivel_riesgo,
            estado="abierta",
        )
        self.db.add(brecha)
        return brecha

    def _notificar_brecha(self, usuario_id: UUID, competencia_id: UUID, riesgo_id: UUID | None) -> None:
        msg = f"Brecha detectada en competencia {competencia_id}."
        if riesgo_id:
            msg += f" Impacta riesgo crítico {riesgo_id}."
        self.db.add(
            Notificacion(
                usuario_id=usuario_id,
                titulo="Brecha de competencia detectada",
                mensaje=msg,
                tipo="warning",
                referencia_tipo="brecha_competencia",
                referencia_id=competencia_id,
            )
        )

    def _generar_accion_preventiva(self, riesgo: Riesgo) -> None:
        origen = f"brecha_competencia_critica:{riesgo.id}"
        existente = (
            self.db.query(AccionProceso)
            .filter(
                AccionProceso.proceso_id == riesgo.proceso_id,
                AccionProceso.origen == origen,
                AccionProceso.estado.in_(["planificada", "en_proceso", "iniciado"]),
                AccionProceso.activo.is_(True),
            )
            .first()
        )
        if existente:
            return

        codigo_base = f"AP-{riesgo.codigo}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        codigo = codigo_base[:100]
        while self.db.query(AccionProceso).filter(AccionProceso.codigo == codigo).first():
            codigo = f"{codigo_base[:92]}-{str(uuid4())[:7]}"

        accion = AccionProceso(
            proceso_id=riesgo.proceso_id,
            codigo=codigo,
            nombre=f"Acción preventiva por brecha de competencia ({riesgo.codigo})",
            descripcion="Acción automática generada por riesgo crítico y brecha de competencia.",
            tipo_accion="preventiva",
            origen=origen,
            responsable_id=riesgo.responsable_id,
            fecha_planificada=datetime.now(timezone.utc),
            estado="planificada",
        )
        self.db.add(accion)

    def _actualizar_residual_por_brechas(self, riesgo: Riesgo, hay_brecha_critica: bool) -> None:
        score_base = self._score_riesgo(riesgo)
        if score_base <= 0:
            riesgo.nivel_residual = None
            return
        riesgo.nivel_residual = score_base + 3 if hay_brecha_critica else score_base

    def _usuarios_asignados_a_proceso(self, proceso_id: UUID) -> list[UUID]:
        usuarios_responsables = (
            self.db.query(ResponsableProceso.usuario_id)
            .filter(
                ResponsableProceso.proceso_id == proceso_id,
                ResponsableProceso.activo.is_(True),
                (ResponsableProceso.vigente_hasta.is_(None))
                | (ResponsableProceso.vigente_hasta > datetime.utcnow()),
            )
            .distinct()
            .all()
        )
        usuarios_participantes = (
            self.db.query(ParticipanteProceso.usuario_id)
            .join(
                InstanciaProceso,
                InstanciaProceso.id == ParticipanteProceso.instancia_proceso_id,
            )
            .filter(
                ParticipanteProceso.activo.is_(True),
                InstanciaProceso.proceso_id == proceso_id,
                InstanciaProceso.activo.is_(True),
            )
            .distinct()
            .all()
        )
        ids = {u[0] for u in usuarios_responsables} | {u[0] for u in usuarios_participantes}
        return list(ids)

    def _evaluar_requisito(
        self,
        usuario_id: UUID,
        competencia_id: UUID,
        nivel_requerido: str,
        etapa_id: UUID | None = None,
        riesgo: Riesgo | None = None,
    ) -> bool:
        nivel_actual = self._nivel_usuario(usuario_id, competencia_id)
        nivel_req_norm = self._normalizar_nivel(nivel_requerido)
        nivel_actual_norm = self._normalizar_nivel(nivel_actual)
        riesgo_id = riesgo.id if riesgo else None
        nivel_riesgo = riesgo.nivel_riesgo if riesgo else None

        cumple = (
            nivel_req_norm in self.NIVELES_ORDEN
            and nivel_actual_norm in self.NIVELES_ORDEN
            and self.NIVELES_ORDEN[nivel_actual_norm] >= self.NIVELES_ORDEN[nivel_req_norm]
        )
        if cumple:
            self._cerrar_brechas_activas(
                usuario_id=usuario_id,
                competencia_id=competencia_id,
                etapa_id=etapa_id,
                riesgo_id=riesgo_id,
                nivel_actual=nivel_actual or "sin_evaluacion",
            )
            return False

        self._upsert_brecha(
            usuario_id=usuario_id,
            competencia_id=competencia_id,
            etapa_id=etapa_id,
            riesgo_id=riesgo_id,
            nivel_requerido=nivel_requerido,
            nivel_actual=nivel_actual or "sin_evaluacion",
            nivel_riesgo=nivel_riesgo,
        )
        self._notificar_brecha(usuario_id, competencia_id, riesgo_id)
        return True

    def evaluar_usuario_en_proceso(self, usuario_id: UUID, proceso_id: UUID) -> None:
        etapas = (
            self.db.query(EtapaProceso)
            .filter(
                EtapaProceso.proceso_id == proceso_id,
                EtapaProceso.activa.is_(True),
                EtapaProceso.activo.is_(True),
            )
            .all()
        )
        for etapa in etapas:
            self.evaluar_usuario_en_etapa(usuario_id, etapa.id)

    def evaluar_usuario_en_etapa(self, usuario_id: UUID, etapa_id: UUID) -> bool:
        requisitos = (
            self.db.query(EtapaCompetencia)
            .filter(
                EtapaCompetencia.etapa_id == etapa_id,
                EtapaCompetencia.activo.is_(True),
            )
            .all()
        )
        if not requisitos:
            return False

        riesgos_criticos = (
            self.db.query(Riesgo)
            .filter(
                Riesgo.etapa_proceso_id == etapa_id,
                Riesgo.activo.is_(True),
            )
            .all()
        )
        riesgos_criticos = [r for r in riesgos_criticos if self._es_riesgo_critico(r)]
        hay_brecha = False
        for req in requisitos:
            hay_brecha = self._evaluar_requisito(
                usuario_id=usuario_id,
                competencia_id=req.competencia_id,
                nivel_requerido=req.nivel_requerido,
                etapa_id=etapa_id,
            ) or hay_brecha

            for riesgo in riesgos_criticos:
                crit = (
                    self.db.query(RiesgoCompetenciaCritica)
                    .filter(
                        RiesgoCompetenciaCritica.riesgo_id == riesgo.id,
                        RiesgoCompetenciaCritica.competencia_id == req.competencia_id,
                        RiesgoCompetenciaCritica.activo.is_(True),
                    )
                    .first()
                )
                if not crit:
                    continue
                brecha_riesgo = self._evaluar_requisito(
                    usuario_id=usuario_id,
                    competencia_id=req.competencia_id,
                    nivel_requerido=crit.nivel_minimo,
                    etapa_id=etapa_id,
                    riesgo=riesgo,
                )
                hay_brecha = hay_brecha or brecha_riesgo

        return hay_brecha

    def reevaluar_riesgo_critico(self, riesgo_id: UUID) -> bool:
        riesgo = self.db.query(Riesgo).filter(Riesgo.id == riesgo_id, Riesgo.activo.is_(True)).first()
        if not riesgo:
            return False

        if not self._es_riesgo_critico(riesgo):
            self._actualizar_residual_por_brechas(riesgo, hay_brecha_critica=False)
            return False

        competencias_criticas = (
            self.db.query(RiesgoCompetenciaCritica)
            .filter(
                RiesgoCompetenciaCritica.riesgo_id == riesgo.id,
                RiesgoCompetenciaCritica.activo.is_(True),
            )
            .all()
        )
        if not competencias_criticas:
            self._actualizar_residual_por_brechas(riesgo, hay_brecha_critica=False)
            return False

        usuarios = self._usuarios_asignados_a_proceso(riesgo.proceso_id)
        hay_brecha_critica = False
        for usuario_id in usuarios:
            for comp_crit in competencias_criticas:
                brecha = self._evaluar_requisito(
                    usuario_id=usuario_id,
                    competencia_id=comp_crit.competencia_id,
                    nivel_requerido=comp_crit.nivel_minimo,
                    etapa_id=riesgo.etapa_proceso_id,
                    riesgo=riesgo,
                )
                hay_brecha_critica = hay_brecha_critica or brecha

        self._actualizar_residual_por_brechas(riesgo, hay_brecha_critica=hay_brecha_critica)
        if hay_brecha_critica:
            self._generar_accion_preventiva(riesgo)
        return hay_brecha_critica

    def reevaluar_usuario_por_competencia(self, usuario_id: UUID, competencia_id: UUID) -> None:
        requisitos_etapa = (
            self.db.query(EtapaCompetencia)
            .join(EtapaProceso, EtapaProceso.id == EtapaCompetencia.etapa_id)
            .join(ResponsableProceso, ResponsableProceso.proceso_id == EtapaProceso.proceso_id)
            .filter(
                EtapaCompetencia.competencia_id == competencia_id,
                ResponsableProceso.usuario_id == usuario_id,
                ResponsableProceso.activo.is_(True),
                EtapaCompetencia.activo.is_(True),
                EtapaProceso.activo.is_(True),
            )
            .distinct()
            .all()
        )

        for req in requisitos_etapa:
            self.evaluar_usuario_en_etapa(usuario_id, req.etapa_id)

        riesgos = (
            self.db.query(Riesgo)
            .join(RiesgoCompetenciaCritica, RiesgoCompetenciaCritica.riesgo_id == Riesgo.id)
            .filter(
                RiesgoCompetenciaCritica.competencia_id == competencia_id,
                RiesgoCompetenciaCritica.activo.is_(True),
                Riesgo.activo.is_(True),
            )
            .all()
        )
        for riesgo in riesgos:
            self.reevaluar_riesgo_critico(riesgo.id)
