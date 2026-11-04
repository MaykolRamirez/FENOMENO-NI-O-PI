"""Configuración central del Monitor El Niño Perú: rutas del proyecto.

Los puntos de lluvia, los puertos y las zonas satelitales viven en cada script
(clima_nino.py e imagenes_satelite.py), junto al código que los usa.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATA_RAW = RAIZ / "data" / "raw"
