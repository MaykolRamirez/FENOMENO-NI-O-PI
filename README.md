# Monitor El Niño Perú

Tablero web que muestra, día a día, cómo golpea el fenómeno de El Niño al Perú: lluvias de los últimos 15 días, pronóstico, riesgo por lluvia intensa (huaicos e inundaciones), temperatura del mar y cambios del terreno vistos desde satélite.

**Sitio web:** https://maykolramirez.github.io/FENOMENO-NI-O-PI/
(se actualiza solo todos los días a las 6:30 a. m., hora de Lima)

> Herramienta independiente, con fines académicos. **No es un producto oficial** del Estado peruano ni reemplaza los avisos de SENAMHI, INDECI, COEN o ENFEN.

Proyecto del Programa de Extensión Universitaria: Ciencia del Dato (PEU-CD), INEI, 2026. Inspirado en el [Monitor de incendios del Perú](https://alexanderquispe.github.io/incendios-peru/).

## Por qué existe

El Niño 2026 es extremo: la anomalía de temperatura del mar en la región Niño 1+2 llegó a +5,4 °C a fines de octubre, por encima del máximo de 1997-98 (+4,0 °C). Las lluvias, los huaicos y las inundaciones que trae son un riesgo diario, pero la información está dispersa. Este tablero junta fuentes públicas y gratuitas en un solo lugar y responde tres preguntas: **cuánto ha llovido, qué se espera en los próximos días y cómo cambió el terreno**.

## Qué muestra

| Pestaña | Contenido |
|---|---|
| **Situación** | Titular del día, cifras clave, mapa del Perú por nivel de riesgo y rankings de los puntos con más riesgo y más lluvia sobre lo normal |
| **Lluvias 15 días** | Tabla de 26 puntos con la lluvia diaria de los últimos 15 días, el pronóstico de 5 días y la comparación con el acumulado normal de esa fecha |
| **Huaicos e inundaciones** | Una tarjeta por punto con su índice de riesgo (0–100) y sus tres componentes |
| **Satélite antes/ahora** | Comparador deslizable de imágenes Sentinel-2 en seis zonas: color real, vegetación (NDVI) y agua (NDWI), con la misma época del año anterior como referencia |
| **Mar y El Niño** | Anomalía semanal Niño 1+2 de los últimos 2 años, comparación con 1982-83, 1997-98, 2017 y 2023, temperatura del mar en 8 puertos e Índice Costero El Niño (ICEN) |
| **Método y fuentes** | Fuentes, fórmula del índice y limitaciones |

## Fuentes de datos

Todas son públicas y no requieren clave.

| Dato | Fuente |
|---|---|
| Lluvia de los últimos 15 días y pronóstico de 5 días | [Open-Meteo](https://open-meteo.com/) (modelo, no pluviómetro) |
| Climatología de lluvia 2010–2025 | Open-Meteo Archive (reanálisis ERA5) |
| Temperatura del mar frente a la costa | Open-Meteo Marine |
| Anomalía semanal Niño 1+2 | NOAA Climate Prediction Center |
| Índice Costero El Niño (ICEN) | IGP / ENFEN |
| Imágenes satelitales | Sentinel-2 L2A (Copernicus) vía [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/) |
| Límites departamentales | INEI, [peru-geojson](https://github.com/juaneladio/peru-geojson) |

## Cómo se calcula el índice de riesgo (0–100)

Mezcla tres señales respecto de lo normal en cada punto, cada una acotada entre 0 y 1:

| Señal | Peso | Definición |
|---|---:|---|
| Intensidad reciente | 40 % | Mayor lluvia diaria de los últimos 3 días ÷ p99 de los días con lluvia de ese punto |
| Pronóstico | 35 % | Mayor lluvia diaria prevista en los próximos 3 días ÷ el mismo p99 |
| Saturación | 25 % | Lluvia acumulada de 15 días ÷ el doble del acumulado normal de esa fecha (mínimo 20 mm) |

Niveles: **Bajo** < 25 · **Moderado** 25–49 · **Alto** 50–74 · **Muy alto** ≥ 75. El p99 se fija en al menos 5 mm para que una llovizna en el desierto no active la alerta. Lo normal sale de la climatología 2010–2025 de cada punto.

## Limitaciones

- **Es un indicador orientativo.** Mide lluvia intensa, no huaicos observados. Un huaico además depende de la quebrada, la pendiente y el suelo.
- **Los pesos del índice no están calibrados** contra eventos pasados (2017, 2023). En zonas áridas, como Lima, puede marcar "Moderado" con lluvias pequeñas.
- **La lluvia es de modelo**, no de pluviómetro: puede subestimar chubascos locales.
- **Solo 26 puntos** (capitales departamentales, Callao y Chimbote): una quebrada concreta puede estar peor que su capital.
- **No incluye reportes oficiales** de emergencias (INDECI/COEN) ni deslizamientos observados.
- **La imagen satelital "ahora"** es la menos nubosa de los últimos 30 días y puede ser anterior a las lluvias más recientes. Cada imagen muestra su fecha y su porcentaje de nubes. La costa nublada puede tapar zonas.
- **"Antes" es la misma época del año anterior**, no necesariamente un estado previo al evento.
- El último valor del ICEN es provisional.

## Estructura del repositorio

```
FENOMENO-NI-O-PI/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── .github/workflows/
│   └── dashboard.yml          Actualiza datos y publica el sitio cada día
├── src/
│   ├── config.py              Rutas del proyecto
│   ├── temperatura_mar.py     Niño 1+2 (NOAA) e ICEN (IGP)
│   ├── clima_nino.py          Lluvia, climatología, mar e índice de riesgo
│   └── imagenes_satelite.py   Imágenes Sentinel-2 antes y ahora
├── data/
│   ├── raw/                   nino12_semanal.csv, icen.csv
│   └── clima/                 climatologia_precip.json (caché de lo "normal")
├── docs/
│   └── metodologia.md         Definiciones operativas, fórmula del índice y pendientes
└── dashboard/                 Lo que se publica en la web
    ├── index.html
    └── data/                  lluvia.json, mar.json, resumen.json,
                               departamentos.geojson y sat/ (imágenes)
```

## Cómo ejecutarlo en local

Requiere Python 3.11 o superior.

```bash
pip install -r requirements.txt
```

Cada comando se ejecuta desde la carpeta `src/`, en este orden:

```bash
python temperatura_mar.py      # Niño 1+2 e ICEN (data/raw)
python clima_nino.py           # lluvia, mar e índice (dashboard/data); la primera vez calcula la climatología
python imagenes_satelite.py    # imágenes Sentinel-2 (dashboard/data/sat); tarda unos minutos
```

Para ver el tablero en el navegador, desde la raíz del repositorio:

```bash
python -m http.server 8765 --directory dashboard
```

y abrir http://localhost:8765. Para recalcular el resumen sin descargar de nuevo: `python clima_nino.py --sin-red`.

## Actualización automática

El archivo `.github/workflows/dashboard.yml` corre **todos los días a las 6:30 a. m. (Lima)** en los servidores de GitHub: descarga los datos, arma el sitio y lo publica en GitHub Pages. También se puede lanzar a mano desde la pestaña **Actions → Monitor El Niño → Run workflow**. Los pasos de temperatura del mar y de imágenes satelitales continúan aunque fallen, y en ese caso el sitio conserva los últimos archivos del repositorio.

## Equipo

Calle Rentería, Christopher Paul · Ramírez Santos, Maykol Ángel · Shapiama De La Cruz, Marcia · Mendizábal Huanca, Luz Ángela

## Licencia

Ver [LICENSE](LICENSE). Los datos pertenecen a sus fuentes originales (Open-Meteo, NOAA, IGP/ENFEN, Copernicus, INEI) y se usan según sus condiciones.
