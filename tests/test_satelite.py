"""Pruebas de la elección de escenas Sentinel-2 (src/imagenes_satelite.py). No usan internet."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from imagenes_satelite import ZONAS, cubre, dentro  # noqa: E402

CUADRADO = [(0, 0), (10, 0), (10, 10), (0, 10)]


def escena(*anillo):
    """Escena mínima con el contorno que usa cubre()."""
    return {"geometry": {"type": "Polygon", "coordinates": [list(anillo)]}}


def test_dentro_acepta_un_punto_interior():
    assert dentro((5, 5), CUADRADO)


def test_dentro_rechaza_un_punto_exterior():
    assert not dentro((15, 5), CUADRADO)
    assert not dentro((-1, 5), CUADRADO)


def test_cubre_acepta_una_escena_que_contiene_la_zona():
    zona = [2, 2, 8, 8]                                   # oeste, sur, este, norte
    assert cubre(escena(*CUADRADO), zona)


def test_cubre_rechaza_una_escena_que_solo_roza_la_zona():
    zona = [8, 8, 14, 14]                                 # solo una esquina cae dentro
    assert not cubre(escena(*CUADRADO), zona)


def test_cubre_acepta_con_tres_de_cuatro_esquinas_y_rechaza_con_dos():
    triangulo = escena((0, 0), (10, 0), (0, 10))          # corta la esquina noreste
    # Centro y 3 esquinas dentro del triángulo (x + y < 10): aceptada.
    assert cubre(triangulo, [1, 1, 4.5, 4.5])
    # Centro dentro, pero solo 2 esquinas dentro: rechazada.
    assert not cubre(triangulo, [1, 1, 9, 5.5])


def test_cubre_funciona_con_multipoligonos():
    multi = {"geometry": {"type": "MultiPolygon", "coordinates": [[CUADRADO]]}}
    assert cubre(multi, [2, 2, 8, 8])


def test_las_zonas_estan_bien_definidas():
    assert len(ZONAS) == 6
    for zid, nombre, o, s, e, n, _ in ZONAS:
        assert o < e and s < n, f"{nombre}: la caja está al revés"
        assert -19 < s and n < 0 and -82 < o and e < -68, f"{nombre}: fuera del Perú"
        assert abs((e - o) - 0.2) < 0.01 and abs((n - s) - 0.2) < 0.01, f"{nombre}: la caja no es de 0,2°"
    assert len({z[0] for z in ZONAS}) == len(ZONAS), "ids repetidos"
