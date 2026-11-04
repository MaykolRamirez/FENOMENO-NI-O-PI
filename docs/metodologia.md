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
- **Resolución:** el color real se guarda a 1.600 × 1.600 px (unos 14 m por píxel); vegetación y agua, a 800 × 800 px.
- **Realce del color real:** gamma 1,9, saturación 1,7 y curva sigmoidal (11, 0,18). Sin este realce la imagen sale pálida y no se distinguen cultivos, ciudades ni cauces.
- **Preferencia de escenas:** primero las que cubren las cuatro esquinas de la zona (sin bordes negros); si no hay, se acepta una con tres.
- **Alcance:** el cambio se interpreta a simple vista. No hay un mapa automático de diferencias.

## 5b. Relieve 3D

- **Elevación:** AWS Terrain Tiles (formato Terrarium) a zoom 12 (unos 38 m por píxel en el ecuador), unidas y remuestreadas a una malla regular de 201 × 201 puntos por zona (unos 110 m de separación). Script: `src/relieve.py`. La malla no cambia día a día, por eso se genera una vez y se guarda en `dashboard/data/dem/`.
- **Proyección:** la malla está en longitud y latitud, igual que las imágenes, de modo que la imagen se pega directamente sobre el relieve.
- **Exageración vertical:** se elige según el desnivel de la zona (×8 si es menor de 400 m, ×1,5 si supera 3.500 m) y se puede ajustar de ×1 a ×8. En zonas llanas, como Piura, sin exageración casi no se distingue el relieve.
- **Visor:** three.js (versión 0.147), en el navegador. El mar se recorta a 0 m.

## 5c. Agua con radar (Sentinel-1)

- **Por qué radar:** las imágenes ópticas dependen del cielo y en la costa norte casi no hay una despejada en 15 días. El radar atraviesa las nubes y mide de día y de noche.
- **Fuente:** Sentinel-1 RTC (corregido por relieve), banda VV, desde Microsoft Planetary Computer. Hay de 4 a 6 pasadas en 15 días por zona.
- **Detección:** se suaviza la señal con un promedio 3 × 3 (reduce el moteado del radar). Un píxel es agua si su retrodispersión es menor de **−18 dB**; era tierra en la referencia si era mayor de **−15 dB**.
- **Referencia:** mediana de hasta tres pasadas de la misma época un año antes (±25 días) y **de la misma órbita**, para que el ángulo de observación no produzca diferencias falsas.
- **Agua nueva:** agua ahora y tierra en la referencia. **Agua permanente:** agua en ambas (mar, ríos, lagunas, embalses).
- **Protecciones contra falsos positivos:** se descartan los píxeles sin dato (borde de la escena), las pendientes de más de 10° (la sombra del relieve también se ve oscura) y, en el agua nueva, las manchas aisladas (apertura 3 × 3).
- **Resolución:** 800 × 800 px por zona (unos 27 m por píxel). Los ríos angostos pueden perderse.
- **Límites:** no distingue inundación de riego ni de un embalse nuevo; los umbrales son valores típicos de la literatura y no se han calibrado contra inundaciones documentadas; el ruido de base llega a unas 8 ha por pasada en zonas secas. Un aumento sostenido en varias pasadas seguidas es más confiable que una cifra aislada.

## 6. Actualización

El workflow `.github/workflows/dashboard.yml` corre cada día a las 6:30 a. m. (Lima): baja el Niño 1+2 y el ICEN, recalcula lluvia, mar e índice, descarga las imágenes ópticas y de radar, corre las pruebas y publica el sitio. Los pasos de mar e imágenes continúan aunque fallen; el sitio conserva entonces los últimos archivos.

## 7. Qué falta

1. Calibrar y validar el índice con los episodios de 2017 y 2023.
2. Incorporar reportes oficiales de emergencias (INDECI/COEN) para contrastar el índice con eventos reales.
3. Añadir un mapa de cambio automático entre las imágenes de antes y ahora.
4. Ampliar los puntos hacia quebradas concretas y desagregar por provincia o distrito.
