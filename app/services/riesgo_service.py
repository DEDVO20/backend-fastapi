from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.riesgo import Riesgo, ControlRiesgo, EvaluacionRiesgoHistorial
from ..repositories.riesgo import RiesgoRepository
from ..schemas.riesgo import RiesgoCreate, RiesgoUpdate, ControlRiesgoCreate, ControlRiesgoUpdate
from ..utils.audit import registrar_auditoria


class RiesgoService:
    UMBRAL_ACCION = 12

    def __init__(self, db: Session):
        self.db = db
        self.repo = RiesgoRepository(db)

    @staticmethod
    def calcular_nivel(probabilidad: int, impacto: int) -> str:
        score = probabilidad * impacto
        if score >= 20:
            return "critico"
        if score >= 12:
            return "alto"
        if score >= 6:
            return "medio"
        return "bajo"

    def listar(self, skip: int = 0, limit: int = 100, proceso_id: UUID | None = None, estado: str | None = None, nivel_riesgo: str | None = None):
        query = self.db.query(Riesgo)
        if hasattr(Riesgo, "activo"):
            query = query.filter(Riesgo.activo.is_(True))
        if proceso_id:
            query = query.filter(Riesgo.proceso_id == proceso_id)
        if estado:
            query = query.filter(Riesgo.estado == estado)
        if nivel_riesgo:
            query = query.filter(Riesgo.nivel_riesgo == nivel_riesgo)
        return query.offset(skip).limit(limit).all()

    def obtener(self, riesgo_id: UUID) -> Riesgo:
        riesgo = self.repo.get_by_id(riesgo_id)
        if not riesgo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riesgo no encontrado")
        return riesgo

    def crear(self, data: RiesgoCreate, usuario_id: UUID) -> Riesgo:
        existente = self.db.query(Riesgo).filter(Riesgo.codigo == data.codigo).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código de riesgo ya existe")

        payload = data.model_dump()
        if payload.get("probabilidad") and payload.get("impacto"):
            payload["nivel_riesgo"] = self.calcular_nivel(payload["probabilidad"], payload["impacto"])

        riesgo = self.repo.create(payload, creado_por=usuario_id)

        if riesgo.probabilidad and riesgo.impacto:
            self.db.add(
                EvaluacionRiesgoHistorial(
                    riesgo_id=riesgo.id,
                    probabilidad_nueva=riesgo.probabilidad,
                    impacto_nueva=riesgo.impacto,
                    nivel_nuevo=riesgo.nivel_riesgo or self.calcular_nivel(riesgo.probabilidad, riesgo.impacto),
                    evaluado_por=usuario_id,
                )
            )

        registrar_auditoria(
            self.db,
            tabla="riesgos",
            registro_id=riesgo.id,
            accion="CREATE",
            usuario_id=usuario_id,
            cambios=payload,
        )
        self.db.commit()
        self.db.refresh(riesgo)
        return riesgo

    def actualizar(self, riesgo_id: UUID, data: RiesgoUpdate, usuario_id: UUID) -> Riesgo:
        riesgo = self.repo.get_by_id(riesgo_id)
        if not riesgo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riesgo no encontrado")

        update_data = data.model_dump(exclude_unset=True)
        prob_anterior = riesgo.probabilidad
        imp_anterior = riesgo.impacto
        nivel_anterior = riesgo.nivel_riesgo

        nueva_prob = update_data.get("probabilidad", riesgo.probabilidad)
        nuevo_imp = update_data.get("impacto", riesgo.impacto)
        if nueva_prob and nuevo_imp:
            update_data["nivel_riesgo"] = self.calcular_nivel(nueva_prob, nuevo_imp)

        if update_data.get("estado") == "cerrado":
            controles = self.db.query(ControlRiesgo).filter(
                ControlRiesgo.riesgo_id == riesgo_id,
                ControlRiesgo.activo.is_(True),
            ).count()
            if controles == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede cerrar un riesgo sin control asociado")

        self.repo.update(riesgo_id, update_data)

        if (
            nueva_prob is not None
            and nuevo_imp is not None
            and (nueva_prob != prob_anterior or nuevo_imp != imp_anterior)
        ):
            self.db.add(
                EvaluacionRiesgoHistorial(
                    riesgo_id=riesgo_id,
                    probabilidad_anterior=prob_anterior,
                    impacto_anterior=imp_anterior,
                    nivel_anterior=nivel_anterior,
                    probabilidad_nueva=nueva_prob,
                    impacto_nueva=nuevo_imp,
                    nivel_nuevo=update_data.get("nivel_riesgo") or riesgo.nivel_riesgo or self.calcular_nivel(nueva_prob, nuevo_imp),
                    evaluado_por=usuario_id,
                    justificacion="Actualización de evaluación de riesgo",
                )
            )

        registrar_auditoria(
            self.db,
            tabla="riesgos",
            registro_id=riesgo_id,
            accion="UPDATE",
            usuario_id=usuario_id,
            cambios=update_data,
        )
        self.db.commit()
        self.db.refresh(riesgo)
        return riesgo

    def eliminar(self, riesgo_id: UUID, usuario_id: UUID) -> None:
        riesgo = self.repo.soft_delete(riesgo_id)
        if not riesgo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riesgo no encontrado")
        registrar_auditoria(
            self.db,
            tabla="riesgos",
            registro_id=riesgo_id,
            accion="DELETE",
            usuario_id=usuario_id,
            cambios=None,
        )
        self.db.commit()

    def listar_controles(self, skip: int = 0, limit: int = 100, activo: bool | None = None, tipo_control: str | None = None):
        query = self.db.query(ControlRiesgo)
        if activo is not None:
            query = query.filter(ControlRiesgo.activo == activo)
        if tipo_control:
            query = query.filter(ControlRiesgo.tipo_control == tipo_control)
        return query.offset(skip).limit(limit).all()

    def listar_controles_riesgo(self, riesgo_id: UUID):
        return self.db.query(ControlRiesgo).filter(ControlRiesgo.riesgo_id == riesgo_id).all()

    def obtener_control(self, control_id: UUID) -> ControlRiesgo:
        control = self.db.query(ControlRiesgo).filter(ControlRiesgo.id == control_id).first()
        if not control:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control de riesgo no encontrado")
        return control

    def crear_control(self, data: ControlRiesgoCreate, usuario_id: UUID) -> ControlRiesgo:
        control = ControlRiesgo(**data.model_dump())
        if hasattr(control, "creado_por"):
            control.creado_por = usuario_id
        self.db.add(control)
        self.db.flush()
        registrar_auditoria(
            self.db,
            tabla="control_riesgos",
            registro_id=control.id,
            accion="CREATE",
            usuario_id=usuario_id,
            cambios=data.model_dump(),
        )
        self.db.commit()
        self.db.refresh(control)
        return control

    def actualizar_control(self, control_id: UUID, data: ControlRiesgoUpdate, usuario_id: UUID) -> ControlRiesgo:
        control = self.obtener_control(control_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(control, key, value)
        registrar_auditoria(
            self.db,
            tabla="control_riesgos",
            registro_id=control_id,
            accion="UPDATE",
            usuario_id=usuario_id,
            cambios=update_data,
        )
        self.db.commit()
        self.db.refresh(control)
        return control

    def eliminar_control(self, control_id: UUID, usuario_id: UUID) -> None:
        control = self.obtener_control(control_id)
        if hasattr(control, "activo"):
            control.activo = False
        else:
            self.db.delete(control)
        registrar_auditoria(
            self.db,
            tabla="control_riesgos",
            registro_id=control_id,
            accion="DELETE",
            usuario_id=usuario_id,
            cambios=None,
        )
        self.db.commit()
