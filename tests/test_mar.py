"""Pruebas de la lectura de Niño 1+2 (NOAA) e ICEN (IGP) en src/temperatura_mar.py. No usan internet."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from temperatura_mar import a_mensual, parsear_icen, parsear_noaa_semanal  # noqa: E402

# Formato del archivo semanal de la NOAA: la primera pareja (SST, anomalía) es Niño 1+2.
# Cuando la anomalía es negativa, las columnas vienen pegadas ("20.6-0.1").
NOAA = """\
 Weekly SST data starts week centered on 3Sep1981
 Week          Nino1+2      Nino3        Nino34       Nino4
 02SEP1981     20.6-0.1     24.2 0.1     26.9 0.3     28.7 0.4
 09SEP1981     20.1-0.6     24.4 0.3     27.0 0.5     28.6 0.4
 16SEP1981     21.0 0.3     24.1-0.2     26.8 0.2     28.7 0.5
"""

ICEN = """\
ICEN: Indice Costero El Nino
YEAR MONTH ICEN
1950 1 -0.75
1950 2 -1.07
2026 8 3.98
"""


def test_noaa_lee_las_tres_semanas_e_ignora_los_encabezados():
    df = parsear_noaa_semanal(NOAA)
    assert len(df) == 3
    assert list(df.columns) == ["semana", "sst_nino12", "anomalia_nino12"]
    assert df["semana"].iloc[0] == pd.Timestamp("1981-09-02")


def test_noaa_separa_columnas_pegadas():
    df = parsear_noaa_semanal(NOAA)
    assert df["sst_nino12"].iloc[0] == 20.6
    assert df["anomalia_nino12"].iloc[0] == -0.1          # venía pegada: "20.6-0.1"
    assert df["anomalia_nino12"].iloc[1] == -0.6


def test_noaa_lee_anomalias_positivas_con_espacio():
    df = parsear_noaa_semanal(NOAA)
    assert df["anomalia_nino12"].iloc[2] == 0.3


def test_noaa_usa_solo_la_region_nino12():
    df = parsear_noaa_semanal(NOAA)
    assert df["sst_nino12"].tolist() == [20.6, 20.1, 21.0]  # no se mezclan Niño 3, 3.4 ni 4


def test_icen_lee_anio_mes_y_valor_e_ignora_encabezados():
    df = parsear_icen(ICEN)
    assert len(df) == 3
    assert str(df["fecha"].iloc[0]) == "1950-01"
    assert df["icen"].tolist() == [-0.75, -1.07, 3.98]


def test_icen_con_texto_sin_datos_devuelve_tabla_vacia():
    assert parsear_icen("sin datos\nnada que leer\n").empty


def test_mensual_promedia_las_semanas_de_cada_mes():
    sem = pd.DataFrame({"semana": pd.to_datetime(["2026-01-07", "2026-01-14", "2026-02-04"]),
                        "sst_nino12": [25.0, 25.0, 26.0], "anomalia_nino12": [1.0, 3.0, 2.0]})
    m = a_mensual(sem)
    assert m["anomalia_nino12"].tolist() == [2.0, 2.0]    # enero = (1 + 3) / 2


def test_mensual_calcula_el_cambio_a_tres_meses():
    meses = pd.date_range("2026-01-01", periods=5, freq="MS")
    sem = pd.DataFrame({"semana": meses, "sst_nino12": 25.0, "anomalia_nino12": [0.0, 1.0, 2.0, 4.0, 7.0]})
    m = a_mensual(sem)
    assert m["cambio_3m"].isna().sum() == 3
    assert m["cambio_3m"].iloc[3] == pytest.approx(4.0)   # abril - enero
    assert m["cambio_3m"].iloc[4] == pytest.approx(6.0)   # mayo - febrero
