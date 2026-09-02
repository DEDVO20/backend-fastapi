"""Endpoint para previsualizar el siguiente código institucional."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..api.dependencies import get_current_user
from ..models.usuario import Usuario, Area
from ..models.documento import Documento
from ..models.riesgo import Riesgo
from ..models.proceso import Proceso, AccionProceso
from ..models.calidad import NoConformidad, AccionCorrectiva, ObjetivoCalidad, Indicador
from ..models.capacitacion import Capacitacion
from ..models.auditoria import Auditoria, HallazgoAuditoria
from ..models.sistema import FormularioDinamico
from ..utils.codigos import resolver_prefijo, siguiente_codigo

router = APIRouter(prefix="/api/v1", tags=["codigos"])

MODELOS = {
    "documento": Documento,
    "riesgo": Riesgo,
    "proceso": Proceso,
    "no_conformidad": NoConformidad,
    "noconformidad": NoConformidad,
    "accion_correctiva": AccionCorrectiva,
    "accioncorrectiva": AccionCorrectiva,
    "capacitacion": Capacitacion,
    "objetivo": ObjetivoCalidad,
    "indicador": Indicador,
    "auditoria": Auditoria,
    "hallazgo": HallazgoAuditoria,
    "area": Area,
    "formulario": FormularioDinamico,
    "formulario_dinamico": FormularioDinamico,
    "accion_proceso": AccionProceso,
}


@router.get("/codigos/siguiente")
def obtener_siguiente_codigo(
    entidad: str = Query(..., description="Tipo de registro (documento, riesgo, proceso, ...)"),
    tipo: str | None = Query(None, description="Tipo interno: formato, eficacia, estrategico, etc."),
    area_codigo: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    clave = entidad.strip().lower()
    modelo = MODELOS.get(clave)
    if not modelo:
        raise HTTPException(status_code=400, detail="Entidad no soportada para código automático")
    try:
        prefix = resolver_prefijo(clave, tipo=tipo, area_codigo=area_codigo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"codigo": siguiente_codigo(db, modelo, prefix)}
