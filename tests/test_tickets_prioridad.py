"""Pruebas de inferencia automática de prioridad de tickets."""
from app.api.tickets import _inferir_prioridad


def test_prioridad_por_categoria():
    assert _inferir_prioridad("soporte", "Ayuda", "Necesito apoyo") == "alta"
    assert _inferir_prioridad("consulta", "Duda", "Cómo se usa") == "baja"
    assert _inferir_prioridad("mejora", "Nueva idea", "Agregar filtro") == "media"
    assert _inferir_prioridad("solicitud_documento", "POE", "Solicito procedimiento") == "media"


def test_prioridad_critica_por_palabras():
    assert _inferir_prioridad("consulta", "Sistema caido", "No entra nadie") == "critica"
    assert _inferir_prioridad("mejora", "Urgente", "Producción bloqueada") == "critica"


def test_prioridad_alta_por_error():
    assert _inferir_prioridad("consulta", "Error al guardar", "Falla el botón") == "alta"


def test_prioridad_categoria_desconocida():
    assert _inferir_prioridad("otra", "Solicitud", "Texto normal") == "media"
