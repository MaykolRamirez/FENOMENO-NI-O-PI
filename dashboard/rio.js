/* Punto 5 de la reunión: "río normal frente a río con El Niño" (verlo azulito).
 *
 * Capas que se prenden y apagan por separado en el mapa 2D:
 *   - Río y agua permanente: JRC Global Surface Water (ocurrencia 1984-2021, 30 m). Es el mismo mapa que usa
 *     src/huellas.py para descartar el agua permanente (ocurrencia >= 75 %), así que lo que se ve en azul es
 *     exactamente lo que el radar NO cuenta como inundación.
 *   - Agua nueva detectada por radar en 2017 (El Niño costero), 2023 (ciclón Yaku) y últimos 24 días.
 * Vistas rápidas: río normal · 2017 · 2023 · ahora · cortina (izquierda río normal, derecha con la crecida).
 * Se activa con mapa2d.html?rio=normal|2017|2023|vivo|cortina.
 * Usa las variables globales de mapa2d.html: mapa, D, S, capaGeo, $, nf, esc, dibujarCapa, actualizar.
 */
"use strict";
const Rio = (() => {
  const GSW = "https://storage.googleapis.com/global-surface-water/tiles2021/occurrence/{z}/{x}/{y}.png";
  const EVENTOS = {
    "2017": { nombre: "El Niño costero 2017", corto: "2017", color: "#D55E00" },
    "2023": { nombre: "Ciclón Yaku 2023", corto: "2023", color: "#CC79A7" },
    vivo: { nombre: "Ahora (últimos 24 días)", corto: "ahora", color: "#E69F00" }
  };
  const VISTAS = {
    normal: { t: "Río normal", capas: [], cortina: false,
      txt: "Así se ve el río en un año normal: en azul, el agua que está casi siempre (ríos, lagunas, esteros y represas). Es la referencia para comparar." },
    "2017": { t: "El Niño 2017", capas: ["2017"], cortina: false,
      txt: "En color, el agua que el radar vio fuera del cauce en febrero–abril de 2017, encima del río normal en azul." },
    "2023": { t: "Yaku 2023", capas: ["2023"], cortina: false,
      txt: "En color, el agua nueva de marzo–abril de 2023 (ciclón Yaku), encima del río normal en azul." },
    vivo: { t: "Ahora", capas: ["vivo"], cortina: false,
      txt: "Agua nueva de los últimos 24 días. En temporada seca suele ser riego, arrozales o humedales, no desbordes." },
    cortina: { t: "Cortina", capas: ["2017"], cortina: true,
      txt: "Arrastre la barra: a la izquierda el río normal, a la derecha el mismo lugar con la crecida elegida." }
  };
  // El mapa mundial del JRC también pinta el mar y Ecuador. Se recorta a la tierra de los 76 distritos de Tumbes y
  // Piura (el mismo ámbito en que el radar mide el agua nueva), dibujando cada mosaico en un lienzo y usando los
  // límites distritales como molde. Por encima del zoom 13 (máximo del JRC) se amplía el mosaico padre.
  const NAT = 13;
  let MOLDE = null;
  function molde() {
    if (MOLDE) return MOLDE;
    const anillos = [], caja = [Infinity, Infinity, -Infinity, -Infinity];
    for (const f of D.DIST.features) {
      const g = f.geometry, pols = g.type === "MultiPolygon" ? g.coordinates : [g.coordinates];
      for (const p of pols) {
        const r = p[0].map(([lon, lat]) => { const q = L.CRS.EPSG3857.latLngToPoint(L.latLng(lat, lon), 0); caja[0] = Math.min(caja[0], q.x); caja[1] = Math.min(caja[1], q.y); caja[2] = Math.max(caja[2], q.x); caja[3] = Math.max(caja[3], q.y); return [q.x, q.y] });
        anillos.push(r);
      }
    }
    return MOLDE = { anillos, caja };
  }
  // Paleta del JRC: rojo (agua rara vez) a azul (agua siempre); ocurrencia ≈ azul / (rojo + azul).
  // Se repinta en una sola escala de azules: celeste = agua algunos años, azul oscuro = agua todo el año.
  const CEL = [158, 202, 225], OSC = [8, 48, 107];
  function azular(g, s, umbral) {
    const im = g.getImageData(0, 0, s.x, s.y), d = im.data;
    for (let i = 0; i < d.length; i += 4) {
      if (!d[i + 3]) continue;
      const o = d[i + 2] / Math.max(1, d[i] + d[i + 2]);
      if (o < umbral) { d[i + 3] = 0; continue }
      d[i] = CEL[0] + (OSC[0] - CEL[0]) * o; d[i + 1] = CEL[1] + (OSC[1] - CEL[1]) * o; d[i + 2] = CEL[2] + (OSC[2] - CEL[2]) * o;
      d[i + 3] = 150 + 105 * o;
    }
    g.putImageData(im, 0, 0);
  }
  const AguaEnTierra = L.GridLayer.extend({
    options: { umbral: 0 },
    createTile(c, listo) {
      const t = document.createElement("canvas"), s = this.getTileSize(), k = Math.pow(2, c.z), M = molde();
      t.width = s.x; t.height = s.y;
      const x0 = c.x * s.x, y0 = c.y * s.y, B = M.caja;
      if (x0 > B[2] * k || x0 + s.x < B[0] * k || y0 > B[3] * k || y0 + s.y < B[1] * k) { setTimeout(() => listo(null, t)); return t }
      const d = Math.max(0, c.z - NAT), z = c.z - d, px = c.x >> d, py = c.y >> d, f = 1 << d, sub = s.x / f;
      const img = new Image(), url = GSW.replace("{z}", z).replace("{x}", px).replace("{y}", py);
      img.onload = () => {
        const g = t.getContext("2d");
        g.imageSmoothingEnabled = false;
        g.drawImage(img, (c.x - px * f) * sub, (c.y - py * f) * sub, sub, sub, 0, 0, s.x, s.y);
        if (img.crossOrigin) azular(g, s, this.options.umbral);
        g.globalCompositeOperation = "destination-in";
        g.beginPath();
        for (const r of M.anillos) { r.forEach(([x, y], i) => { const a = x * k - x0, b = y * k - y0; i ? g.lineTo(a, b) : g.moveTo(a, b) }); g.closePath() }
        g.fill();
        listo(null, t);
      };
      // si el servidor dejara de permitir CORS, se muestra la paleta original del JRC (rojo = poco, azul = siempre)
      img.onerror = () => { if (img.crossOrigin) { img.removeAttribute("crossorigin"); img.crossOrigin = null; img.src = url + "#x" } else listo(null, t) };
      img.crossOrigin = "anonymous";
      img.src = url;
      return t;
    }
  });
  const R = { activo: false, vista: null, capas: {}, gsw: null, cortinaX: .5, cortina: false, panelEvento: null, barra: null };

  function css() {
    const s = document.createElement("style");
    s.textContent = `
.rio .vistas{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 8px}
.rio .vistas button{min-height:32px;padding:4px 10px;font-size:13px;border-radius:999px}
.rio .vistas button[aria-pressed="true"]{background:var(--acento);border-color:var(--acento);color:#fff}
.rio .txt{font-size:13px;color:var(--tx2);margin:0 0 8px;min-height:2.9em}
.rio .fila{display:flex;align-items:center;gap:6px;font-size:14px;padding:2px 0}
.rio .fila i{display:inline-block;width:14px;height:14px;border-radius:3px;border:1px solid #0003;flex:none}
.rio .grad{width:52px!important;background:linear-gradient(90deg,#9ecae1,#08306b)}
.rio .barras{margin-top:8px;font-size:12.5px}
.rio .barras .b{display:grid;grid-template-columns:96px 1fr 64px;gap:6px;align-items:center;margin:3px 0}
.rio .barras .b span{height:12px;border-radius:3px;display:block;min-width:2px}
.rio .barras .n{text-align:right;font-variant-numeric:tabular-nums}
.rio .veces{font-size:13px;margin:6px 0 0}
.rio input[type=range]{width:100%}
.rio-cortina{position:absolute;top:0;bottom:0;width:0;z-index:650;pointer-events:none}
.rio-cortina .linea{position:absolute;top:0;bottom:0;left:-2px;width:4px;background:#fff;box-shadow:0 0 0 1px #0007}
.rio-cortina .asa{position:absolute;top:50%;left:-19px;width:38px;height:38px;margin-top:-19px;border-radius:50%;background:#fff;border:2px solid #14212b;
  display:flex;align-items:center;justify-content:center;font-size:18px;color:#14212b;cursor:ew-resize;pointer-events:auto;touch-action:none;user-select:none}
.rio-etq{position:absolute;top:8px;z-index:650;padding:3px 8px;border-radius:6px;font-size:12.5px;font-weight:600;background:#14212bd9;color:#fff;pointer-events:none}
`;
    document.head.appendChild(s);
  }

  function panel() {
    const caja = document.createElement("div");
    caja.className = "caja rio";
    caja.id = "rio";
    caja.innerHTML = `
      <h2>El río: normal frente a El Niño</h2>
      <div class="vistas" role="group" aria-label="Vista del río">${Object.entries(VISTAS).map(([k, v]) => `<button type="button" data-v="${k}" aria-pressed="false">${v.t}</button>`).join("")}</div>
      <p class="txt" id="rio-txt">Elija una vista para ver el río en un año normal y cuánto se extendió el agua con El Niño.</p>
      <label class="fila"><input type="checkbox" id="rio-k-gsw"> <i class="grad"></i> Río y agua permanente (JRC, 30 m)</label>
      ${Object.entries(EVENTOS).map(([k, e]) => `<label class="fila"><input type="checkbox" id="rio-k-${k}" data-ev="${k}"> <i style="background:${e.color}"></i> Agua nueva: ${e.nombre}</label>`).join("")}
      <label class="fila"><input type="checkbox" id="rio-k-cortina"> Cortina: izquierda río normal, derecha con la crecida</label>
      <label class="fila" style="flex-direction:column;align-items:stretch;font-size:12px;color:var(--tx2)">Intensidad del azul
        <input type="range" id="rio-op" min="20" max="100" value="85" aria-label="Opacidad del agua permanente"></label>
      <div style="font-size:12px;color:var(--tx2)">Azul oscuro: agua casi todo el año · celeste: agua solo algunos años o en temporada.</div>
      <label class="fila" style="font-size:13px"><input type="checkbox" id="rio-k-perm"> Solo agua permanente (≥ 75 % del tiempo, el mismo criterio del radar)</label>
      <div class="barras" id="rio-barras"></div>
      <p style="font-size:12px;color:var(--tx2);margin:6px 0 0">Agua permanente: JRC Global Surface Water (Comisión Europea, imágenes Landsat 1984–2021). Agua nueva: radar Sentinel-1, que ya descuenta la permanente (ocurrencia ≥ 75 %). El radar es un mínimo: no ve el agua entre calles ni en la sierra.</p>`;
    const capas = document.querySelector(".caja.capas");
    capas.parentNode.insertBefore(caja, capas);
    caja.querySelectorAll(".vistas button").forEach(b => b.onclick = () => vista(b.dataset.v));
    $("#rio-k-gsw").onchange = aplicar;
    Object.keys(EVENTOS).forEach(k => $("#rio-k-" + k).onchange = aplicar);
    $("#rio-k-cortina").onchange = aplicar;
    $("#rio-k-perm").onchange = e => { if (R.gsw) { R.gsw.options.umbral = e.target.checked ? .75 : 0; R.gsw.redraw() } };
    $("#rio-op").oninput = e => { if (R.gsw) R.gsw.setOpacity(e.target.value / 100) };
  }

  function barras() {
    const ev = D.IN.eventos, perm = (ev["2017"] && ev["2017"].qa && ev["2017"].qa.km2_agua_permanente_tierra) || null;
    const filas = [["Río normal", perm, "#2b2bff"]].concat(Object.entries(EVENTOS).filter(([k]) => ev[k]).map(([k, e]) => [e.corto === "ahora" ? "Ahora" : e.corto, ev[k].km2, e.color]));
    const mx = Math.max(...filas.map(f => f[1] || 0), 1);
    let h = `<div style="font-weight:600;margin-bottom:2px">¿Cuánto se extendió el agua? (km² en tierra de Tumbes y Piura)</div>` +
      filas.map(([t, v, c]) => `<div class="b"><div>${esc(t)}</div><div><span style="width:${(v || 0) / mx * 100}%;background:${c}"></span></div><div class="n">${nf(v, 1)}</div></div>`).join("");
    if (perm && ev["2017"]) h += `<p class="veces">En 2017 el agua nueva cubrió <b>${nf(ev["2017"].km2 / perm, 1)} veces</b> la superficie del río normal${ev["2023"] ? `; en 2023, <b>${nf(ev["2023"].km2 / perm, 1)} veces</b>` : ""}.</p>`;
    $("#rio-barras").innerHTML = h;
  }

  function vista(k) {
    const v = VISTAS[k]; if (!v) return;
    R.vista = k;
    document.querySelectorAll("#rio .vistas button").forEach(b => b.setAttribute("aria-pressed", b.dataset.v === k));
    $("#rio-txt").textContent = v.txt;
    $("#rio-k-gsw").checked = true;
    Object.keys(EVENTOS).forEach(e => $("#rio-k-" + e).checked = v.capas.includes(e));
    $("#rio-k-cortina").checked = v.cortina;
    // La mancha general (celeste) se confunde con el azul del río y los puntos tapan el cauce: se apagan al
    // entrar a la vista del río (se pueden volver a prender en "Capas"). Las cifras pasan al evento elegido.
    const ev = v.capas[0];
    let cambio = false;
    ["k-mancha", "k-col", "k-sal", "k-edif", "k-pob", "k-eve"].forEach(id => { const c = $("#" + id); if (c && c.checked) { c.checked = false; cambio = true } });
    if (ev && D.IN.eventos[ev] && S.esc !== ev) { S.esc = ev; $("#f-esc").value = ev; cambio = true }
    if (cambio) dibujarCapa().then(() => actualizar(false));
    aplicar();
  }

  async function aplicar() {
    if (!R.gsw) {
      mapa.createPane("rioBase").style.zIndex = 390;
      mapa.createPane("rioEvento").style.zIndex = 410;
      R.render = L.canvas({ pane: "rioEvento", padding: .5 });
      R.gsw = new AguaEnTierra({ pane: "rioBase", maxZoom: 18, opacity: $("#rio-op").value / 100, umbral: $("#rio-k-perm").checked ? .75 : 0,
        attribution: "Agua permanente: EC JRC/Google, Global Surface Water" });
    }
    if ($("#rio-k-gsw").checked) R.gsw.addTo(mapa); else mapa.removeLayer(R.gsw);
    for (const k of Object.keys(EVENTOS)) {
      const on = $("#rio-k-" + k).checked;
      if (on && !R.capas[k]) {
        const g = await capaGeo(k);
        if (g) R.capas[k] = L.geoJSON(g, { pane: "rioEvento", renderer: R.render, interactive: false,
          style: { stroke: false, fillColor: EVENTOS[k].color, fillOpacity: .8 } });
      }
      if (R.capas[k]) { if (on) R.capas[k].addTo(mapa); else mapa.removeLayer(R.capas[k]) }
    }
    cortina($("#rio-k-cortina").checked);
  }

  function cortina(on) {
    R.cortina = on;
    const cont = mapa.getContainer();
    if (on && !R.barra) {
      R.barra = L.DomUtil.create("div", "rio-cortina", cont);
      R.barra.innerHTML = `<div class="linea"></div><div class="asa" tabindex="0" role="slider" aria-label="Cortina: mover para comparar" aria-valuemin="0" aria-valuemax="100">⇔</div>`;
      R.etqI = L.DomUtil.create("div", "rio-etq", cont); R.etqI.style.left = "52px"; R.etqI.textContent = "Río normal";
      R.etqD = L.DomUtil.create("div", "rio-etq", cont); R.etqD.style.right = "8px";
      const asa = R.barra.querySelector(".asa");
      L.DomEvent.disableClickPropagation(R.barra);
      const mover = ev => { const r = cont.getBoundingClientRect(); R.cortinaX = Math.min(.98, Math.max(.02, (ev.clientX - r.left) / r.width)); recortar() };
      asa.addEventListener("pointerdown", ev => { ev.preventDefault(); ev.stopPropagation(); mapa.dragging.disable(); asa.setPointerCapture(ev.pointerId);
        asa.onpointermove = mover; asa.onpointerup = () => { asa.onpointermove = null; mapa.dragging.enable() } });
      asa.addEventListener("keydown", ev => { const d = ev.key === "ArrowLeft" ? -.05 : ev.key === "ArrowRight" ? .05 : 0; if (d) { ev.preventDefault(); R.cortinaX = Math.min(.98, Math.max(.02, R.cortinaX + d)); recortar() } });
      mapa.on("move zoom resize zoomend moveend", recortar);
    }
    [R.barra, R.etqI, R.etqD].forEach(x => { if (x) x.style.display = on ? "" : "none" });
    const elegidos = Object.keys(EVENTOS).filter(k => $("#rio-k-" + k).checked).map(k => EVENTOS[k].corto);
    if (on) R.etqD.textContent = elegidos.length ? "Con " + elegidos.join(" + ") : "Marque una crecida";
    recortar();
  }

  function recortar() {
    const p = mapa.getPane("rioEvento"); if (!p) return;
    if (!R.cortina) { p.style.clip = ""; return }
    const t = mapa.getSize(), nw = mapa.containerPointToLayerPoint([0, 0]), se = mapa.containerPointToLayerPoint(t), x = t.x * R.cortinaX;
    p.style.clip = `rect(${nw.y}px, ${se.x}px, ${se.y}px, ${nw.x + x}px)`;
    R.barra.style.left = x + "px";
    R.barra.querySelector(".asa").setAttribute("aria-valuenow", Math.round(R.cortinaX * 100));
  }

  function iniciar() {
    if (!window.L || !mapa || !D || !D.IN) return;
    css(); panel(); barras();
    const p = new URLSearchParams(location.search).get("rio");
    if (p && VISTAS[p]) { vista(p); document.getElementById("rio").scrollIntoView({ block: "nearest" }) }
  }
  return { iniciar, vista };
})();
