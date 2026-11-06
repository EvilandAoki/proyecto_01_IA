/* Árbol de Minimax animado. Recibe lo que entrega /api/gato/arbol (nodos planos + eventos) y
   reproduce la búsqueda evento por evento: el árbol "crece", los valores suben y las ramas
   podadas se tachan. El estado de cualquier paso se recalcula desde cero (así se puede retroceder). */
"use strict";

const R = 17;                  // radio de un nodo
const SLOT = 42;               // ancho que ocupa cada hoja
const NIVEL = 86;              // distancia vertical entre niveles

/* Calcula la posición (x, y) de cada nodo: las hojas se reparten de izquierda a derecha y cada
   padre queda centrado sobre sus hijos. Devuelve { mapa: id -> nodo con x, y, hijos, raiz, ancho, alto }. */
function disposicion(nodos) {
  const mapa = new Map(nodos.map((n) => [n.id, { ...n, hijos: [] }]));
  let raiz = null;
  for (const n of mapa.values()) { if (n.padre === null) raiz = n; else mapa.get(n.padre).hijos.push(n); }
  let hoja = 0, maxProf = 0;
  (function rec(n) {
    maxProf = Math.max(maxProf, n.prof);
    if (!n.hijos.length) n.x = hoja++ * SLOT;
    else { n.hijos.forEach(rec); n.x = (n.hijos[0].x + n.hijos[n.hijos.length - 1].x) / 2; }
    n.y = n.prof * NIVEL;
  })(raiz);
  return { mapa, raiz, ancho: Math.max(1, hoja - 1) * SLOT, alto: maxProf * NIVEL };
}

/* Forma del nodo según su tipo (la forma, además del color, indica el tipo):
   MAX triángulo hacia arriba · MIN triángulo hacia abajo · HOJA cuadrado · CORTE rombo · PODA cuadrado punteado */
function forma(tipo) {
  const r = R;
  switch (tipo) {
    case "MAX": return G.svg("polygon", { class: "forma", points: `0,${-r - 2} ${r + 3},${r - 3} ${-r - 3},${r - 3}`, "stroke-linejoin": "round" });
    case "MIN": return G.svg("polygon", { class: "forma", points: `0,${r + 2} ${r + 3},${-r + 3} ${-r - 3},${-r + 3}`, "stroke-linejoin": "round" });
    case "HOJA": return G.svg("rect", { class: "forma", x: -r + 2, y: -r + 2, width: 2 * r - 4, height: 2 * r - 4, rx: 4 });
    case "CORTE": return G.svg("polygon", { class: "forma", points: `0,${-r - 1} ${r + 2},0 0,${r + 1} ${-r - 2},0`, "stroke-linejoin": "round" });
    default: return G.svg("rect", { class: "forma", x: -r + 2, y: -r + 2, width: 2 * r - 4, height: 2 * r - 4, rx: 4 });
  }
}

G.ArbolAnimado = function (datos) {
  const { mapa, raiz, ancho, alto } = disposicion(datos.nodos);
  const eventos = datos.eventos, N = eventos.length, margen = 46;
  const visor = G.h("div", { class: "visor-arbol", tabindex: 0, role: "figure", "aria-label": "Árbol de búsqueda de Minimax" });
  const W = ancho + 2 * margen, H = alto + 2 * margen;
  const svg = G.svg("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H });
  visor.append(svg);
  const px = (n) => n.x + margen, py = (n) => n.y + margen;
  const aristas = new Map(), elementos = new Map();

  for (const n of mapa.values()) {                       // aristas primero (quedan debajo de los nodos)
    if (n.padre === null) continue;
    const p = mapa.get(n.padre), ym = (py(p) + py(n)) / 2;
    const a = G.svg("path", { class: "arista" + (n.podado ? " podada" : ""), d: `M${px(p)} ${py(p) + R} C${px(p)} ${ym} ${px(n)} ${ym} ${px(n)} ${py(n) - R}` });
    aristas.set(n.id, a); svg.append(a);
  }
  const tipoTxt = { MAX: "MAX", MIN: "MIN", HOJA: "hoja", CORTE: "corte por profundidad", PODA: "podado" };
  for (const n of mapa.values()) {
    const g = G.svg("g", { class: "nodo " + n.tipo.toLowerCase() + (n.podado ? " podado" : ""), transform: `translate(${px(n)} ${py(n)})` });
    g.append(G.svg("title", {}, `${tipoTxt[n.tipo] || n.tipo}${n.mov ? " · jugada " + n.mov : " · raíz"}`));
    g.append(forma(n.tipo));
    const t = G.svg("text", {}, n.podado ? "" : "");
    if (n.podado) g.append(G.svg("text", { class: "tijera", y: 1 }, "✂")); else g.append(t);
    elementos.set(n.id, { g, t });
    svg.append(g);
  }
  const marcaAB = G.svg("text", { class: "etq-ab", "text-anchor": "middle", fill: "currentColor", style: "font-size:10px;fill:var(--suave);opacity:0" });
  svg.append(marcaAB);

  /* Variante principal: de la raíz siguiendo `elegido` (se resalta al terminar). */
  const principal = new Set();
  for (let n = raiz; n; ) {
    principal.add(n.id);
    n = n.elegido ? n.hijos.find((h) => h.mov === n.elegido && !h.podado) : null;
  }

  let ultimo = -1;
  function aplicar(p) {
    const visible = new Set(), valores = new Map(), ab = new Map();
    let actual = null, evaluados = 0, podas = 0;
    for (let i = 0; i < p; i++) {
      const e = eventos[i];
      if (e.tipo === "entrar") { visible.add(e.nodo); evaluados++; actual = e.nodo; ab.set(e.nodo, [e.alfa, e.beta]); }
      else if (e.tipo === "hoja" || e.tipo === "corte") valores.set(e.nodo, e.valor);
      else if (e.tipo === "subir") { valores.set(e.nodo, e.valor); actual = e.nodo; ab.set(e.nodo, [e.alfa, e.beta]); }
      else if (e.tipo === "poda") {
        podas++; actual = e.nodo; ab.set(e.nodo, [e.alfa, e.beta]);
        for (const h of mapa.get(e.nodo).hijos) if (h.podado) visible.add(h.id);
      }
    }
    const camino = new Set();
    for (let n = actual === null ? null : mapa.get(actual); n; n = n.padre === null ? null : mapa.get(n.padre)) camino.add(n.id);
    const fin = p === N;
    for (const [id, { g, t }] of elementos) {
      const n = mapa.get(id), v = valores.has(id);
      g.classList.toggle("visible", visible.has(id) || (id === raiz.id && p > 0));
      g.classList.toggle("con-valor", v);
      g.classList.toggle("actual", id === actual);
      g.classList.toggle("camino", camino.has(id) && id !== actual);
      g.classList.toggle("elegido-pv", fin && principal.has(id));
      if (!n.podado) t.textContent = v ? G.fmt(valores.get(id)) : "";
      const a = aristas.get(id);
      if (a) {
        a.classList.toggle("visible", visible.has(id));
        a.classList.toggle("camino", camino.has(id) && id !== actual);
      }
    }
    // Etiqueta de α/β sobre el nodo actual
    if (actual !== null && datos.poda && ab.get(actual)) {
      const n = mapa.get(actual), [a, b] = ab.get(actual);
      marcaAB.textContent = `α=${G.fmt(a)}  β=${G.fmt(b)}`;
      marcaAB.setAttribute("x", px(n)); marcaAB.setAttribute("y", py(n) + R + 17);
      marcaAB.style.opacity = 1;
    } else marcaAB.style.opacity = 0;
    if (actual !== null && actual !== ultimo) seguir(mapa.get(actual));
    ultimo = actual === null ? -1 : actual;
    return { p, N, evento: p ? eventos[p - 1] : null, actual: actual === null ? null : mapa.get(actual),
      evaluados, podas, alfaBeta: actual === null ? null : ab.get(actual) };
  }

  let zoom = 1;
  function seguir(n) {                    // mantiene el nodo actual a la vista
    const x = px(n) * zoom, y = py(n) * zoom;
    const fuera = x < visor.scrollLeft + 40 || x > visor.scrollLeft + visor.clientWidth - 40 ||
                  y < visor.scrollTop + 40 || y > visor.scrollTop + visor.clientHeight - 60;
    if (fuera) visor.scrollTo({ left: x - visor.clientWidth / 2, top: y - visor.clientHeight / 3, behavior: G.reducir ? "auto" : "smooth" });
  }
  function ponerZoom(z) { zoom = z; svg.setAttribute("width", W * z); svg.setAttribute("height", H * z); }
  ponerZoom(ancho > 900 ? 0.8 : 1);

  return { visor, N, datos, aplicar, ponerZoom, get zoom() { return zoom; } };
};

/* Reproductor: controla uno o varios árboles con el mismo reloj. Con dos árboles de distinta longitud
   cada uno avanza en la misma proporción (para que terminen a la vez). */
const NIVELES_VELOCIDAD = [ // [ms entre pasos, eventos por paso]
  [1100, 1], [650, 1], [380, 1], [200, 1], [100, 1], [60, 1], [60, 3], [60, 8], [60, 24]];
G.Reproductor = function (arboles, alCambiar) {
  const total = Math.max(...arboles.map((a) => a.N));
  let paso = 0, velocidad = 3, reloj = null;
  function refrescar() {
    const resultados = arboles.map((a) => a.aplicar(paso >= total ? a.N : Math.round((paso / total) * a.N)));
    alCambiar({ paso, total, resultados, reproduciendo: reloj !== null });
  }
  function tic() {
    const [ms, salto] = NIVELES_VELOCIDAD[velocidad];
    paso = Math.min(total, paso + salto);
    refrescar();
    if (paso >= total) pausa(); else reloj = setTimeout(tic, ms);
  }
  function pausa() { if (reloj) clearTimeout(reloj); reloj = null; refrescar(); }
  const api = {
    total,
    get paso() { return paso; },
    get reproduciendo() { return reloj !== null; },
    reproducir() { if (paso >= total) paso = 0; if (!reloj) { reloj = setTimeout(tic, 0); refrescar(); } },
    pausa,
    alternar() { api.reproduciendo ? pausa() : api.reproducir(); },
    mover(delta) { pausa(); paso = Math.max(0, Math.min(total, paso + delta)); refrescar(); },
    ir(k) { pausa(); paso = Math.max(0, Math.min(total, k)); refrescar(); },
    velocidad(v) { velocidad = Math.max(0, Math.min(NIVELES_VELOCIDAD.length - 1, v)); },
    detener() { if (reloj) clearTimeout(reloj); reloj = null; },
  };
  refrescar();
  return api;
};
