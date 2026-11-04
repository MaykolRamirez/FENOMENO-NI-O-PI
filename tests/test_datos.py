"""Pruebas de los datos que lee el tablero (dashboard/data). Corren después de clima_nino.py e imagenes_satelite.py."""
import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "dashboard" / "data"

CLAVES_PUNTO = {"punto", "departamento", "region", "lat", "lon", "altitud_m", "fechas", "lluvia_mm",
                "pronostico_fechas", "pronostico_mm", "acum15_mm", "normal15_mm", "anomalia_pct", "max_dia_mm",
                "p99_mm", "indice", "nivel", "reciente", "pronostico", "saturacion"}
NIVELES = {"Bajo", "Moderado", "Alto", "Muy alto"}


def leer(nombre):
    ruta = DATA / nombre
    if not ruta.exists():
        pytest.skip(f"{nombre} aún no se ha generado")
    return json.loads(ruta.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def puntos():
    return leer("lluvia.json")


def test_hay_26_puntos_con_todas_las_claves(puntos):
    assert len(puntos) == 26
    for p in puntos:
        assert CLAVES_PUNTO <= p.keys(), f"{p.get('punto')}: faltan {CLAVES_PUNTO - p.keys()}"


def test_cada_punto_tiene_15_dias_observados_y_5_de_pronostico(puntos):
    for p in puntos:
        assert len(p["fechas"]) == len(p["lluvia_mm"]) == 15, p["punto"]
        assert len(p["pronostico_fechas"]) == len(p["pronostico_mm"]) == 5, p["punto"]


def test_los_valores_son_coherentes(puntos):
    for p in puntos:
        assert all(x >= 0 for x in p["lluvia_mm"] + p["pronostico_mm"]), p["punto"]
        assert p["acum15_mm"] == pytest.approx(sum(p["lluvia_mm"]), abs=0.2), p["punto"]
        assert 0 <= p["indice"] <= 100 and p["nivel"] in NIVELES, p["punto"]
        assert p["max_dia_mm"] == max(p["lluvia_mm"]), p["punto"]


def test_los_puntos_estan_dentro_del_peru(puntos):
    for p in puntos:
        assert -19 < p["lat"] < 0 and -82 < p["lon"] < -68, p["punto"]


def test_cada_departamento_de_los_puntos_existe_en_el_mapa(puntos):
    geo = leer("departamentos.geojson")
    nombres = {f["properties"]["NOMBDEP"] for f in geo["features"]}
    assert {p["departamento"] for p in puntos} <= nombres


def test_mar_tiene_las_series_que_dibuja_el_tablero():
    m = leer("mar.json")
    n = m["nino12"]
    assert len(n["semanas"]) == len(n["anomalia"]) == len(n["sst"]) > 50
    assert {"semana", "anomalia", "sst"} <= m["ultimo"].keys()
    assert len(m["icen"]["meses"]) == len(m["icen"]["valor"]) == 24
    assert {"1982-83", "1997-98", "2017", "2023"} <= m["episodios_max"].keys()
    assert len(m["puertos"]) >= 1
    for q in m["puertos"]:
        assert len(q["fechas"]) == len(q["sst"]) > 7 and 10 < q["actual"] < 35, q["puerto"]


def test_resumen_tiene_corte_y_titular():
    r = leer("resumen.json")
    assert r["corte"] and r["titular"]
    assert set(r["niveles"]) == NIVELES


def test_satelite_lista_seis_zonas_y_sus_imagenes_existen():
    meta = leer("sat/satelite.json")
    assert len(meta["zonas"]) == 6
    for z in meta["zonas"]:
        assert {"antes", "ahora"} <= z["escenas"].keys(), z["id"]
        for etapa in ("antes", "ahora"):
            assert 0 <= z["escenas"][etapa]["nubes"] <= 100
            for vista in ("rgb", "ndvi", "agua"):
                img = DATA / "sat" / f"{z['id']}_{etapa}_{vista}.jpg"
                assert img.exists() and img.stat().st_size > 10_000, img.name
