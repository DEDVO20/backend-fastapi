from sqlalchemy.orm import Session
from datetime import date
from uuid import UUID
from fastapi import HTTPException, status

from ..models.calidad import AccionCorrectiva, NoConformidad
from ..utils.audit import registrar_auditoria


class CalidadService:
    def __init__(self, db: Session):
        self.db = db

    def cerrar_accion(self, accion_id: UUID, verificacion_data: dict, usuario_id: UUID) -> AccionCorrectiva:
        accion = self.db.query(AccionCorrectiva).filter(AccionCorrectiva.id == accion_id).first()
        if not accion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acción correctiva no encontrada")

        if not accion.analisis_causa_raiz:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe completar el análisis de causa")

        if not accion.evidencias:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe adjuntar evidencia de implementación")

        eficacia_val = verificacion_data.get("eficacia_verificada")
        eficaz_explicit = verificacion_data.get("eficaz")
        if eficaz_explicit is None:
            if eficacia_val is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar la verificación de eficacia")
            eficaz = eficacia_val >= 80
        else:
            eficaz = bool(eficaz_explicit)

        if verificacion_data.get("observaciones"):
            accion.observacion = verificacion_data["observaciones"]
        if eficacia_val is not None:
            accion.eficacia_verificada = eficacia_val

        if not eficaz:
            if accion.no_conformidad_id:
                nc = self.db.query(NoConformidad).filter(NoConformidad.id == accion.no_conformidad_id).first()
                if nc:
                    nc.estado = "abierta"
            accion.estado = "no_eficaz"
        else:
            accion.estado = "cerrada"
            if accion.no_conformidad_id:
                nc = self.db.query(NoConformidad).filter(NoConformidad.id == accion.no_conformidad_id).first()
                if nc:
                    nc.estado = "cerrada"

        accion.verificado_por = usuario_id
        accion.fecha_verificacion = date.today()

        registrar_auditoria(
            self.db,
            tabla="acciones_correctivas",
            registro_id=accion.id,
            accion="VERIFICAR",
            usuario_id=usuario_id,
            cambios={"estado": accion.estado, "eficacia_verificada": accion.eficacia_verificada},
        )
        self.db.commit()
        self.db.refresh(accion)
        return accion
