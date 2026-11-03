"""Configuración central del proyecto IAPN.

Aquí viven los códigos de series, las rutas y las fechas que usan todos los
scripts. Si cambia un código o una fecha, se cambia solo en este archivo.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
DATA_RAW = RAIZ / "data" / "raw"
DATA_PROCESSED = RAIZ / "data" / "processed"
DATA_VINTAGES = RAIZ / "data" / "vintages"
REGISTROS = RAIZ / "registros" / "nowcasts"
RESULTADOS = RAIZ / "resultados"

# ---------------------------------------------------------------------------
# Series objetivo: producción nacional y sus nueve sectores (BCRPData)
# Variación porcentual interanual, mensual, desde enero de 1995.
# Verificados los diez códigos el 02/11/2026 con el nombre que devuelve la API
# (julio 2026, PBI = 3,56 %, igual a la cifra del INEI). Último mes: agosto 2026.
# ---------------------------------------------------------------------------
SERIES_OBJETIVO = {
    "PN01728AM": "Producción nacional (PBI)",
    "PN01713AM": "Agropecuario",
    "PN01716AM": "Pesca",
    "PN01717AM": "Minería e Hidrocarburos",
    "PN01720AM": "Manufactura",
    "PN01723AM": "Electricidad y Agua",
    "PN01724AM": "Construcción",
    "PN01725AM": "Comercio",
    "PN01726AM": "Otros Servicios",
    "PN01727AM": "Derechos de Importación y Otros Impuestos",
}

# ---------------------------------------------------------------------------
# Predictoras desde BCRPData.
# Regla: solo series que se publican ANTES que la cifra oficial del INEI.
# Códigos verificados el 02/11/2026. Entre corchetes, el último mes disponible
# ese día (sirve para saber qué rezago tiene cada fuente).
#
# Hallazgo: los indicadores de coyuntura del BCRP (electricidad, cemento) salen
# casi al mismo tiempo que la cifra del INEI: el 02/11 solo llegaban a agosto.
# La electricidad que sí adelanta viene del COES (src/coes.py): el 03/11 ya tenía
# setiembre y octubre.
# ---------------------------------------------------------------------------
PREDICTORAS_BCRP = {
    "PD37965AM": "Electricidad, var. % 12 meses [ago-2026]",
    "PD38039AM": "Electricidad sin minería, var. % 12 meses [ago-2026, desde 2013]",
    "PD37967GM": "Consumo interno de cemento, var. % 12 meses [ago-2026]",
    "PN01652XM": "Cobre LME, ¢US$/lb, promedio [set-2026]",
    "PN01654XM": "Oro LME, US$/oz troy, promedio [set-2026]",
    "PN01657XM": "Zinc LME, ¢US$/lb, promedio [set-2026]",
    "PN38697FM": "IGV interno, millones de S/ de 2021 (términos reales) [recaudación hasta set-2026 = actividad hasta ago-2026]",
}

# Series que NUNCA pueden ser predictoras (fuga de información).
LISTA_NEGRA = [
    "PBI desestacionalizado",
    "Sectores primarios",
    "Sectores no primarios",
    "Demanda interna",
]

# ---------------------------------------------------------------------------
# Calendario de publicación del INEI
# El Informe Técnico de Producción Nacional del mes t sale hacia el día 15
# del mes t+2 (ejemplo: julio 2026 se publicó el 15/09/2026).
# ---------------------------------------------------------------------------
DIA_PUBLICACION_INEI = 15
MESES_REZAGO_PUBLICACION = 2

# ---------------------------------------------------------------------------
# Episodios de El Niño Costero según el ENFEN.
# PROVISIONAL: confirmar inicio y fin con los comunicados oficiales del ENFEN
# antes de usarlos en la evaluación (tarea de R4, semana 1).
# ---------------------------------------------------------------------------
EPISODIOS_NINO = {
    "2017": {"inicio": "2017-01", "fin": "2017-05", "confirmado": False},
    "2023": {"inicio": "2023-03", "fin": "2024-04", "confirmado": False},
    "2026": {"inicio": "2026-03", "fin": None, "confirmado": False},
}

# ---------------------------------------------------------------------------
# Evaluación
# ---------------------------------------------------------------------------
INICIO_EVALUACION = "2010-01"
PERCENTILES = (0.10, 0.50, 0.90)
