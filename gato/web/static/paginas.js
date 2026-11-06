/* Las cinco pestañas de la interfaz. Cada una es una función `montar(panel)` que se ejecuta la
   primera vez que se abre. Usan G (app.js), los tableros (tablero.js), los gráficos (graficos.js),
   el árbol animado (arbol.js) y la animación de búsqueda (busqueda.js). */
"use strict";

const { h: el } = G;
const titulo = (t, p) => el("div", { class: "titulo-pagina" }, el("h2", {}, t), p ? el("p", {}, p) : null);
const metrica = (valor, etiqueta, extra) => el("div", { class: "metrica" + (extra ? " " + extra : "") }, el("div", { class: "valor mono" }, valor), el("div", { class: "etiqueta" }, etiqueta));
const campo = (etiqueta, control) => el("label", { class: "campo" }, etiqueta, control);
const opcion = (valor, texto, sel) => el("option", { value: valor, selected: sel }, texto);
const cargando = (msg) => el("div", { class: "cargando", role: "status" }, msg || "Calculando…");
const errorCaja = (msg) => el("div", { class: "aviso error", role: "alert" }, msg);

/* =============================================================== INICIO */
G.registrar("inicio", "Inicio", function (panel) {
  const tarjetaAlg = (nombre, tipo, texto) => el("div", { class: "tarjeta" }, el("span", { class: "chip" }, tipo), el("h3", { style: "margin-top:8px" }, nombre), el("p", { class: "suave", style: "margin:0" }, texto));
  panel.append(
    el("div", { class: "tarjeta heroe" },
      el("h2", {}, "Cinco algoritmos de búsqueda, un solo juego: el gato"),
      el("p", { style: "max-width:70ch" }, "Esta interfaz muestra cómo piensa cada algoritmo: el árbol de Minimax que crece y se poda, los estados que recorren DFS, BFS, UCS y A*, y las gráficas que los comparan."),
      el("div", { class: "grupo-botones" },
        el("button", { class: "boton primario", type: "button", onclick: () => G.ir("jugar") }, "Jugar contra la máquina"),
        el("button", { class: "boton", type: "button", onclick: () => G.ir("arbol") }, "Ver el árbol de Minimax"),
        el("button", { class: "boton", type: "button", onclick: () => G.ir("movil") }, "Resolver el Gato en movimiento"),
        el("button", { class: "boton", type: "button", onclick: () => G.ir("comparacion") }, "Comparar algoritmos"))),
    el("h3", { style: "margin:20px 0 10px" }, "Modo adversario: Gato contra la máquina"),
    el("div", { class: "rejilla tres" },
      tarjetaAlg("Minimax con poda alfa-beta", "dos jugadores", "La máquina (MAX) busca la jugada que más le conviene suponiendo que el rival (MIN) juega lo mejor posible. La poda descarta ramas que no pueden cambiar el resultado, con la misma jugada y muchos menos nodos."),
      tarjetaAlg("Profundidad límite y evaluación", "estimación", "Con límite de profundidad, la máquina no llega al final de la partida: valora los tableros con una función de evaluación (líneas abiertas y centro)."),
      tarjetaAlg("Torneo", "comparación", "Jugadores de distinta profundidad y evaluación juegan todos contra todos. El resultado está en la pestaña Comparación.")),
    el("h3", { style: "margin:20px 0 10px" }, "Modo de un agente: Gato en movimiento"),
    el("p", { class: "suave" }, "Un tablero con fichas X móviles y obstáculos O. Cada jugada mueve una X a una casilla vecina (recto cuesta 2, diagonal cuesta 3). La meta es dejar las X formando una línea."),
    el("div", { class: "rejilla tres" },
      tarjetaAlg("DFS", "no informada", "Pila. Se interna por una rama; encuentra una solución, no necesariamente corta ni barata."),
      tarjetaAlg("BFS", "no informada", "Cola. Recorre por niveles; halla la solución con menos pasos, pero no siempre la de menor costo."),
      tarjetaAlg("Costo uniforme", "no informada con costos", "Cola de prioridad por costo acumulado g. Siempre halla la solución de menor costo."),
      tarjetaAlg("A*", "informada", "Prioridad por f = g + h con una heurística propia (admisible y consistente). Mismo costo mínimo, muchos menos nodos.")),
    el("div", { class: "tarjeta", style: "margin-top:20px" },
      el("h3", {}, "Glosario"),
      el("dl", { class: "glosario" },
        el("dt", {}, "MAX / MIN"), el("dd", {}, "MAX es la máquina (maximiza el valor); MIN es el rival (lo minimiza)."),
        el("dt", {}, "α (alfa) y β (beta)"), el("dd", {}, "α es lo mejor que MAX ya tiene asegurado; β es lo mejor que MIN ya tiene asegurado. Si α ≥ β se poda."),
        el("dt", {}, "Frontera y explorados"), el("dd", {}, "La frontera son los estados descubiertos que aún no se expanden; los explorados ya se expandieron y no se repiten."),
        el("dt", {}, "g, h y f"), el("dd", {}, "g es el costo acumulado desde el inicio; h es la estimación de lo que falta; f = g + h."),
        el("dt", {}, "Admisible / consistente"), el("dd", {}, "Una heurística es admisible si nunca sobreestima el costo real, y consistente si h(s) ≤ costo de una jugada + h(s′)."))));
});

/* =============================================================== JUGAR */
G.registrar("jugar", "Jugar", function (panel) {
  let lineasGanadoras = [], t = Array(9).fill(" "), humano = "X", ia = "O", fin = false, ocupado = false;
  let ultimo = null, antes = null, calor = null, elegida = null;
  const cajaTablero = el("div"), tab = G.tablero3(cajaTablero);
  const estado = el("div", { class: "explicacion", role: "status", "aria-live": "polite" });
  const selFicha = el("select", {}, opcion("X", "X (empiezas tú)"), opcion("O", "O (empieza la máquina)"));
  const rango = el("input", { type: "range", min: 1, max: 9, value: 9, oninput: () => { etqProf.textContent = textoProf(); } });
  const textoProf = () => (+rango.value === 9 ? "9 (hasta el final)" : rango.value);
  const etqProf = el("strong", {}, "9 (hasta el final)");
  const selEval = el("select", {}, opcion("lineas", "Por líneas abiertas"), opcion("posicional", "Posicional (centro y esquinas)"));
  const razonamiento = el("div");

  function ganadorDe(tab9) {
    for (const l of lineasGanadoras) if (tab9[l[0]] !== " " && tab9[l[0]] === tab9[l[1]] && tab9[l[1]] === tab9[l[2]]) return { g: tab9[l[0]], linea: l };
    return null;
  }
  const turnoDe = (tab9) => (tab9.filter((c) => c === "X").length === tab9.filter((c) => c === "O").length ? "X" : "O");
  const profMax = () => (+rango.value === 9 ? null : +rango.value);

  function dibujar() {
    const ganador = ganadorDe(t);
    tab.render(t, { onClick: !fin && !ocupado && turnoDe(t) === humano ? clic : null, calor, elegida, linea: ganador && ganador.linea });
  }
  function terminar() {
    const g = ganadorDe(t);
    if (!g && t.includes(" ")) return false;
    fin = true;
    estado.textContent = !g ? "Empate: el mejor resultado posible contra Minimax."
      : g.g === humano ? (profMax() ? "¡Ganaste! Con profundidad límite la máquina no ve toda la partida." : "¡Ganaste! (Esto no debería pasar con profundidad completa.)")
      : "Ganó la máquina.";
    return true;
  }
  function clic(pos) {
    calor = null; elegida = null;
    t[pos - 1] = humano;
    dibujar();
    if (!terminar()) turnoMaquina(); else dibujar();
  }
  async function turnoMaquina() {
    ocupado = true; antes = t.slice();
    estado.textContent = "La máquina está pensando…"; dibujar();
    let r;
    try {
      r = await G.api.post("/api/gato/jugada", { tablero: t, prof_max: profMax(), evaluador: selEval.value });
    } catch (e) { estado.textContent = "Error: " + e.message; ocupado = false; return; }
    ultimo = { r, antes: antes.slice(), prof: profMax(), evaluador: selEval.value };
    calor = Object.fromEntries(Object.entries(r.valores).map(([k, v]) => [+k, v]));
    elegida = r.mejor;
    mostrarRazonamiento(r);
    dibujar();                                   // primero se ve el mapa de calor con la elegida…
    await G.esperar(G.reducir ? 0 : 1100);
    t[r.mejor - 1] = ia;                         // …y luego la máquina coloca su ficha
    ocupado = false;
    if (!terminar()) estado.textContent = `La máquina jugó en la casilla ${r.mejor}. Tu turno (${humano}).`;
    dibujar();
  }
  function explicar(r) {
    const v = r.valor, n = Object.keys(r.valores).length;
    if (typeof v === "number" && v >= 1) return `Veo una victoria forzada (valor ${G.fmt(v)}): jugando en ${r.mejor} gano haga lo que haga el rival.`;
    if (typeof v === "number" && v <= -1) return `Con juego perfecto del rival pierdo; elijo ${r.mejor}, la jugada que retrasa más la derrota (valor ${G.fmt(v)}).`;
    if (r.prof_max) return `A profundidad ${r.prof_max} no veo el final de la partida: estimo cada una de las ${n} jugadas con la función de evaluación y elijo la mayor (${G.fmt(v)} en la casilla ${r.mejor}).`;
    return `Con juego perfecto de ambos el resultado es un empate (valor 0). Elijo la casilla ${r.mejor} entre ${n} jugadas posibles.`;
  }
  function mostrarRazonamiento(r) {
    const mayor = Math.max(r.nodos_minimax, 1);
    G.vaciar(razonamiento).append(
      el("div", { class: "metricas" },
        metrica(G.miles(r.nodos_minimax), "nodos con Minimax"),
        metrica(G.miles(r.nodos_alfabeta), "nodos con poda α-β", "destacada"),
        metrica(r.ahorro.toFixed(1) + " %", "menos nodos con la poda"),
        metrica(r.ms.toFixed(1) + " ms", "tiempo (Minimax)")),
      el("div", { style: "margin-top:12px" },
        el("div", { class: "fila-barra" }, el("span", {}, "Sin poda"), el("div", { class: "barra" }, el("i", { style: `width:100%;background:var(--serie-2)` })), el("span", { class: "num" }, G.miles(r.nodos_minimax))),
        el("div", { class: "fila-barra" }, el("span", {}, "Con poda"), el("div", { class: "barra" }, el("i", { style: `width:${Math.max(1.5, 100 * r.nodos_alfabeta / mayor)}%` })), el("span", { class: "num" }, G.miles(r.nodos_alfabeta)))),
      el("p", { class: "suave pequeno" }, r.misma_jugada ? "✔ Las dos versiones eligen la misma jugada y el mismo valor." : "⚠ Las versiones difieren (no debería ocurrir)."),
      el("div", { class: "explicacion", "aria-live": "polite" }, explicar(r)),
      el("div", { style: "margin-top:12px" },
        el("button", { class: "boton primario", type: "button", onclick: () => G.ir("arbol", { tablero: ultimo.antes, prof: ultimo.prof, evaluador: ultimo.evaluador }) }, "Ver este razonamiento como árbol animado"),
        el("p", { class: "suave pequeno", style: "margin:6px 0 0" }, "El árbol se dibuja completo solo si es pequeño: funciona mejor con profundidad ≤ 3 o pocas casillas libres.")));
  }
  function nueva() {
    t = Array(9).fill(" "); humano = selFicha.value; ia = humano === "X" ? "O" : "X";
    fin = false; ocupado = false; calor = null; elegida = null; ultimo = null;
    G.vaciar(razonamiento).append(el("p", { class: "suave" }, "Aquí aparecerá el razonamiento de la máquina después de cada jugada suya: el valor de cada casilla (mapa de calor), cuántos nodos evaluó con y sin poda, y por qué eligió esa casilla."));
    estado.textContent = humano === "X" ? "Empiezas tú (X). Haz clic en una casilla." : "La máquina empieza.";
    dibujar();
    if (ia === "X") turnoMaquina();
  }
  panel.append(titulo("Jugar contra la máquina", "Juega al gato contra Minimax. Después de cada jugada de la máquina verás su razonamiento: cada casilla se colorea según su valor (verde = conviene, rojo = no conviene)."),
    el("div", { class: "controles" },
      campo("Tu ficha", selFicha),
      campo(el("span", {}, "Profundidad límite: ", etqProf), rango),
      campo("Función de evaluación", selEval),
      el("button", { class: "boton primario", type: "button", onclick: nueva }, "Nueva partida")),
    el("div", { class: "rejilla lado" },
      el("div", { class: "tarjeta" }, cajaTablero, el("div", { style: "margin-top:12px" }, estado),
        el("div", { class: "leyenda", style: "margin-top:10px" },
          el("span", {}, G.svg("svg", { width: 14, height: 14 }, G.svg("rect", { width: 14, height: 14, rx: 3, style: "fill:var(--bien);opacity:.6" })), "casilla que conviene"),
          el("span", {}, G.svg("svg", { width: 14, height: 14 }, G.svg("rect", { width: 14, height: 14, rx: 3, style: "fill:var(--mal);opacity:.6" })), "casilla que no conviene"),
          el("span", {}, G.svg("svg", { width: 14, height: 14 }, G.svg("rect", { width: 14, height: 14, rx: 3, fill: "none", style: "stroke:var(--acento);stroke-width:3" })), "la elegida"))),
      el("div", { class: "tarjeta" }, el("h3", {}, "Razonamiento de la máquina"), razonamiento)));
  G.catalogo().then((c) => { lineasGanadoras = c.lineas_ganadoras; nueva(); }).catch((e) => G.vaciar(panel).append(errorCaja(e.message)));
});

/* =============================================================== ÁRBOL DE MINIMAX */
G.registrar("arbol", "Árbol de Minimax", function (panel) {
  let cat = null, tabPersonal = Array(9).fill(" "), reproductor = null, enJuego = null;
  const selPos = el("select", { onchange: () => { editor.hidden = selPos.value !== "personal"; } });
  const selModo = el("select", {}, opcion("con", "Con poda α-β"), opcion("sin", "Sin poda (Minimax puro)"), opcion("comparar", "Comparar lado a lado"));
  const rango = el("input", { type: "range", min: 1, max: 9, value: 9, oninput: () => { etq.textContent = rango.value === "9" ? "9 (hasta el final)" : rango.value; } });
  const etq = el("strong", {}, "9 (hasta el final)");
  const selEval = el("select", {}, opcion("lineas", "Por líneas"), opcion("posicional", "Posicional"));
  const cajaEditor = el("div", { style: "max-width:150px" }), tabEditor = G.tablero3(cajaEditor);
  const editor = el("div", { hidden: true, class: "campo" }, "Haz clic para cambiar cada casilla (vacía → X → O):", cajaEditor);
  const pintarEditor = () => tabEditor.render(tabPersonal, { editable: true, onClick: (pos) => { const i = pos - 1; tabPersonal[i] = { " ": "X", X: "O", O: " " }[tabPersonal[i]]; pintarEditor(); } });
  pintarEditor();
  const salida = el("div");
  const accionar = el("button", { class: "boton primario", type: "button", onclick: () => dibujar() }, "Dibujar y animar");
  panel.append(titulo("Árbol de Minimax, paso a paso", "El árbol crece mientras el algoritmo explora. Los nodos MAX (▲) y MIN (▼) eligen el mayor o el menor valor de sus hijos; los valores suben hasta la raíz. Con poda, las ramas descartadas aparecen tachadas (✂)."),
    el("div", { class: "controles" }, campo("Posición", selPos), campo("Algoritmo", selModo), campo(el("span", {}, "Profundidad límite: ", etq), rango), campo("Evaluación", selEval), accionar), editor, salida);

  function posicionElegida() {
    if (selPos.value === "personal") return { tablero: tabPersonal };
    if (selPos.value === "juego" && enJuego) return enJuego;
    const e = cat.ejemplos.find((x) => x.id === selPos.value);
    return { tablero: e.tablero };
  }
  async function dibujar() {
    if (reproductor) reproductor.detener();
    G.vaciar(salida).append(cargando("Construyendo el árbol…"));
    accionar.disabled = true;
    const pos = posicionElegida(), prof = +rango.value === 9 ? null : +rango.value;
    const cuerpo = { tablero: pos.tablero, prof_max: prof, evaluador: selEval.value };
    try {
      const modo = selModo.value;
      const pedidos = modo === "comparar" ? [true, false] : [modo === "con"];
      const datos = await Promise.all(pedidos.map((poda) => G.api.post("/api/gato/arbol", { ...cuerpo, poda })));
      montar(datos, pedidos);
    } catch (e) { G.vaciar(salida).append(errorCaja(e.message)); }
    accionar.disabled = false;
  }
  function montar(datos, pedidos) {
    const arboles = datos.map((d) => G.ArbolAnimado(d));
    const cajaNodo = el("div", { style: "max-width:150px;margin:0 auto" }), tabNodo = G.tablero3(cajaNodo);
    const texto = el("div", { class: "explicacion", "aria-live": "polite" });
    const resumen = el("div", { class: "metricas" });
    const barraProg = el("div", { class: "barra" }, el("i", { style: "width:0" }));
    const info = el("div", { class: "pequeno suave" });
    const btnPlay = el("button", { class: "boton primario", type: "button", onclick: () => reproductor.alternar() }, "▶ Reproducir");
    const scrub = el("input", { type: "range", min: 0, max: reproductor ? 0 : 0, value: 0, style: "width:100%", "aria-label": "Posición en la animación", oninput: (e) => reproductor.ir(+e.target.value) });
    const vel = el("input", { type: "range", min: 0, max: 8, value: 3, "aria-label": "Velocidad", oninput: (e) => reproductor.velocidad(+e.target.value) });
    const zoom = el("input", { type: "range", min: 30, max: 160, value: Math.round(arboles[0].zoom * 100), "aria-label": "Zoom", oninput: (e) => arboles.forEach((a) => a.ponerZoom(e.target.value / 100)) });
    const boton = (txt, ayuda, f) => el("button", { class: "boton", type: "button", title: ayuda, "aria-label": ayuda, onclick: f }, txt);
    const controles = el("div", { class: "controles" },
      el("div", { class: "grupo-botones" }, boton("⏮", "Al inicio", () => reproductor.ir(0)), boton("◀", "Paso atrás", () => reproductor.mover(-1)), btnPlay, boton("▶", "Paso adelante", () => reproductor.mover(1)), boton("⏭", "Al final", () => reproductor.ir(reproductor.total))),
      campo("Velocidad", vel), campo("Zoom", zoom));
    const visores = arboles.map((a, i) => el("div", {}, datos.length > 1 ? el("h3", {}, pedidos[i] ? "Con poda α-β" : "Sin poda (Minimax)") : null, a.visor));
    const leyenda = el("div", { class: "leyenda", style: "margin:6px 0 10px" },
      ...[["MAX", "polygon", "7,0 14,13 0,13"], ["MIN", "polygon", "0,0 14,0 7,13"], ["HOJA", "rect"], ["CORTE", "polygon", "7,0 14,7 7,14 0,7"], ["PODA", "rect"]].map(([n, f, pts], i) =>
        el("span", {}, G.svg("svg", { width: 16, height: 16, viewBox: "-1 -1 16 16" }, f === "polygon" ? G.svg("polygon", { points: pts, fill: "none", style: `stroke:var(--${["max", "min", "hoja", "corte", "poda"][i]});stroke-width:2` })
          : G.svg("rect", { x: 1, y: 1, width: 12, height: 12, rx: 3, fill: "none", style: `stroke:var(--${i === 2 ? "hoja" : "poda"});stroke-width:2`, "stroke-dasharray": i === 4 ? "3 2" : "" })),
          { MAX: "MAX (la máquina)", MIN: "MIN (el rival)", HOJA: "hoja: partida terminada", CORTE: "corte por profundidad", PODA: "rama podada ✂" }[n])),
      el("span", {}, G.svg("svg", { width: 16, height: 16 }, G.svg("circle", { cx: 8, cy: 8, r: 6, fill: "none", style: "stroke:var(--acento);stroke-width:3" })), "nodo actual"),
      el("span", {}, G.svg("svg", { width: 16, height: 16 }, G.svg("circle", { cx: 8, cy: 8, r: 6, fill: "none", style: "stroke:var(--bien);stroke-width:3" })), "variante principal (al terminar)"));

    reproductor = G.Reproductor(arboles, (e) => {
      scrub.max = e.total; scrub.value = e.paso;
      btnPlay.textContent = e.reproduciendo ? "⏸ Pausa" : "▶ Reproducir";
      const r0 = e.resultados[0], d0 = datos[0];
      const lineas = e.resultados.map((r, i) => (r.evento ? (datos.length > 1 ? (pedidos[i] ? "Con poda: " : "Sin poda: ") : "") + r.evento.texto : null)).filter(Boolean);
      G.vaciar(texto).append(...(lineas.length ? lineas.map((l) => el("div", {}, l)) : ["Pulsa ▶ para empezar. Cada paso explica qué hace el algoritmo."]));
      const tableroNodo = r0.actual ? r0.actual.tablero : d0.nodos[0].tablero;
      tabNodo.render(tableroNodo);
      info.textContent = r0.actual ? `Nodo actual: ${r0.actual.tipo === "HOJA" ? "hoja" : r0.actual.tipo}${r0.actual.mov ? " · jugada " + r0.actual.mov : " · raíz"} · profundidad ${r0.actual.prof}${r0.alfaBeta && d0.poda ? ` · α=${G.fmt(r0.alfaBeta[0])}, β=${G.fmt(r0.alfaBeta[1])}` : ""}` : "";
      G.vaciar(resumen).append(...e.resultados.flatMap((r, i) => {
        const etiqueta = datos.length > 1 ? (pedidos[i] ? " (poda)" : " (sin poda)") : "";
        return [metrica(G.miles(r.evaluados), "nodos evaluados" + etiqueta), datos[i].poda ? metrica(r.podas, "podas realizadas") : null].filter(Boolean);
      }));
      const total = d0.total_sin_poda, ev = datos.find((d) => d.poda) ? e.resultados[datos.findIndex((d) => d.poda)].evaluados : e.resultados[0].evaluados;
      barraProg.firstChild.style.width = Math.min(100, (100 * ev) / total) + "%";
      if (e.paso === e.total) {
        const mm = datos.find((d) => !d.poda), ab = datos.find((d) => d.poda);
        const fila = (d) => `${d.poda ? "Con poda" : "Sin poda"}: ${G.miles(d.evaluados)} nodos`;
        texto.append(el("div", { style: "margin-top:8px;font-weight:700" }, `Resultado: mejor jugada = casilla ${datos[0].mejor}, valor ${G.fmt(datos[0].valor)}. ${datos.map(fila).join(" · ")}` +
          (ab ? ` · la poda evita ${(100 * (1 - ab.evaluados / ab.total_sin_poda)).toFixed(1)} % de los nodos.` : ".")));
      }
    });
    const infoNodo = el("div", { class: "tarjeta" }, el("h3", {}, "Nodo actual"), cajaNodo, el("div", { style: "margin:8px 0 12px" }, info),
      texto, el("div", { style: "margin-top:12px" }, resumen),
      el("div", { style: "margin-top:12px" }, el("div", { class: "pequeno suave" }, `Nodos evaluados frente al total sin poda (${G.miles(datos[0].total_sin_poda)})`), barraProg));
    const barraControl = el("div", { class: "tarjeta", style: "padding:12px 16px" }, controles, scrub);
    const comparando = datos.length > 1;
    G.vaciar(salida).append(comparando
      ? el("div", {}, el("div", { class: "rejilla lado" }, infoNodo, el("div", {}, barraControl, el("div", { style: "height:10px" }), leyenda)),
          el("div", { class: "rejilla dos", style: "margin-top:16px" }, ...visores))
      : el("div", { class: "rejilla lado" }, infoNodo, el("div", {}, barraControl, el("div", { style: "height:10px" }), leyenda, ...visores)));
    reproductor.ir(0);
  }
  document.addEventListener("keydown", (e) => {
    if (panel.hidden || !reproductor || /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) return;
    if (e.key === " ") { e.preventDefault(); reproductor.alternar(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); reproductor.mover(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); reproductor.mover(-1); }
  });
  G.catalogo().then((c) => {
    cat = c;
    c.ejemplos.forEach((x) => selPos.append(opcion(x.id, `Ejemplo ${x.id}: ${x.descripcion}`)));
    selPos.append(opcion("personal", "Posición personalizada"));
    dibujar();
  }).catch((e) => salida.append(errorCaja(e.message)));
  return {
    alActivar(datos) {                  // viene desde "Jugar" con la posición de la partida
      if (!datos || !cat) return;
      enJuego = datos;
      if (!selPos.querySelector('option[value="juego"]')) selPos.append(opcion("juego", "Posición de tu partida"));
      selPos.value = "juego"; editor.hidden = true;
      rango.value = datos.prof || 9; etq.textContent = rango.value === "9" ? "9 (hasta el final)" : rango.value;
      selEval.value = datos.evaluador || "lineas";
      dibujar();
    },
  };
});

/* =============================================================== GATO EN MOVIMIENTO */
G.registrar("movil", "Gato en movimiento", function (panel) {
  let cat = null, panelAnim = null;
  const sesion = new Map();            // "caso|algoritmo" -> métricas de las ejecuciones de esta sesión
  const selCaso = el("select", { onchange: previa }), selAlg = el("select", {});
  const cajaPrevia = el("div"), cajaAnim = el("div"), cajaMetricas = el("div"), cajaSesion = el("div");
  const boton = el("button", { class: "boton primario", type: "button", onclick: resolver }, "Resolver y animar");
  panel.append(titulo("Gato en movimiento: DFS, BFS, costo uniforme y A*", "Las fichas X se mueven (recto cuesta 2, diagonal cuesta 3) hasta formar una línea. Elige un caso y un algoritmo: verás qué estados explora, cuántos guarda en memoria y cómo se mueven las fichas por la solución."),
    el("div", { class: "controles" }, campo("Caso", selCaso), campo("Algoritmo", selAlg), boton), cajaMetricas, cajaAnim, cajaPrevia, cajaSesion);

  function previa() {
    G.vaciar(cajaPrevia);
    if (panelAnim) return;
    const caso = cat.casos.find((c) => c.id === selCaso.value), caja = el("div", { style: "max-width:360px" });
    const tb = G.tableroMovil(caja, caso, { entrada: true });
    tb.poner(caso.x_iniciales, { animar: false });
    if (caso.lineas.length <= 6) tb.lineasPosibles(caso.lineas);
    cajaPrevia.append(el("div", { class: "tarjeta" }, el("h3", {}, caso.nombre), el("p", { class: "suave" }, `Tablero ${caso.n}×${caso.n} · ${caso.k} fichas X · ${caso.o_fijas.length} obstáculo(s) O · ${caso.lineas.length} línea(s) posibles. Pulsa “Resolver y animar”.`), caja));
  }
  async function resolver() {
    if (panelAnim) { panelAnim.destruir(); panelAnim = null; }
    G.vaciar(cajaAnim); G.vaciar(cajaPrevia); G.vaciar(cajaMetricas).append(cargando("Resolviendo… (A* sobre el caso grande puede tardar unos segundos)"));
    boton.disabled = true;
    try {
      const datos = await G.api.post("/api/busqueda", { caso: selCaso.value, algoritmo: selAlg.value });
      const caso = cat.casos.find((c) => c.id === selCaso.value), m = datos.metricas;
      sesion.set(`${datos.caso}|${datos.algoritmo}`, { caso: caso.nombre, id: datos.caso, alg: datos.algoritmo, ...m });
      G.vaciar(cajaMetricas).append(el("div", { class: "metricas" },
        metrica(m.costo, "costo de la solución", "destacada"), metrica(m.pasos, "pasos"), metrica(G.miles(m.expandidos), "nodos expandidos"),
        metrica(G.miles(m.generados), "nodos generados"), metrica(G.miles(m.memoria_nodos), "nodos en memoria (máx.)"),
        metrica(G.kb(m.memoria_bytes), "memoria (pico Python)"), metrica(m.ms.toFixed(1) + " ms", "tiempo")));
      panelAnim = G.PanelBusqueda(cajaAnim, caso, datos);
      tablaSesion();
    } catch (e) { G.vaciar(cajaMetricas).append(errorCaja(e.message)); }
    boton.disabled = false;
  }
  function tablaSesion() {
    const filas = [...sesion.values()].sort((a, b) => a.id.localeCompare(b.id) || cat.algoritmos.indexOf(a.alg) - cat.algoritmos.indexOf(b.alg));
    const mejorPorCaso = {};
    for (const f of filas) mejorPorCaso[f.id] = Math.min(mejorPorCaso[f.id] ?? Infinity, f.costo);
    const nota = [];
    const bfs = sesion.get("2|BFS"), ucs = sesion.get("2|UCS");
    if (bfs && ucs) nota.push(el("div", { class: "aviso", style: "margin-bottom:10px" }, `En el caso 2, BFS halla la solución con menos pasos (${bfs.pasos}) pero su costo es ${bfs.costo}; UCS logra costo ${ucs.costo} con ${ucs.pasos} pasos. Minimizar pasos no es minimizar costo.`));
    G.vaciar(cajaSesion).append(el("div", { class: "tarjeta", style: "margin-top:16px" }, el("h3", {}, "Resultados de esta sesión"), el("p", { class: "suave pequeno" }, "Ejecuta varios algoritmos sobre el mismo caso para compararlos. En verde, el menor costo de cada caso."), ...nota,
      el("table", { class: "tabla-datos" }, el("thead", {}, el("tr", {}, ...["Caso", "Algoritmo", "Costo", "Pasos", "Expandidos", "Memoria (nodos)", "Tiempo (ms)"].map((x) => el("th", {}, x)))),
        el("tbody", {}, ...filas.map((f) => el("tr", { class: f.costo === mejorPorCaso[f.id] ? "mejor" : "" }, el("td", {}, f.caso), el("td", {}, f.alg), el("td", {}, f.costo), el("td", {}, f.pasos), el("td", {}, G.miles(f.expandidos)), el("td", {}, G.miles(f.memoria_nodos)), el("td", {}, f.ms.toFixed(1))))))));
  }
  G.catalogo().then((c) => {
    cat = c;
    c.casos.forEach((x) => selCaso.append(opcion(x.id, x.nombre)));
    c.algoritmos.forEach((a) => selAlg.append(opcion(a, a === "A* (h1)" ? "A* con heurística propia (h1)" : a === "A* (h2)" ? "A* con heurística simple (h2)" : a === "UCS" ? "Costo uniforme (UCS)" : a)));
    selAlg.value = "A* (h1)";
    previa();
  }).catch((e) => panel.append(errorCaja(e.message)));
});

/* =============================================================== COMPARACIÓN */
G.registrar("comparacion", "Comparación", function (panel) {
  const raiz = el("div"), METRICAS = {
    expandidos: { etq: "Nodos expandidos", dato: (r) => r.expandidos, formato: G.corto },
    ms: { etq: "Tiempo (ms)", dato: (r) => r.ms, formato: (v) => (v < 10 ? v.toFixed(1) : Math.round(v)) + "" },
    memoria: { etq: "Memoria pico (KB)", dato: (r) => Math.round(r.memoria_bytes / 1024), formato: G.corto },
    costo: { etq: "Costo de la solución", dato: (r) => r.costo, formato: (v) => v + "" },
    pasos: { etq: "Pasos de la solución", dato: (r) => r.pasos, formato: (v) => v + "" },
  };
  panel.append(titulo("Comparación de algoritmos", "Mismos casos, mismas métricas. Las gráficas se pueden descargar como imagen (PNG o SVG) o copiar como tabla Markdown para el informe y las diapositivas."), raiz);
  raiz.append(cargando("Midiendo los 5 algoritmos en los 4 casos… (tarda unos segundos la primera vez)"));
  Promise.all([G.api.get("/api/comparacion"), G.api.get("/api/poda")]).then(([comp, poda]) => {
    G.vaciar(raiz).append(seccionBusqueda(comp), seccionPesos(comp), seccionPoda(poda), seccionTorneo());
  }).catch((e) => G.vaciar(raiz).append(errorCaja(e.message)));

  function seccionBusqueda(comp) {
    const selMet = el("select", { onchange: () => refrescar() }, ...Object.entries(METRICAS).map(([k, m]) => opcion(k, m.etq)));
    const log = el("input", { type: "checkbox", id: "log-busq", onchange: () => refrescar() });
    const valores = () => comp.casos.map((c) => comp.competidores.map((n) => METRICAS[selMet.value].dato(c.resultados[n])));
    const markdown = () => G.aMarkdown(["Caso", ...comp.competidores], comp.casos.map((c, i) => [c.nombre, ...valores()[i].map(METRICAS[selMet.value].formato)]));
    const tarjeta = G.tarjetaGrafico("Búsqueda en el Gato en movimiento", "Cada grupo es un caso; cada barra, un algoritmo.", () =>
      G.barrasAgrupadas({ grupos: comp.casos.map((c) => c.nombre), series: comp.competidores, valores: valores(), formato: METRICAS[selMet.value].formato, log: log.checked, ejeY: METRICAS[selMet.value].etq }), markdown);
    const refrescar = () => tarjeta.actualizar();
    return el("section", { style: "margin-bottom:24px" }, el("h3", { style: "margin-bottom:8px" }, "1 · Algoritmos de búsqueda"),
      el("div", { class: "controles" }, campo("Métrica", selMet), el("label", { class: "check" }, log, "Escala logarítmica")), tarjeta,
      el("p", { class: "suave pequeno" }, "Lectura: DFS expande pocos nodos pero su solución es larga y cara (mira “Costo”); A* con h1 expande muchos menos nodos que UCS con el mismo costo, pero tarda más por lo caro de calcular la heurística."));
  }

  function seccionPesos(comp) {
    const criterios = [["costo", "Costo de la solución", 3, (r) => r.costo], ["expandidos", "Nodos expandidos", 1, (r) => r.expandidos], ["memoria", "Memoria (pico)", 1, (r) => r.memoria_bytes], ["tiempo", "Tiempo", 1, (r) => r.ms]];
    const pesos = Object.fromEntries(criterios.map(([k, , p]) => [k, p]));
    const entradas = [];                      // [input, etiqueta de valor, clave] para poder restablecer
    const deslizadores = criterios.map(([k, etq]) => {
      const valor = el("strong", {}, pesos[k]);
      const r = el("input", { type: "range", min: 0, max: 5, value: pesos[k], oninput: (e) => { pesos[k] = +e.target.value; valor.textContent = pesos[k]; tarjeta.actualizar(); resumen(); } });
      entradas.push([r, valor, k]);
      return campo(el("span", {}, etq, " ×", valor), r);
    });
    const restablecer = () => {
      criterios.forEach(([k, , p]) => (pesos[k] = p));
      entradas.forEach(([r, v, k]) => { r.value = pesos[k]; v.textContent = pesos[k]; });
      tarjeta.actualizar(); resumen();
    };
    const nombres = comp.competidores, n = nombres.length;
    const puntos = () => {                    // mismo cálculo que torneo.py: n-1-(rivales estrictamente mejores)
      const tot = Object.fromEntries(criterios.map(([k]) => [k, Object.fromEntries(nombres.map((x) => [x, 0]))]));
      for (const c of comp.casos) for (const [k, , , dato] of criterios) {
        const vals = Object.fromEntries(nombres.map((x) => [x, dato(c.resultados[x])]));
        for (const x of nombres) tot[k][x] += n - 1 - nombres.filter((y) => vals[y] < vals[x]).length;
      }
      return tot;
    };
    const filas = () => {
      const p = puntos();
      return nombres.map((x) => ({ nombre: x, partes: criterios.map(([k], i) => ({ valor: pesos[k] * p[k][x], serie: i })), total: criterios.reduce((s, [k]) => s + pesos[k] * p[k][x], 0) }))
        .sort((a, b) => b.total - a.total);
    };
    const maximo = () => Object.values(pesos).reduce((s, v) => s + v, 0) * (n - 1) * comp.casos.length;
    const campeon = el("div", { class: "explicacion", "aria-live": "polite" });
    const resumen = () => {
      const f = filas();
      const empate = f.filter((x) => x.total === f[0].total).map((x) => x.nombre);
      campeon.textContent = maximo() === 0 ? "Pon al menos un peso mayor que 0." : `Campeón con estos pesos: ${empate.join(" y ")} (${f[0].total} de ${maximo()} puntos). Mueve los deslizadores: el campeón depende de qué le importe más a quien elige.`;
    };
    const tarjeta = G.tarjetaGrafico("¿Quién gana? Depende de los pesos", "Cada criterio da puntos por caso (el mejor n−1, el peor 0); se suman multiplicados por su peso.", () => {
      const f = filas();
      return G.barrasApiladas({ filas: f.map(({ nombre, partes }) => ({ nombre, partes })), series: criterios.map(([, etq]) => etq), maximo: Math.max(1, maximo()), ejeX: "Puntos ponderados", resaltar: maximo() ? f[0].nombre : null });
    }, () => G.aMarkdown(["Competidor", ...criterios.map(([k, e]) => `${e} (×${pesos[k]})`), "Total"], filas().map((f) => [f.nombre, ...f.partes.map((p) => p.valor), f.total])));
    resumen();
    return el("section", { style: "margin-bottom:24px" }, el("h3", { style: "margin-bottom:8px" }, "2 · Competencia con pesos ajustables"),
      el("div", { class: "controles" }, ...deslizadores, el("button", { class: "boton", type: "button", onclick: restablecer }, "Restablecer")),
      campeon, el("div", { style: "height:10px" }), tarjeta);
  }

  function seccionPoda(poda) {
    const sel = el("select", { onchange: () => tarjeta.actualizar() }, ...poda.posiciones.map((p, i) => opcion(i, p.posicion)));
    const serie = () => poda.posiciones[+sel.value].serie;
    const tarjeta = G.tarjetaGrafico("Ahorro de la poda alfa-beta", "Nodos evaluados según la profundidad límite (escala logarítmica).", () =>
      G.lineas({ x: serie().map((s) => s.prof), series: [{ nombre: "Minimax", valores: serie().map((s) => s.minimax) }, { nombre: "Alfa-beta", valores: serie().map((s) => s.alfabeta) }], log: true, ejeX: "Profundidad límite", ejeY: "Nodos evaluados" }),
      () => G.aMarkdown(["Profundidad", "Minimax", "Alfa-beta", "Ahorro"], serie().map((s) => [s.prof, G.miles(s.minimax), G.miles(s.alfabeta), s.ahorro + " %"])));
    const tabla = el("div");
    const pintarTabla = () => G.vaciar(tabla).append(el("table", { class: "tabla-datos" }, el("thead", {}, el("tr", {}, ...["Profundidad", "Minimax", "Alfa-beta", "Ahorro"].map((x) => el("th", {}, x)))),
      el("tbody", {}, ...serie().map((s) => el("tr", {}, el("td", {}, s.prof), el("td", {}, G.miles(s.minimax)), el("td", {}, G.miles(s.alfabeta)), el("td", {}, s.ahorro.toFixed(1) + " %"))))));
    sel.addEventListener("change", pintarTabla); pintarTabla();
    return el("section", { style: "margin-bottom:24px" }, el("h3", { style: "margin-bottom:8px" }, "3 · Minimax con y sin poda"),
      el("div", { class: "controles" }, campo("Posición", sel)), el("div", { class: "rejilla" }, tarjeta, el("div", { class: "tarjeta" }, tabla, el("p", { class: "suave pequeno" }, "La poda no cambia la jugada ni el valor: solo evita evaluar ramas que no pueden influir. El ahorro crece con la profundidad."))));
  }

  function seccionTorneo() {
    const sel = el("select", {}, opcion(5, "5 aperturas por pareja"), opcion(10, "10 aperturas por pareja", true), opcion(20, "20 aperturas por pareja"));
    const salida = el("div");
    const boton = el("button", { class: "boton primario", type: "button", onclick: correr }, "Correr el torneo");
    async function correr() {
      boton.disabled = true; G.vaciar(salida).append(cargando("Jugando todas las partidas…"));
      try { pintar(await G.api.get("/api/torneo?partidas=" + sel.value)); } catch (e) { G.vaciar(salida).append(errorCaja(e.message)); }
      boton.disabled = false;
    }
    function pintar(t) {
      const filas = t.ranking.map((r) => ({ nombre: r.nombre, partes: [{ valor: r.ganadas, serie: 0 }, { valor: r.empatadas / 2, serie: 1 }] }));
      const grafico = G.tarjetaGrafico("Ranking del torneo de gato", "Puntos: victoria 1, empate ½. Cada jugador juega " + t.partidas_por_pareja * (t.ranking.length - 1) + " partidas.", () =>
        G.barrasApiladas({ filas, series: ["Victorias", "Empates (½ punto)"], maximo: Math.max(...t.ranking.map((r) => r.puntos)) * 1.05, ejeX: "Puntos" }),
        () => G.aMarkdown(["#", "Jugador", "Ganadas", "Empatadas", "Perdidas", "Puntos"], t.ranking.map((r, i) => [i + 1, r.nombre, r.ganadas, r.empatadas, r.perdidas, r.puntos])));
      const color = (v) => (v === null ? "transparent" : `color-mix(in srgb, var(${v >= 0.5 ? "--bien" : "--mal"}) ${Math.round(Math.abs(v - 0.5) * 2 * 70)}%, var(--superficie))`);
      const matriz = el("table", { class: "tabla-datos" }, el("thead", {}, el("tr", {}, el("th", {}, "Fila contra columna →"), ...t.orden.map((_, i) => el("th", { class: "celda-matriz" }, i + 1)))),
        el("tbody", {}, ...t.orden.map((n, i) => el("tr", {}, el("td", {}, `${i + 1} · ${n}`), ...t.matriz[i].map((v) => el("td", { class: "celda-matriz", style: `background:${color(v)}` }, v === null ? "—" : Math.round(v * 100) + " %"))))));
      G.vaciar(salida).append(el("div", { class: "rejilla" }, grafico, el("div", { class: "tarjeta" }, el("h3", {}, "Matriz de resultados"), el("p", { class: "suave pequeno" }, "Porcentaje de puntos que obtiene el jugador de la fila contra el de la columna (verde = ganó más, rojo = perdió más)."), matriz)),
        el("p", { class: "suave pequeno" }, "Cada pareja juega aperturas aleatorias de 2 jugadas, cada una con ambos colores. El jugador perfecto pierde algunas partidas porque a veces la apertura (que no juega nadie) ya le dejó una posición perdida. Con pocas partidas, diferencias pequeñas entre jugadores están dentro del ruido."));
    }
    return el("section", {}, el("h3", { style: "margin-bottom:8px" }, "4 · Torneo de gato (todos contra todos)"),
      el("div", { class: "controles" }, campo("Tamaño del torneo", sel), boton), salida);
  }
});
