/* Animación de DFS, BFS, UCS y A* sobre el Gato en movimiento.
   Dos fases: EXPLORACIÓN (el estado que se expande en cada paso, contadores en vivo, gráfica de la
   frontera y mapa de calor de casillas) y SOLUCIÓN (las fichas se deslizan por el camino hallado). */
"use strict";

const REGLA_SALIDA = {
  "DFS": "DFS usa una pila: expande siempre el último estado que entró, así que se interna por una sola rama.",
  "BFS": "BFS usa una cola: expande el estado más antiguo, así que avanza nivel por nivel (menos pasos).",
  "UCS": "UCS usa una cola de prioridad por costo acumulado g: expande lo más barato hasta ahora.",
  "A* (h1)": "A* usa una cola de prioridad por f = g + h (h = heurística propia): expande lo que parece más prometedor.",
  "A* (h2)": "A* usa una cola de prioridad por f = g + h (h2 = heurística simple, más débil que h1).",
};
const EVENTOS_POR_SEG = [4, 10, 25, 60, 150, 400, 1000, 3000];
const DURACION_PASO = [1600, 1200, 900, 650, 450, 300, 200, 120];   // ms por paso de la solución

G.PanelBusqueda = function (contenedor, caso, datos) {
  const traza = datos.traza, M = traza.length, camino = datos.camino, tema = () => G.tema();
  let modo = "exploracion", k = 0, j = 0, reloj = null, vel = 0;
  let acumulado = 0;
  // Velocidad por defecto: que la exploración dure unos 6 segundos.
  vel = EVENTOS_POR_SEG.findIndex((v) => v >= M / 6); if (vel < 0) vel = EVENTOS_POR_SEG.length - 1;

  const cajaTablero = G.h("div", {});
  const tablero = G.tableroMovil(cajaTablero, caso, { entrada: true });
  tablero.poner(datos.inicial, { animar: false });
  const verLineas = G.h("input", { type: "checkbox", id: "ver-lineas", onchange: () => tablero.lineasPosibles(verLineas.checked ? caso.lineas : null) });
  verLineas.checked = caso.lineas.length <= 6;          // con muchas líneas (5×5) se ve recargado: queda apagado
  tablero.lineasPosibles(verLineas.checked ? caso.lineas : null);

  /* ---- gráfica de crecimiento (frontera y explorados) ---- */
  const GW = 460, GH = 130, gm = { i: 36, d: 8, s: 10, b: 22 };
  const maxY = Math.max(1, ...traza.map((e) => Math.max(e[3], e[4])));
  const gx = (i) => gm.i + (M <= 1 ? 0 : (i / (M - 1)) * (GW - gm.i - gm.d));
  const gy = (v) => gm.s + (GH - gm.s - gm.b) * (1 - v / maxY);
  const ruta = (idx) => traza.map((e, i) => `${i ? "L" : "M"}${gx(i).toFixed(1)} ${gy(e[idx]).toFixed(1)}`).join(" ");
  const gSvg = G.svg("svg", { viewBox: `0 0 ${GW} ${GH}`, class: "mini-grafica", role: "img", "aria-label": "Crecimiento de la frontera y de los explorados" });
  const clip = G.svg("rect", { x: 0, y: 0, width: 0, height: GH });
  gSvg.append(G.svg("defs", {}, G.svg("clipPath", { id: "clip-traza" }, clip)));
  const pintarBase = () => {
    G.vaciar(gSvg).append(G.svg("defs", {}, G.svg("clipPath", { id: "clip-traza" }, clip)));
    const t = tema();
    gSvg.append(G.svg("line", { x1: gm.i, x2: GW - gm.d, y1: gy(0), y2: gy(0), stroke: t.borde }),
      G.svg("text", { x: gm.i - 5, y: gy(maxY) + 4, "text-anchor": "end", "font-size": 10, fill: t.suave, "font-family": "system-ui" }, G.corto(maxY)),
      G.svg("text", { x: gm.i - 5, y: gy(0) + 4, "text-anchor": "end", "font-size": 10, fill: t.suave, "font-family": "system-ui" }, "0"),
      G.svg("text", { x: gm.i, y: GH - 5, "font-size": 10, fill: t.suave, "font-family": "system-ui" }, "expansiones →"),
      G.svg("g", { "clip-path": "url(#clip-traza)" },
        G.svg("path", { d: ruta(4), fill: "none", stroke: t.series[1], "stroke-width": 2.5 }),
        G.svg("path", { d: ruta(3), fill: "none", stroke: t.series[0], "stroke-width": 2.5, "stroke-dasharray": "6 3" })));
  };
  pintarBase();
  document.addEventListener("tema-cambiado", pintarBase);

  /* ---- contadores ---- */
  const cont = {};
  const tarjetaNum = (clave, etiqueta) => { cont[clave] = G.h("div", { class: "valor mono" }, "0"); return G.h("div", { class: "metrica" }, cont[clave], G.h("div", { class: "etiqueta" }, etiqueta)); };
  const contadores = G.h("div", { class: "metricas", "aria-live": "off" },
    tarjetaNum("exp", "Expandidos"), tarjetaNum("fro", "En la frontera"), tarjetaNum("g", "Costo g del estado"), tarjetaNum("f", "f = g + h"));
  const texto = G.h("div", { class: "explicacion", "aria-live": "polite" });

  /* ---- modos y controles ---- */
  const btnExp = G.h("button", { class: "boton", type: "button", onclick: () => cambiarModo("exploracion") }, "1 · Exploración");
  const btnSol = G.h("button", { class: "boton", type: "button", onclick: () => cambiarModo("solucion") }, "2 · Solución");
  const btnPlay = G.h("button", { class: "boton primario", type: "button", onclick: () => alternar() }, "▶ Reproducir");
  const barra = G.h("input", { type: "range", min: 0, max: M, value: 0, "aria-label": "Posición en la animación", style: "width:100%", oninput: (e) => ir(+e.target.value) });
  const velocidad = G.h("input", { type: "range", min: 0, max: EVENTOS_POR_SEG.length - 1, value: vel, "aria-label": "Velocidad", oninput: (e) => { vel = +e.target.value; } });
  const lista = G.h("ol", { class: "lista-pasos" });
  camino.forEach((p, i) => lista.append(G.h("li", { id: "paso-" + i }, `${p.texto}  `, G.h("span", { class: "suave" }, `(+${p.costo})`))));
  const controles = G.h("div", { class: "controles", style: "margin:10px 0 6px" },
    G.h("div", { class: "grupo-botones" },
      G.h("button", { class: "boton", type: "button", title: "Al inicio", "aria-label": "Al inicio", onclick: () => ir(0) }, "⏮"),
      G.h("button", { class: "boton", type: "button", title: "Paso atrás", "aria-label": "Paso atrás", onclick: () => ir(posicion() - paso()) }, "◀"),
      btnPlay,
      G.h("button", { class: "boton", type: "button", title: "Paso adelante", "aria-label": "Paso adelante", onclick: () => ir(posicion() + paso()) }, "▶"),
      G.h("button", { class: "boton", type: "button", title: "Al final", "aria-label": "Al final", onclick: () => ir(maximo()) }, "⏭")),
    G.h("label", { class: "campo" }, "Velocidad", velocidad));
  const resumenSolucion = G.h("div", { class: "suave pequeno", style: "margin-top:6px" });

  const izquierda = G.h("div", { class: "tarjeta" },
    G.h("div", { class: "grupo-botones", style: "margin-bottom:10px" }, btnExp, btnSol),
    cajaTablero,
    G.h("label", { class: "check", style: "margin-top:10px" }, verLineas, "Mostrar las líneas meta posibles (bandas verdes; más oscuro donde se cruzan)"),
    G.h("div", { class: "leyenda", style: "margin-top:10px" },
      G.h("span", {}, G.svg("svg", { width: 16, height: 16, viewBox: "0 0 16 16" }, G.svg("path", { d: "M3 3L13 13M13 3L3 13", class: "trazo-x", "stroke-width": 3, "stroke-linecap": "round" })), "ficha X (se mueve)"),
      G.h("span", {}, G.svg("svg", { width: 16, height: 16, viewBox: "0 0 16 16" }, G.svg("circle", { cx: 8, cy: 8, r: 5, fill: "none", class: "trazo-o", "stroke-width": 3 })), "obstáculo O (fijo)"),
      G.h("span", {}, G.svg("svg", { width: 26, height: 10, viewBox: "0 0 26 10" }, G.svg("line", { x1: 1, y1: 5, x2: 20, y2: 5, class: "flecha-mov", "stroke-width": 3 }), G.svg("polygon", { points: "25,5 19,1.5 19,8.5", class: "flecha-cabeza" })), "recto: +2"),
      G.h("span", {}, G.svg("svg", { width: 26, height: 10, viewBox: "0 0 26 10" }, G.svg("line", { x1: 1, y1: 5, x2: 20, y2: 5, class: "flecha-mov diagonal", "stroke-width": 3 }), G.svg("polygon", { points: "25,5 19,1.5 19,8.5", class: "flecha-cabeza" })), "diagonal: +3"),
      G.h("span", {}, G.svg("svg", { width: 14, height: 14 }, G.svg("rect", { x: 0, y: 0, width: 14, height: 14, rx: 3, style: "fill:var(--acento);opacity:.5" })), "más veces ocupada")));
  const derecha = G.h("div", { class: "tarjeta" }, contadores,
    G.h("div", { style: "margin-top:12px" },
      G.h("div", { class: "cab-grafico", style: "margin-bottom:2px" }, G.h("strong", { class: "pequeno" }, "Tamaño de la frontera y de los explorados"),
        G.h("span", { class: "leyenda" }, G.h("span", {}, G.svg("svg", { width: 22, height: 6 }, G.svg("line", { x1: 0, x2: 22, y1: 3, y2: 3, style: "stroke:var(--serie-1);stroke-width:3;stroke-dasharray:6 3" })), "frontera"),
          G.h("span", {}, G.svg("svg", { width: 22, height: 6 }, G.svg("line", { x1: 0, x2: 22, y1: 3, y2: 3, style: "stroke:var(--serie-2);stroke-width:3" })), "explorados"))),
      gSvg),
    controles, barra, G.h("div", { style: "margin-top:10px" }, texto), resumenSolucion, lista);
  lista.hidden = true;
  contenedor.append(G.h("div", { class: "rejilla lado" }, izquierda, derecha));

  /* ---- lógica ---- */
  const maximo = () => (modo === "exploracion" ? M : camino.length);
  const posicion = () => (modo === "exploracion" ? k : j);
  const paso = () => (modo === "exploracion" ? Math.max(1, Math.round(M / 60)) : 1);

  function pintarExploracion() {
    tablero.sinMovimiento(); tablero.linea(null); tablero.meta(null);
    const calor = Array(caso.n * caso.n).fill(0);
    for (let i = 0; i < k; i++) for (const c of traza[i][0]) calor[c]++;
    tablero.calor(calor);
    if (k === 0) {
      tablero.poner(datos.inicial, { animar: false });
      for (const c of Object.keys(cont)) cont[c].textContent = "0";
      texto.textContent = REGLA_SALIDA[datos.algoritmo] + " Pulsa ▶ para ver cómo recorre los estados.";
    } else {
      const e = traza[k - 1];
      tablero.poner(e[0], { animar: false });
      cont.exp.textContent = G.miles(e[4]); cont.fro.textContent = G.miles(e[3]);
      cont.g.textContent = e[1]; cont.f.textContent = e[2];
      texto.textContent = `Expande un estado con g = ${e[1]}${/A\*/.test(datos.algoritmo) ? `, h = ${e[2] - e[1]}, f = ${e[2]}` : ""}. Hay ${G.miles(e[3])} estados esperando en la frontera y ${G.miles(e[4])} ya explorados.` +
        (datos.muestreo > 1 ? ` (Se muestra 1 de cada ${datos.muestreo} expansiones.)` : "");
    }
    clip.setAttribute("width", M ? gm.i + (k / M) * (GW - gm.i - gm.d) : 0);
  }
  function pintarSolucion(deslizar) {
    tablero.calor(Array(caso.n * caso.n).fill(0));
    tablero.meta(null); tablero.linea(null);
    clip.setAttribute("width", GW);                 // en la solución la gráfica muestra la búsqueda completa
    const ult = camino.length ? camino[camino.length - 1].estado : datos.inicial;
    const estado = j === 0 ? datos.inicial : camino[j - 1].estado;
    if (deslizar && j > 0) tablero.mover(camino[j - 1].accion[0], camino[j - 1].accion[1]); else tablero.poner(estado, { animar: false });
    if (j > 0) tablero.movimiento(camino[j - 1].accion[0], camino[j - 1].accion[1], camino[j - 1].costo); else tablero.sinMovimiento();
    if (j === camino.length && j > 0) tablero.linea(ult);           // meta alcanzada: se traza la línea, como al ganar
    const acum = camino.slice(0, j).reduce((s, p) => s + p.costo, 0);
    cont.exp.textContent = j; cont.fro.textContent = camino.length - j; cont.g.textContent = acum; cont.f.textContent = datos.metricas.costo;
    [...lista.children].forEach((li, i) => { li.classList.toggle("hecho", i < j); li.classList.toggle("actual", i === j - 1); });
    texto.textContent = j === 0 ? `Solución encontrada: ${camino.length} pasos y costo total ${datos.metricas.costo}. Pulsa ▶ para ver cómo se mueven las fichas.`
      : j < camino.length ? `Paso ${j} de ${camino.length}: se mueve la ficha ${camino[j - 1].texto} (cuesta ${camino[j - 1].costo}). Costo acumulado: ${acum}.`
      : `Meta alcanzada: las ${caso.k} fichas forman una línea. Costo total ${acum} en ${camino.length} pasos.`;
  }
  function pintar(deslizar = false) {
    barra.max = maximo(); barra.value = posicion();
    if (modo === "exploracion") pintarExploracion(); else pintarSolucion(deslizar);
  }
  function cambiarModo(m) {
    detener(); modo = m;
    btnExp.classList.toggle("primario", m === "exploracion"); btnSol.classList.toggle("primario", m === "solucion");
    lista.hidden = m !== "solucion";
    for (const [c, etq] of [["exp", m === "exploracion" ? "Expandidos" : "Paso"], ["fro", m === "exploracion" ? "En la frontera" : "Pasos que faltan"], ["g", m === "exploracion" ? "Costo g del estado" : "Costo acumulado"], ["f", m === "exploracion" ? "f = g + h" : "Costo total"]])
      cont[c].nextSibling.textContent = etq;
    if (m === "solucion") { j = 0; } else { k = 0; }
    pintar();
  }
  function ir(v) {
    detener();
    const nuevo = Math.max(0, Math.min(maximo(), Math.round(v)));
    const adelanteUno = modo === "solucion" && nuevo === j + 1;
    if (modo === "exploracion") k = nuevo; else j = nuevo;
    pintar(adelanteUno);
  }
  function detener() { if (reloj) clearInterval(reloj); reloj = null; btnPlay.textContent = "▶ Reproducir"; }
  function alternar() {
    if (reloj) return detener();
    if (posicion() >= maximo()) { if (modo === "exploracion") k = 0; else j = 0; pintar(); }
    btnPlay.textContent = "⏸ Pausa";
    acumulado = 0;
    reloj = setInterval(() => {
      if (modo === "exploracion") {
        acumulado += EVENTOS_POR_SEG[vel] * 0.05;
        const salto = Math.floor(acumulado); acumulado -= salto;
        k = Math.min(M, k + Math.max(salto, 0)); pintar();
        if (k >= M) {                      // al terminar la exploración pasa sola a la solución
          detener();
          if (camino.length) setTimeout(() => { cambiarModo("solucion"); alternar(); }, G.reducir ? 0 : 700);
        }
      } else {                             // solución: un paso cada cierto tiempo según la velocidad
        acumulado += 50;
        if (acumulado < DURACION_PASO[vel]) return;
        acumulado = 0;
        j = Math.min(camino.length, j + 1); pintar(true);
        if (j >= camino.length) detener();
      }
    }, 50);
  }
  resumenSolucion.textContent = camino.length ? "" : "Este algoritmo no encontró solución.";
  btnExp.classList.add("primario");
  pintar();
  return { destruir() { detener(); document.removeEventListener("tema-cambiado", pintarBase); }, cambiarModo, alternar };
};
