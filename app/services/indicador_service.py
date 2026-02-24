from sqlalchemy.orm import Session
from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException, status

from ..models.calidad import Indicador, MedicionIndicador
from ..utils.audit import registrar_auditoria


class IndicadorService:
    def __init__(self, db: Session):
        self.db = db

    def registrar_medicion(self, indicador_id: UUID, data: dict, usuario_id: UUID) -> MedicionIndicador:
        indicador = self.db.query(Indicador).filter(Indicador.id == indicador_id).first()
        if not indicador:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicador no encontrado")

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
        return self.db.query(MedicionIndicador).filter(
            MedicionIndicador.indicador_id == indicador_id
        ).order_by(MedicionIndicador.periodo.asc()).all()

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
