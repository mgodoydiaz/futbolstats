/* ============================================================================
 * Extractor de cuotas de Betano  —  pegar en la consola del navegador (F12)
 * ----------------------------------------------------------------------------
 * USO:
 *   1. Abrí la página del partido en Betano (lat.betano.com/cuotas-de-partido/...)
 *   2. Esperá a que carguen las cuotas. Hacé clic en "MOSTRAR TODO" de los
 *      mercados que te interesen (corners, goles) para desplegar las alternativas.
 *   3. F12 → pestaña "Console" → pegá TODO este archivo → Enter.
 *   4. Se copia el JSON al portapapeles y se descarga un .json.
 *   5. Movés el archivo a  01_data_raw/odds/  y corrés:
 *        python 08_models/predict_match.py --odds 01_data_raw/odds/<archivo>.json
 *
 * Produce el formato que entiende lib/odds_betano.py (1X2, goles, BTTS, corners,
 * tarjetas). Los mercados que no encuentre simplemente se omiten.
 * ========================================================================== */
(() => {
  // --- 1. equipos (del título: "Local - Visita Fútbol Cuotas | Betano") ---
  const title = document.title.split("Fútbol")[0].trim();
  const [home, away] = title.split(" - ").map(s => s.trim());

  // --- 2. recolectar (mercado → [{seleccion, cuota}]) recorriendo el DOM ---
  // Los botones de apuesta tienen aria-label: "Bet on <sel> with odds <x>."
  // Los encabezados de mercado son nodos de texto sueltos. Caminamos en orden
  // y asignamos cada botón al último encabezado visto.
  const HEADERS = [
    "Resultado del partido", "Doble oportunidad", "Goles totales Más/Menos",
    "Ambos equipos anotan", "Córners Más/Menos", "Tarjetas Totales Más/Menos",
    `${home} - Goles totales Más/Menos`, `${away} - Goles totales Más/Menos`,
  ];
  const isHeader = t => HEADERS.includes(t.trim());

  const markets = {};
  let current = null;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  const seen = new Set();
  while (walker.nextNode()) {
    const el = walker.currentNode;
    const txt = (el.childElementCount === 0 ? el.textContent : "").trim();
    if (txt && isHeader(txt)) { current = txt; markets[current] = markets[current] || []; continue; }
    const aria = el.getAttribute && el.getAttribute("aria-label");
    if (aria && /^Bet on .+ with odds [\d.]+/.test(aria) && current) {
      const m = aria.match(/^Bet on (.+) with odds ([\d.]+)/);
      const key = current + "|" + m[1];
      if (!seen.has(key)) { seen.add(key); markets[current].push({ sel: m[1].trim(), cuota: parseFloat(m[2]) }); }
    }
  }

  // --- 3. helpers de mapeo ---
  const find = (arr, re) => (arr.find(x => re.test(x.sel)) || {}).cuota ?? null;
  const ou = (arr) => {  // separa Más/Menos por línea
    const principal = [], alt = [];
    const lines = {};
    arr.forEach(x => {
      const mm = x.sel.match(/(Más|Menos)\s+([\d.]+)/);
      if (!mm) return;
      const side = mm[1] === "Más" ? "Más" : "Menos";
      (lines[mm[2]] = lines[mm[2]] || {})[side] = x.cuota;
    });
    const keys = Object.keys(lines);
    keys.forEach((ln, i) => {
      const tgt = i === 0 ? principal : alt;
      if (lines[ln]["Más"]) tgt.push({ seleccion: `Más ${ln}`, cuota: lines[ln]["Más"] });
      if (lines[ln]["Menos"]) tgt.push({ seleccion: `Menos ${ln}`, cuota: lines[ln]["Menos"] });
    });
    return { principal, alternativas: alt };
  };

  const M = {};
  if (markets["Resultado del partido"]) {
    const a = markets["Resultado del partido"];
    M.resultado_partido = { nombre: "Resultado del partido", tipo: "1X2", cuotas: [
      { seleccion: `1 (${home})`, cuota: find(a, /^1$|^1 /) ?? a[0]?.cuota ?? null },
      { seleccion: "X (Empate)", cuota: find(a, /^X$|Empate/) ?? a[1]?.cuota ?? null },
      { seleccion: `2 (${away})`, cuota: find(a, /^2$|^2 /) ?? a[2]?.cuota ?? null },
    ]};
  }
  if (markets["Goles totales Más/Menos"])
    M.goles_totales_mas_menos = { nombre: "Goles totales Más/Menos", tipo: "mas_menos", ...ou(markets["Goles totales Más/Menos"]) };
  if (markets["Ambos equipos anotan"]) {
    const a = markets["Ambos equipos anotan"];
    M.ambos_equipos_anotan = { nombre: "Ambos equipos anotan", tipo: "si_no", cuotas: [
      { seleccion: "Sí", cuota: find(a, /^Sí|^Si/) }, { seleccion: "No", cuota: find(a, /^No/) },
    ]};
  }
  if (markets["Córners Más/Menos"])
    M.corners_mas_menos = { nombre: "Córners Más/Menos", tipo: "mas_menos", ...ou(markets["Córners Más/Menos"]) };
  if (markets["Tarjetas Totales Más/Menos"])
    M.tarjetas_totales_mas_menos = { nombre: "Tarjetas Totales Más/Menos", tipo: "mas_menos", ...ou(markets["Tarjetas Totales Más/Menos"]) };
  if (markets[`${home} - Goles totales Más/Menos`])
    M.local_goles_mas_menos = { nombre: `${home} - Goles totales Más/Menos`, tipo: "mas_menos", ...ou(markets[`${home} - Goles totales Más/Menos`]) };
  if (markets[`${away} - Goles totales Más/Menos`])
    M.visita_goles_mas_menos = { nombre: `${away} - Goles totales Más/Menos`, tipo: "mas_menos", ...ou(markets[`${away} - Goles totales Más/Menos`]) };

  // --- 4. armar JSON + copiar + descargar ---
  const out = {
    partido: `${home} vs ${away}`,
    competicion: "Copa del Mundo FIFA",
    fecha: new Date().toISOString().slice(0, 10),
    fuente: "lat.betano.com",
    url: location.href,
    mercados: M,
  };
  const json = JSON.stringify(out, null, 2);
  copy?.(json);                       // copia al portapapeles (consola Chrome)
  try { navigator.clipboard.writeText(json); } catch (e) {}
  const slug = `${home}_${away}`.toLowerCase().replace(/[^a-z0-9]+/g, "_");
  const blob = new Blob([json], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `betano_${slug}_${out.fecha}.json`;
  a.click();
  console.log("✅ Extraído:", Object.keys(M).length, "mercados →", a.download);
  console.log(json);
  return out;
})();
