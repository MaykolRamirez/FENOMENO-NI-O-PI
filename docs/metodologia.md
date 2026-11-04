# Metodología

Cómo se obtiene cada cifra del tablero, con las definiciones operativas y sus límites.

## 1. Puntos vigilados

26 puntos: las capitales departamentales (24, incluida Lima), más Callao y Chimbote, definidos en `src/clima_nino.py`. Cada punto tiene latitud y longitud y se agrupa en una región: costa norte, costa central, costa sur, sierra norte, sierra central, sierra sur o selva. En el mapa, cada departamento toma el nivel de su punto; si tiene dos (por ejemplo, Áncash con Chimbote y Huaraz), toma el más alto.

## 2. Lluvia

- **Observada (últimos 15 días):** lluvia diaria en mm de Open-Meteo (modelo numérico), de hace 14 días a hoy. El valor de hoy es parcial y puede cambiar.
- **Pronóstico:** los 5 días siguientes, de la misma fuente.
- **Acumulado de 15 días:** suma de la lluvia diaria de la ventana.
- **Lo normal:** promedio, para cada día del año, del acumulado de 15 días entre 2010 y 2025 (reanálisis ERA5 de Open-Meteo Archive). Se calcula una sola vez por punto y se guarda en `data/clima/climatologia_precip.json`.
- **Anomalía:** acumulado − normal, en mm. En % solo cuando lo normal es de al menos 5 mm; en zonas desérticas la comparación en % no es estable.
- **p99 del punto:** percentil 99 de la lluvia diaria en los días con lluvia (≥ 1 mm) entre 2010 y 2025. Mide qué es un día extremo en ese lugar. Se usa un mínimo de 5 mm.

## 3. Índice de riesgo por lluvia intensa (0–100)

Se calcula para cada punto con tres señales, cada una acotada entre 0 y 1:

```
reciente  = min(1, mayor lluvia diaria de los últimos 3 días ÷ p99)
pronóstico = min(1, mayor lluvia diaria prevista en 3 días ÷ p99)
saturación = min(1, acumulado de 15 días ÷ máx(2 × normal de esa fecha, 20 mm))

índice = 100 × (0,40 × reciente + 0,35 × pronóstico + 0,25 × saturación)
```

| Nivel | Rango |
|---|---|
| Bajo | menos de 25 |
| Moderado | 25 a 49 |
| Alto | 50 a 74 |
| Muy alto | 75 o más |

**Por qué se escala con el p99 de cada punto.** Un día con 20 mm es un evento extremo en Piura y normal en Puerto Maldonado. Medir cada punto contra su propio régimen de lluvias hace comparables las zonas.

**Estado de los pesos.** Los pesos (40/35/25) y los mínimos (5 mm y 20 mm) son un criterio de trabajo. No se han calibrado contra eventos pasados. Una validación pendiente es medir si el índice habría avisado en los episodios de 2017 y 2023. Mientras tanto debe leerse como un indicador orientativo.

## 4. Mar y El Niño

- **Anomalía semanal Niño 1+2:** diferencia entre la temperatura del mar de la región (0°–10°S, 90°–80°W) y su promedio histórico. Fuente: NOAA Climate Prediction Center (`wksst9120.for`). Se considera "El Niño" por encima de **+1 °C**, el umbral que usa el tablero.
- **Episodios de comparación:** máximo de la anomalía semanal en cada ventana: 1982-83 (jun 1982 a ago 1983), 1997-98 (abr 1997 a jun 1998), 2017 (ene a jun) y 2023 (mar 2023 a feb 2024). Las ventanas son un criterio propio y no las fechas oficiales del ENFEN.
- **ICEN:** Índice Costero El Niño del IGP/ENFEN, media móvil de 3 meses. El último valor es provisional.
- **Temperatura del mar por puerto:** promedio diario de la temperatura superficial (Open-Meteo Marine) en un punto a pocos km de la costa de Tumbes, Paita, Pimentel, Salaverry, Chimbote, Callao, Pisco e Ilo. El cambio a 7 días es la diferencia entre el último día y el de una semana antes.

## 5. Imágenes satelitales (Sentinel-2)

- **Fuente:** Sentinel-2 L2A, resolución de 10 m, desde Microsoft Planetary Computer (catálogo STAC).
- **Zonas:** seis cajas de 0,2° (unos 22 km): Tumbes, Piura, Lambayeque, Trujillo, Lima y Huaraz. Cada una cabe en una sola escena para evitar franjas negras.
- **Escena "ahora":** la de menor cobertura de nubes de los últimos 30 días (máximo 85 %).
- **Escena "antes":** la de menor cobertura de nubes en la misma época un año antes (±20 días).
- **Cobertura:** solo se aceptan escenas cuyo contorno cubre el centro y al menos 3 de las 4 esquinas de la zona.
- **Vistas:**
  - *Color real:* bandas B04, B03, B02.
  - *Vegetación (NDVI):* (B08 − B04) ÷ (B08 + B04). Rojo = suelo desnudo o sin plantas; verde = vegetación densa.
  - *Agua (NDWI):* (B03 − B08) ÷ (B03 + B08). Azul oscuro = agua o suelo muy húmedo; amarillo claro = suelo seco.
- **Alcance:** el cambio se interpreta a simple vista. No hay un mapa automático de diferencias.

## 6. Actualización

El workflow `.github/workflows/dashboard.yml` corre cada día a las 6:30 a. m. (Lima): baja el Niño 1+2 y el ICEN, recalcula lluvia, mar e índice, descarga las imágenes y publica el sitio. Los pasos de mar e imágenes continúan aunque fallen; el sitio conserva entonces los últimos archivos.

## 7. Qué falta

1. Calibrar y validar el índice con los episodios de 2017 y 2023.
2. Incorporar reportes oficiales de emergencias (INDECI/COEN) para contrastar el índice con eventos reales.
3. Añadir un mapa de cambio automático entre las imágenes de antes y ahora.
4. Ampliar los puntos hacia quebradas concretas y desagregar por provincia o distrito.
