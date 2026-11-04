"""Pruebas del índice de riesgo por lluvia intensa (src/clima_nino.py). No usan internet."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from clima_nino import indice_riesgo, nivel  # noqa: E402

# Un punto de ejemplo: p99 de 20 mm y 30 mm de lluvia normal en 15 días.
CLIM = {"p99": 20.0, "acum15_dia_del_anio": {"100": 30.0}}
SECO = [0.0] * 15
SIN_PRON = [0.0] * 5


def calcular(obs, pron, clim=CLIM):
    return indice_riesgo(obs, pron, clim, 100)


def test_sin_lluvia_el_indice_es_cero():
    r = calcular(SECO, SIN_PRON)
    assert r["indice"] == 0
    assert r["nivel"] == "Bajo"


def test_lluvia_extrema_observada_y_prevista_da_100():
    obs = [0.0] * 12 + [25.0, 25.0, 25.0]          # >= p99 los últimos 3 días, acumulado 75 >= 2 x normal
    pron = [25.0, 25.0, 25.0, 0.0, 0.0]
    r = calcular(obs, pron)
    assert r["indice"] == 100
    assert r["nivel"] == "Muy alto"


def test_los_pesos_suman_100():
    # Con las tres señales al máximo el índice es exactamente 100: pesos 0,40 + 0,35 + 0,25 = 1.
    r = calcular([60.0] * 15, [60.0] * 5)
    assert r["reciente"] == r["pronostico"] == r["saturacion"] == 1.0
    assert r["indice"] == 100


def test_la_lluvia_prevista_sola_pesa_35_por_ciento():
    r = calcular(SECO, [20.0, 0.0, 0.0, 0.0, 0.0])      # pronóstico = p99, sin lluvia observada
    assert r["indice"] == pytest.approx(35.0)
    assert r["nivel"] == "Moderado"


def test_la_lluvia_reciente_sola_pesa_40_por_ciento():
    obs = [0.0] * 14 + [20.0]                           # intensidad = p99; el acumulado (20 mm) sube la saturación
    r = calcular(obs, SIN_PRON)
    assert r["reciente"] == 1.0
    assert r["indice"] >= 40


def test_el_indice_no_baja_cuando_llueve_mas():
    previo = -1.0
    for mm in [0, 2, 5, 10, 20, 40]:
        r = calcular([0.0] * 14 + [float(mm)], [float(mm), 0, 0, 0, 0])
        assert r["indice"] >= previo
        previo = r["indice"]


def test_una_llovizna_en_el_desierto_no_activa_la_alerta():
    # Punto muy seco: p99 de 1 mm y casi nada de lluvia normal. Con el piso de 5 mm, 3 mm no es extremo.
    desierto = {"p99": 1.0, "acum15_dia_del_anio": {"100": 0.2}}
    r = calcular([0.0] * 14 + [3.0], [3.0, 0, 0, 0, 0], desierto)
    assert r["reciente"] == pytest.approx(0.6)          # 3 / 5, no 3 / 1
    assert r["nivel"] != "Muy alto"


def test_el_acumulado_normal_se_busca_por_dia_del_anio():
    sin_dato = {"p99": 20.0, "acum15_dia_del_anio": {}}
    r = calcular(SECO, SIN_PRON, sin_dato)               # sin dato de ese día, no debe fallar
    assert r["normal15"] == 0.0


@pytest.mark.parametrize("valor, esperado", [
    (0, "Bajo"), (24.9, "Bajo"), (25, "Moderado"), (49.9, "Moderado"),
    (50, "Alto"), (74.9, "Alto"), (75, "Muy alto"), (100, "Muy alto"),
])
def test_los_niveles_respetan_los_cortes(valor, esperado):
    assert nivel(valor) == esperado
