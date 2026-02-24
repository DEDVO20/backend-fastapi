from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from ..models.auditoria import HallazgoAuditoria
from ..models.proceso import Proceso, EtapaProceso
from ..models.riesgo import Riesgo
from ..models.usuario import Usuario
from ..repositories.proceso import ProcesoRepository, EtapaProcesoRepository
from ..schemas.proceso import ProcesoCreate, ProcesoUpdate, EtapaProcesoCreate, EtapaProcesoUpdate
from ..utils.audit import registrar_auditoria


class ProcesoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProcesoRepository(db)
        self.etapa_repo = EtapaProcesoRepository(db)

    def _validar_usuario_activo(self, usuario_id: UUID, campo: str = "responsable") -> Usuario:
        usuario = self.db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El {campo} especificado no existe")
        if not usuario.activo:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El {campo} especificado está inactivo")
        return usuario

    def listar(self, skip: int = 0, limit: int = 100, estado: str | None = None, area_id: UUID | None = None):
        query = self.db.query(Proceso).options(
            joinedload(Proceso.area),
            joinedload(Proceso.responsable)
        )
        if hasattr(Proceso, "activo"):
            query = query.filter(Proceso.activo.is_(True))
        if estado:
            query = query.filter(Proceso.estado == estado)
        if area_id:
            query = query.filter(Proceso.area_id == area_id)
        return query.offset(skip).limit(limit).all()

    def obtener(self, proceso_id: UUID) -> Proceso:
        query = self.db.query(Proceso).options(
            joinedload(Proceso.area),
            joinedload(Proceso.responsable)
        )
        if hasattr(Proceso, "activo"):
            query = query.filter(Proceso.activo.is_(True))
        proceso = query.filter(Proceso.id == proceso_id).first()
        if not proceso:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proceso no encontrado")
        return proceso

    def crear_proceso(self, data: ProcesoCreate, usuario_id: UUID) -> Proceso:
        existente = self.db.query(Proceso).filter(Proceso.codigo == data.codigo).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código de proceso ya existe")

        if data.responsable_id:
            self._validar_usuario_activo(data.responsable_id, "responsable")

        proceso = self.repo.create(data.model_dump(), creado_por=usuario_id)
        registrar_auditoria(
            self.db,
            tabla="procesos",
            registro_id=proceso.id,
            accion="CREATE",
            usuario_id=usuario_id,
            cambios=data.model_dump(),
        )
        self.db.commit()
        self.db.refresh(proceso)
        return proceso

    def actualizar_proceso(self, proceso_id: UUID, data: ProcesoUpdate, usuario_id: UUID) -> Proceso:
        proceso = self.repo.get_by_id(proceso_id)
        if not proceso:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proceso no encontrado")

        if data.codigo and data.codigo != proceso.codigo:
            duplicado = self.db.query(Proceso).filter(Proceso.codigo == data.codigo).first()
            if duplicado:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código de proceso ya existe")

        update_data = data.model_dump(exclude_unset=True)
        if "responsable_id" in update_data and update_data["responsable_id"]:
            self._validar_usuario_activo(update_data["responsable_id"], "responsable")

        self.repo.update(proceso_id, update_data)
        registrar_auditoria(
            self.db,
            tabla="procesos",
            registro_id=proceso_id,
            accion="UPDATE",
            usuario_id=usuario_id,
            cambios=update_data,
        )
        self.db.commit()
        self.db.refresh(proceso)
        return proceso

    def eliminar_proceso(self, proceso_id: UUID, usuario_id: UUID) -> None:
        proceso = self.repo.soft_delete(proceso_id)
        if not proceso:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proceso no encontrado")

        registrar_auditoria(
            self.db,
            tabla="procesos",
            registro_id=proceso_id,
            accion="DELETE",
            usuario_id=usuario_id,
            cambios=None,
        )
        self.db.commit()

    def crear_etapa(self, data: EtapaProcesoCreate, usuario_id: UUID) -> EtapaProceso:
        proceso = self.repo.get_by_id(data.proceso_id)
        if not proceso:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El proceso especificado no existe o está inactivo")

        orden_duplicado = self.db.query(EtapaProceso).filter(
            EtapaProceso.proceso_id == data.proceso_id,
            EtapaProceso.orden == data.orden,
        ).first()
        if orden_duplicado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una etapa con ese orden en el proceso")

        if data.responsable_id:
            self._validar_usuario_activo(data.responsable_id, "responsable de etapa")

        etapa = self.etapa_repo.create(data.model_dump(), creado_por=usuario_id)
        registrar_auditoria(
            self.db,
            tabla="etapa_procesos",
            registro_id=etapa.id,
            accion="CREATE",
            usuario_id=usuario_id,
            cambios=data.model_dump(),
        )
        self.db.commit()
        self.db.refresh(etapa)
        return etapa

    def actualizar_etapa(self, etapa_id: UUID, data: EtapaProcesoUpdate, usuario_id: UUID) -> EtapaProceso:
        etapa = self.etapa_repo.get_by_id(etapa_id)
        if not etapa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etapa no encontrada")

        update_data = data.model_dump(exclude_unset=True)
        nuevo_orden = update_data.get("orden")
        if nuevo_orden is not None and nuevo_orden != etapa.orden:
            orden_duplicado = self.db.query(EtapaProceso).filter(
                EtapaProceso.proceso_id == etapa.proceso_id,
                EtapaProceso.orden == nuevo_orden,
                EtapaProceso.id != etapa_id,
            ).first()
            if orden_duplicado:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una etapa con ese orden en el proceso")

        if "responsable_id" in update_data and update_data["responsable_id"]:
            self._validar_usuario_activo(update_data["responsable_id"], "responsable de etapa")

        self.etapa_repo.update(etapa_id, update_data)
        registrar_auditoria(
            self.db,
            tabla="etapa_procesos",
            registro_id=etapa_id,
            accion="UPDATE",
            usuario_id=usuario_id,
            cambios=update_data,
        )
        self.db.commit()
        self.db.refresh(etapa)
        return etapa

    def eliminar_etapa(self, etapa_id: UUID, usuario_id: UUID) -> None:
        etapa = self.etapa_repo.get_by_id(etapa_id)
        if not etapa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etapa no encontrada")

        riesgos_activos = self.db.query(Riesgo).filter(
            Riesgo.etapa_proceso_id == etapa_id,
            Riesgo.estado == "activo",
        ).count()
        if riesgos_activos > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar: tiene {riesgos_activos} riesgos activos",
            )

        hallazgos_abiertos = self.db.query(HallazgoAuditoria).filter(
            HallazgoAuditoria.etapa_proceso_id == etapa_id,
            HallazgoAuditoria.estado == "abierto",
        ).count()
        if hallazgos_abiertos > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar: tiene {hallazgos_abiertos} hallazgos abiertos",
            )

        self.etapa_repo.soft_delete(etapa_id)
        registrar_auditoria(
            self.db,
            tabla="etapa_procesos",
            registro_id=etapa_id,
            accion="DELETE",
            usuario_id=usuario_id,
            cambios=None,
        )
        self.db.commit()
