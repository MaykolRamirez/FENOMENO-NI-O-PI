"""Pruebas del relieve 3D (src/relieve.py y dashboard/data/dem). No usan internet."""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from imagenes_satelite import ZONAS  # noqa: E402
from relieve import N, tesela_xy  # noqa: E402

DEM = RAIZ / "dashboard" / "data" / "dem"


def test_tesela_en_el_origen_del_mapa():
    x, y = tesela_xy(-180.0, 0.0, 12)
    assert x == pytest.approx(0.0)
    assert y == pytest.approx(2 ** 11)            # el ecuador queda a la mitad de la vertical


def test_tesela_crece_hacia_el_este_y_hacia_el_sur():
    x0, y0 = tesela_xy(-80.0, -5.0, 12)
    x1, y1 = tesela_xy(-79.9, -5.1, 12)
    assert x1 > x0 and y1 > y0                     # más al este = x mayor; más al sur = y mayor


def test_tesela_de_piura_cae_en_peru():
    # Piura (-80,63; -5,19) a zoom 12. A mano: x = (180 - 80,63) / 360 * 4096 = 1130,6 ;
    # y = (1 + 0,02887) / 2 * 4096 = 2107,1 (0,02887 = asinh(tan 5,19°) / pi).
    x, y = tesela_xy(-80.63, -5.19, 12)
    assert (int(x), int(y)) == (1130, 2107)


def test_cada_zona_tiene_su_malla_de_relieve():
    for zid, nombre, o, s, e, n, _ in ZONAS:
        ruta = DEM / f"{zid}.json"
        if not ruta.exists():
            pytest.skip(f"{ruta.name} aún no se ha generado (python src/relieve.py)")
        d = json.loads(ruta.read_text(encoding="utf-8"))
        assert d["n"] == N, nombre
        assert len(d["h"]) == N * N, nombre
        assert d["bbox"] == [o, s, e, n], f"{nombre}: el relieve no coincide con la zona satelital"
        assert 0 <= d["min"] < d["max"] < 7000, nombre
        assert min(d["h"]) == d["min"] and max(d["h"]) == d["max"], nombre
