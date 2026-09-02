from app.utils.codigos import (
    prefijo_documento,
    prefijo_proceso,
    resolver_prefijo,
    siguiente_desde_existentes,
)


def test_siguiente_desde_existentes_incrementa():
    assert siguiente_desde_existentes(["FO-GC-001", "FO-GC-003"], "FO-GC-") == "FO-GC-004"


def test_siguiente_desde_existentes_vacio():
    assert siguiente_desde_existentes([], "R-") == "R-001"


def test_prefijo_documento_formato():
    assert prefijo_documento("formato") == "FO-GC-"
    assert prefijo_documento("procedimiento") == "PR-GC-"


def test_prefijo_proceso_incluye_area():
    assert prefijo_proceso("estrategico", "DIR") == "PE-DIR-"
    assert prefijo_proceso("operativo", None) == "PO-SGC-"


def test_resolver_prefijo_documento_y_riesgo():
    assert resolver_prefijo("documento", tipo="formato") == "FO-GC-"
    assert resolver_prefijo("riesgo") == "R-"
