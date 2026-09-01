"""Pruebas de cálculo de nivel de riesgo."""
import pytest

from app.services.riesgo_service import RiesgoService


@pytest.mark.parametrize(
    "probabilidad,impacto,esperado",
    [
        (1, 1, "bajo"),
        (2, 2, "bajo"),
        (3, 2, "medio"),
        (3, 4, "alto"),
        (4, 5, "critico"),
        (5, 5, "critico"),
    ],
)
def test_calcular_nivel_riesgo(probabilidad, impacto, esperado):
    assert RiesgoService.calcular_nivel(probabilidad, impacto) == esperado


def test_umbral_accion():
    assert RiesgoService.UMBRAL_ACCION == 12
    assert 3 * 4 >= RiesgoService.UMBRAL_ACCION
    assert 2 * 5 < RiesgoService.UMBRAL_ACCION
