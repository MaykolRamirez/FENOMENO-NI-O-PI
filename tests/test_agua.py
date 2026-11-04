"""Pruebas de la detección de agua con radar (src/agua_radar.py). No usan internet."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from agua_radar import (PENDIENTE_MAX, UMBRAL_AGUA, UMBRAL_TIERRA, abrir, mascaras, pendiente_grados,  # noqa: E402
                        remuestrear, suavizar, una_por_pasada)

AGUA_JSON = RAIZ / "dashboard" / "data" / "agua" / "agua.json"
TIERRA, LAGO = -10.0, -22.0                      # dB típicos de suelo seco y de agua en calma


def plano(valor, n=20):
    return np.full((n, n), valor, dtype=float)


def test_suavizar_no_cambia_una_imagen_uniforme():
    assert np.allclose(suavizar(plano(-12.0)), -12.0)


def test_suavizar_reparte_un_pixel_aislado():
    a = plano(0.0, 9)
    a[4, 4] = 9.0
    s = suavizar(a)
    assert s[4, 4] == pytest.approx(1.0)             # 9 / 9
    assert s.sum() == pytest.approx(9.0)             # la energía se conserva


def test_abrir_quita_pixeles_aislados_y_conserva_los_bloques():
    m = np.zeros((10, 10), bool)
    m[2, 2] = True                                   # un píxel suelto: ruido
    m[5:8, 5:8] = True                               # un bloque de 3 x 3: agua
    r = abrir(m)
    assert not r[2, 2]
    assert r[5:8, 5:8].all() and r.sum() == 9


def test_agua_nueva_es_tierra_antes_y_agua_ahora():
    ahora, ref = plano(TIERRA), plano(TIERRA)
    ahora[5:12, 5:12] = LAGO                         # inundación de 7 x 7
    nueva, perm = mascaras(ahora, ref, plano(0.0))
    assert nueva[5:12, 5:12].all() and nueva.sum() == 49
    assert perm.sum() == 0


def test_agua_permanente_es_agua_antes_y_ahora():
    ahora, ref = plano(TIERRA), plano(TIERRA)
    ahora[2:9, 2:9] = LAGO
    ref[2:9, 2:9] = LAGO                             # un embalse que ya existía
    nueva, perm = mascaras(ahora, ref, plano(0.0))
    assert nueva.sum() == 0
    assert perm.sum() == 49


def test_las_pendientes_fuertes_se_descartan():
    ahora, ref = plano(TIERRA), plano(TIERRA)
    ahora[5:12, 5:12] = LAGO                         # sombra de relieve parecida al agua
    pend = plano(0.0)
    pend[5:12, 5:12] = PENDIENTE_MAX + 5
    nueva, perm = mascaras(ahora, ref, pend)
    assert nueva.sum() == 0 and perm.sum() == 0


def test_los_pixeles_sin_dato_no_son_agua():
    ahora, ref = plano(TIERRA), plano(TIERRA)
    ahora[:, :5] = -30.0                             # borde de la escena, relleno y no medición
    nueva, perm = mascaras(ahora, ref, plano(0.0))
    assert nueva.sum() == 0 and perm.sum() == 0


def test_sin_dato_en_la_referencia_tampoco_cuenta():
    ahora, ref = plano(LAGO), plano(TIERRA)
    ref[:, :5] = -30.0
    nueva, _ = mascaras(ahora, ref, plano(0.0))
    assert not nueva[:, :5].any()


def test_umbrales_coherentes():
    assert UMBRAL_AGUA < UMBRAL_TIERRA               # entre ambos hay una zona gris que no se clasifica


def test_pendiente_de_un_plano_inclinado():
    # Sube 1 m por cada 1 m horizontal: 45 grados.
    h = np.tile(np.arange(10, dtype=float), (10, 1))
    pend = pendiente_grados(h, ancho_m=10.0, alto_m=10.0)
    assert np.allclose(pend, 45.0, atol=1e-6)


def test_pendiente_de_un_terreno_llano_es_cero():
    assert np.allclose(pendiente_grados(plano(100.0), 1000.0, 1000.0), 0.0)


def test_remuestrear_conserva_las_esquinas_y_el_tamaño():
    h = np.arange(25, dtype=float).reshape(5, 5)
    r = remuestrear(h, 20)
    assert r.shape == (20, 20)
    assert r[0, 0] == h[0, 0] and r[-1, -1] == h[-1, -1]


def test_una_pasada_dividida_en_cuadros_cuenta_una_vez():
    def item(fecha, orbita, ident):
        return {"id": ident, "properties": {"datetime": f"{fecha}T23:00:00Z", "sat:relative_orbit": orbita}}
    items = [item("2026-10-06", 40, "a"), item("2026-10-06", 40, "b"), item("2026-10-06", 91, "c")]
    g = una_por_pasada(items)
    assert len(g) == 2 and g[("2026-10-06", 40)]["id"] == "a"


def test_agua_json_tiene_seis_zonas_con_sus_capas():
    if not AGUA_JSON.exists():
        pytest.skip("agua.json aún no se ha generado (python src/agua_radar.py)")
    datos = json.loads(AGUA_JSON.read_text(encoding="utf-8"))
    assert len(datos["zonas"]) == 6
    for zid, z in datos["zonas"].items():
        assert z["escenas"], f"{zid}: sin pasadas"
        for e in z["escenas"]:
            assert e["nueva_ha"] >= 0 and e["permanente_ha"] >= 0
            assert (AGUA_JSON.parent / e["archivo"]).exists(), e["archivo"]
