"""Datos base de exposición a inundaciones para Tumbes: edificaciones, ríos y terreno fino.

Uso:
    python src/datos_tumbes.py edificios   # Google Open Buildings v3 (tesela 903, ~409 MB comprimidos; se filtra al vuelo)
    python src/datos_tumbes.py rios        # red hidrográfica de OpenStreetMap (Overpass)
    python src/datos_tumbes.py terreno     # Copernicus DEM GLO-30 (30 m) en AWS Open Data

Todo se guarda en data/crudo/tumbes/ (ignorado por git; se regenera con este script).
Solo se conservan las edificaciones dentro del polígono del departamento de Tumbes.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import zlib

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from matplotlib.path import Path as Trazo

from config import RAIZ

SALIDA = RAIZ / "data" / "crudo" / "tumbes"
LIMITE = RAIZ / "dashboard" / "data" / "departamentos.geojson"
TESELA = "https://storage.googleapis.com/open-buildings-data/v3/polygons_s2_level_4_gzip/903_buildings.csv.gz"
OVERPASS_ESPEJOS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
DEM_URL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM/Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM.tif"
CLIENTE = {"User-Agent": "monitor-nino-peru-academico/0.1"}


def limite_tumbes() -> np.ndarray:
    g = json.loads(LIMITE.read_text(encoding="utf-8"))
    for f in g["features"]:
        if f["properties"]["NOMBDEP"] == "TUMBES":
            return np.array(f["geometry"]["coordinates"][0])
    raise SystemExit("No se encontró Tumbes en departamentos.geojson")


def lineas_gz(url: str):
    """Descomprime el .csv.gz en streaming, sin guardar el archivo completo."""
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    resto = b""
    with requests.get(url, stream=True, timeout=120, headers=CLIENTE) as r:
        r.raise_for_status()
        for trozo in r.iter_content(1 << 20):
            datos = resto + d.decompress(trozo)
            partes = datos.split(b"\n")
            resto = partes.pop()
            for p in partes:
                yield p.decode("utf-8")
    if resto:
        yield resto.decode("utf-8")


def edificios() -> None:
    poli = limite_tumbes()
    w, s, e, n = poli[:, 0].min(), poli[:, 1].min(), poli[:, 0].max(), poli[:, 1].max()
    trazo = Trazo(poli)
    filas, total = [], 0
    it = lineas_gz(TESELA)
    cab = next(it).split(",")
    print("columnas:", cab)
    for linea in it:
        total += 1
        if total % 5_000_000 == 0:
            print(f"  {total:,} leídas, {len(filas):,} en la caja de Tumbes", flush=True)
        a = linea.split(",", 2)
        lat, lon = float(a[0]), float(a[1])
        if w <= lon <= e and s <= lat <= n:
            fila = next(csv.reader([linea]))
            filas.append((lat, lon, float(fila[2]), float(fila[3]), fila[4]))
    print(f"Leídas {total:,}; en la caja {len(filas):,}")
    pts = np.array([(f[1], f[0]) for f in filas])
    dentro = trazo.contains_points(pts)
    filas = [f for f, ok in zip(filas, dentro) if ok]
    print(f"Dentro del polígono de Tumbes: {len(filas):,}")
    tabla = pa.table({"lat": [f[0] for f in filas], "lon": [f[1] for f in filas], "area_m2": [f[2] for f in filas],
                      "confianza": [f[3] for f in filas], "wkt": [f[4] for f in filas]})
    SALIDA.mkdir(parents=True, exist_ok=True)
    pq.write_table(tabla, SALIDA / "edificios.parquet", compression="zstd")


def rios() -> None:
    poli = limite_tumbes()
    w, s, e, n = poli[:, 0].min(), poli[:, 1].min(), poli[:, 0].max(), poli[:, 1].max()
    q = f'[out:json][timeout:180];way["waterway"~"^(river|stream|canal|drain)$"]({s},{w},{n},{e});out geom tags;'
    r = None
    for intento in range(6):
        url = OVERPASS_ESPEJOS[intento % len(OVERPASS_ESPEJOS)]
        try:
            r = requests.post(url, data={"data": q}, headers=CLIENTE, timeout=240)
            if r.status_code == 200:
                break
            print(f"  {url}: HTTP {r.status_code}, reintento…")
        except requests.RequestException as ex:
            print(f"  {url}: {type(ex).__name__}, reintento…")
        time.sleep(10)
    if r is None or r.status_code != 200:
        raise SystemExit("Overpass no respondió; reintentar más tarde")
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "rios_osm.json").write_text(r.text, encoding="utf-8")
    tipos: dict[str, int] = {}
    for el in r.json()["elements"]:
        t = el.get("tags", {}).get("waterway", "?")
        tipos[t] = tipos.get(t, 0) + 1
    print("Tramos por tipo:", tipos)


def terreno() -> None:
    (SALIDA / "dem").mkdir(parents=True, exist_ok=True)
    for ns in ("S04", "S05"):
        for ew in ("W081", "W082"):
            dest = SALIDA / "dem" / f"{ns}_{ew}.tif"
            r = requests.get(DEM_URL.format(ns=ns, ew=ew), timeout=300, headers=CLIENTE)
            if r.status_code != 200:
                print(f"{ns}_{ew}: no existe ({r.status_code})")
                continue
            dest.write_bytes(r.content)
            print(f"{ns}_{ew}: {len(r.content) / 1e6:.1f} MB")


if __name__ == "__main__":
    {"edificios": edificios, "rios": rios, "terreno": terreno}[sys.argv[1]]()
