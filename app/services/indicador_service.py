from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException, status

from ..models.calidad import Indicador, MedicionIndicador
from ..utils.audit import registrar_auditoria


TIPOS_INDICADOR = {"eficacia", "eficiencia", "cumplimiento"}
ESTADOS_INDICADOR = {"borrador", "pendiente_aprobacion", "aprobado", "rechazado"}


def _ahora():
    return datetime.now(timezone.utc)


class IndicadorService:
    def __init__(self, db: Session):
        self.db = db

    def _query(self):
        return self.db.query(Indicador).options(
            joinedload(Indicador.proceso),
            joinedload(Indicador.responsable_medicion),
            joinedload(Indicador.creador),
            joinedload(Indicador.revisador),
            joinedload(Indicador.aprobador),
            joinedload(Indicador.mediciones).joinedload(MedicionIndicador.registrador),
        )

    def obtener(self, indicador_id: UUID) -> Indicador:
        indicador = self._query().filter(Indicador.id == indicador_id).unique().first()
        if not indicador:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicador no encontrado")
        return indicador

    def listar(self, proceso_id: UUID = None, activo: bool = None, tipo_indicador: str = None, skip: int = 0, limit: int = 200):
        query = self._query()
        if proceso_id:
            query = query.filter(Indicador.proceso_id == proceso_id)
        if activo is not None:
            query = query.filter(Indicador.activo == activo)
        if tipo_indicador:
            tipo = tipo_indicador.strip().lower()
            if tipo not in TIPOS_INDICADOR:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tipo inválido. Use: {', '.join(sorted(TIPOS_INDICADOR))}",
                )
            query = query.filter(Indicador.tipo_indicador == tipo)
        return query.order_by(Indicador.codigo.asc()).offset(skip).limit(limit).unique().all()

    def registrar_medicion(self, indicador_id: UUID, data: dict, usuario_id: UUID) -> MedicionIndicador:
        indicador = self.obtener(indicador_id)

        meta = data.get("meta")
        if meta is None:
            meta = indicador.meta

        cumple_meta = None
        if meta is not None:
            cumple_meta = Decimal(str(data["valor"])) >= Decimal(str(meta))

        medicion = MedicionIndicador(
            indicador_id=indicador_id,
            periodo=data["periodo"],
            valor=data["valor"],
            meta=meta,
            cumple_meta=cumple_meta,
            observaciones=data.get("observaciones"),
            registrado_por=usuario_id,
            creado_por=usuario_id,
        )
        self.db.add(medicion)

        indicador.revisado_por = usuario_id
        indicador.fecha_revision = _ahora()
        if indicador.estado == "aprobado":
            indicador.estado = "pendiente_aprobacion"
        elif indicador.estado == "rechazado":
            indicador.estado = "borrador"

        self.db.flush()

        registrar_auditoria(
            self.db,
            tabla="mediciones_indicador",
            registro_id=medicion.id,
            accion="CREATE",
            usuario_id=usuario_id,
            cambios={"indicador_id": str(indicador_id), **data, "cumple_meta": cumple_meta},
        )
        self.db.commit()
        self.db.refresh(medicion)
        return medicion

    def historial(self, indicador_id: UUID):
        self.obtener(indicador_id)
        return self.db.query(MedicionIndicador).options(
            joinedload(MedicionIndicador.registrador),
        ).filter(
            MedicionIndicador.indicador_id == indicador_id
        ).order_by(MedicionIndicador.periodo.asc(), MedicionIndicador.creado_en.asc()).all()

    def tendencia(self, indicador_id: UUID) -> dict:
        mediciones = self.historial(indicador_id)
        if not mediciones:
            return {
                "indicador_id": indicador_id,
                "total_mediciones": 0,
                "promedio": Decimal("0"),
                "ultimo_valor": None,
                "ultimo_periodo": None,
                "tendencia": "sin_datos",
            }

        valores = [Decimal(str(m.valor)) for m in mediciones]
        promedio = sum(valores) / Decimal(len(valores))

        tendencia = "estable"
        if len(valores) >= 2:
            if valores[-1] > valores[-2]:
                tendencia = "subiendo"
            elif valores[-1] < valores[-2]:
                tendencia = "bajando"

        ultima = mediciones[-1]
        return {
            "indicador_id": indicador_id,
            "total_mediciones": len(mediciones),
            "promedio": promedio.quantize(Decimal("0.01")),
            "ultimo_valor": Decimal(str(ultima.valor)),
            "ultimo_periodo": ultima.periodo,
            "tendencia": tendencia,
        }

    def solicitar_aprobacion(self, indicador_id: UUID, usuario_id: UUID) -> Indicador:
        indicador = self.obtener(indicador_id)
        if indicador.estado == "aprobado":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El indicador ya está aprobado")
        if not indicador.mediciones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registre al menos una medición antes de solicitar aprobación",
            )
        indicador.estado = "pendiente_aprobacion"
        indicador.revisado_por = usuario_id
        indicador.fecha_revision = _ahora()
        registrar_auditoria(
            self.db,
            tabla="indicadores",
            registro_id=indicador.id,
            accion="UPDATE",
            usuario_id=usuario_id,
            cambios={"estado": "pendiente_aprobacion"},
        )
        self.db.commit()
        return self.obtener(indicador_id)

    def aprobar(self, indicador_id: UUID, usuario_id: UUID, observacion: str | None = None) -> Indicador:
        indicador = self.obtener(indicador_id)
        if indicador.estado not in {"borrador", "pendiente_aprobacion", "rechazado"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El indicador no está pendiente de aprobación")
        if indicador.creado_por and str(indicador.creado_por) == str(usuario_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Quien elabora el indicador no puede aprobarlo. Debe aprobarlo otra persona.",
            )
        if not indicador.mediciones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede aprobar un indicador sin mediciones",
            )
        indicador.estado = "aprobado"
        indicador.aprobado_por = usuario_id
        indicador.fecha_aprobacion = _ahora()
        indicador.observacion_aprobacion = observacion
        if not indicador.revisado_por:
            indicador.revisado_por = indicador.responsable_medicion_id or usuario_id
            indicador.fecha_revision = indicador.fecha_revision or _ahora()
        registrar_auditoria(
            self.db,
            tabla="indicadores",
            registro_id=indicador.id,
            accion="UPDATE",
            usuario_id=usuario_id,
            cambios={"estado": "aprobado", "aprobado_por": str(usuario_id)},
        )
        self.db.commit()
        return self.obtener(indicador_id)

    def rechazar(self, indicador_id: UUID, usuario_id: UUID, observacion: str | None = None) -> Indicador:
        indicador = self.obtener(indicador_id)
        if indicador.estado not in {"borrador", "pendiente_aprobacion"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El indicador no está pendiente de aprobación")
        if indicador.creado_por and str(indicador.creado_por) == str(usuario_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Quien elabora el indicador no puede rechazarlo. Debe decidirlo otra persona.",
            )
        if not observacion or not observacion.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Indique el motivo del rechazo")
        indicador.estado = "rechazado"
        indicador.aprobado_por = None
        indicador.fecha_aprobacion = None
        indicador.observacion_aprobacion = observacion.strip()
        registrar_auditoria(
            self.db,
            tabla="indicadores",
            registro_id=indicador.id,
            accion="UPDATE",
            usuario_id=usuario_id,
            cambios={"estado": "rechazado", "observacion": observacion.strip()},
        )
        self.db.commit()
        return self.obtener(indicador_id)
