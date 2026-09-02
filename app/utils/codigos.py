"""Generación secuencial de códigos institucionales del SGC."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

PREFIJOS_DOCUMENTO = {
    "formato": "FO-GC-",
    "procedimiento": "PR-GC-",
    "instructivo": "IN-GC-",
    "manual": "MN-GC-",
    "politica": "PO-GC-",
    "registro": "RG-GC-",
    "plan": "PL-GC-",
    "proceso": "CH-GC-",
}

PREFIJOS_PROCESO = {
    "estrategico": "PE",
    "operativo": "PO",
    "apoyo": "PA",
    "medicion": "PM",
}

PREFIJOS_INDICADOR = {
    "eficacia": "IND-EFC-",
    "eficiencia": "IND-EFI-",
    "cumplimiento": "IND-CUM-",
}


def _normalizar_segmento(valor: Optional[str], fallback: str) -> str:
    texto = re.sub(r"[^A-Za-z0-9]", "", (valor or "").strip().upper())
    return (texto[:8] or fallback)


def prefijo_documento(tipo: Optional[str] = None) -> str:
    return PREFIJOS_DOCUMENTO.get((tipo or "formato").strip().lower(), "FO-GC-")


def prefijo_proceso(tipo: Optional[str] = None, area_codigo: Optional[str] = None) -> str:
    tipo_prefijo = PREFIJOS_PROCESO.get((tipo or "operativo").strip().lower(), "PR")
    return f"{tipo_prefijo}-{_normalizar_segmento(area_codigo, 'SGC')}-"


def prefijo_indicador(tipo: Optional[str] = None) -> str:
    return PREFIJOS_INDICADOR.get((tipo or "eficacia").strip().lower(), "IND-EFC-")


def prefijo_anual(base: str) -> str:
    return f"{base}-{datetime.now().year}-"


def resolver_prefijo(
    entidad: str,
    tipo: Optional[str] = None,
    area_codigo: Optional[str] = None,
) -> str:
    clave = (entidad or "").strip().lower()
    if clave == "documento":
        return prefijo_documento(tipo)
    if clave == "riesgo":
        return "R-"
    if clave == "proceso":
        return prefijo_proceso(tipo, area_codigo)
    if clave in ("no_conformidad", "noconformidad"):
        return prefijo_anual("NC")
    if clave in ("accion_correctiva", "accioncorrectiva"):
        return prefijo_anual("AC")
    if clave == "capacitacion":
        return prefijo_anual("CAP")
    if clave == "objetivo":
        return prefijo_anual("OBJ")
    if clave == "indicador":
        return prefijo_indicador(tipo)
    if clave == "auditoria":
        return prefijo_anual("AUD")
    if clave == "hallazgo":
        return prefijo_anual("HALL")
    if clave == "area":
        return "AREA-"
    if clave in ("formulario", "formulario_dinamico"):
        return "FD-"
    if clave == "accion_proceso":
        return prefijo_anual("AP")
    raise ValueError(f"Entidad no soportada para código automático: {entidad}")


def siguiente_desde_existentes(codigos: list[str], prefix: str, digits: int = 3) -> str:
    patron = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
    maximo = 0
    for valor in codigos:
        if not valor:
            continue
        coincidencia = patron.match(str(valor).strip())
        if coincidencia:
            maximo = max(maximo, int(coincidencia.group(1)))
    return f"{prefix}{str(maximo + 1).zfill(digits)}"


def siguiente_codigo(db: Session, model, prefix: str, campo: str = "codigo", digits: int = 3) -> str:
    columna = getattr(model, campo)
    filas = (
        db.query(columna)
        .filter(func.lower(columna).like(f"{prefix.lower()}%"))
        .all()
    )
    existentes = [fila[0] for fila in filas if fila and fila[0]]
    return siguiente_desde_existentes(existentes, prefix, digits)


def asignar_codigo(
    db: Session,
    model,
    codigo: Optional[str],
    prefix: str,
    campo: str = "codigo",
    digits: int = 3,
) -> str:
    valor = (codigo or "").strip().upper()
    if valor:
        existente = db.query(model).filter(getattr(model, campo) == valor).first()
        if not existente:
            return valor
    return siguiente_codigo(db, model, prefix, campo=campo, digits=digits)
