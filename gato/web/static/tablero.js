/* Tableros en SVG: el gato normal (3×3, clicable, con mapa de calor) y el Gato en movimiento (N×N,
   fichas que se deslizan). */
"use strict";

/* ---------------------------------------------------------------- Gato normal 3×3 */
G.tablero3 = function (contenedor) {
  const svg = G.svg("svg", { viewBox: "0 0 300 300", class: "tablero-svg", role: "group", "aria-label": "Tablero de gato" });
  contenedor.append(svg);
  let previo = Array(9).fill(" ");

  /* render(tablero, op): tablero = lista de 9 ('X','O',' ').
     op.onClick(pos 1-9)  hace clicables las casillas libres (todas si op.editable)
     op.calor {pos: valor} pinta cada casilla libre según su valor (verde bueno, rojo malo)
     op.elegida (pos)      resalta la casilla elegida; op.linea [i,j,k] marca la línea ganadora */
  function render(tablero, op = {}) {
    G.vaciar(svg);
    const valores = op.calor ? Object.values(op.calor).filter((v) => typeof v === "number") : [];
    const escala = valores.length ? Math.max(0.0001, ...valores.map(Math.abs)) : 1;
    tablero.forEach((c, i) => {
      const pos = i + 1, x = (i % 3) * 100, y = Math.floor(i / 3) * 100;
      const libre = c === " ", clicable = op.onClick && (libre || op.editable);
      const g = G.svg("g", {
        class: "celda" + (clicable ? " celda-click" : "") + (op.elegida === pos ? " celda-elegida" : ""),
        transform: `translate(${x} ${y})`,
        role: clicable ? "button" : "img", tabindex: clicable ? 0 : null,
        "aria-label": `Casilla ${pos}, ${libre ? "libre" : c}${op.calor && op.calor[pos] !== undefined ? ", valor " + G.fmt(op.calor[pos]) : ""}`,
      });
      g.append(G.svg("rect", { class: "celda-fondo", x: 3, y: 3, width: 94, height: 94, rx: 10 }));
      if (libre && op.calor && typeof op.calor[pos] === "number") {
        const t = op.calor[pos] / escala;
        g.append(G.svg("rect", { x: 3, y: 3, width: 94, height: 94, rx: 10,
          style: `fill: var(${t >= 0 ? "--bien" : "--mal"}); opacity: ${(0.12 + 0.5 * Math.abs(t)).toFixed(2)}` }));
        g.append(G.svg("text", { class: "valor-celda", x: 50, y: 56, "text-anchor": "middle", fill: "currentColor", style: "fill: var(--texto)" }, G.fmt(op.calor[pos])));
        g.append(G.svg("text", { class: "num-celda", x: 10, y: 20 }, pos));
      } else if (libre) {
        g.append(G.svg("text", { class: "num-celda", x: 50, y: 60, "text-anchor": "middle", style: "font-size:22px" }, pos));
      } else {
        const nueva = previo[i] !== c && !G.reducir;
        const pieza = G.svg("g", { class: nueva ? "pieza-nueva" : "" });
        if (c === "X") {
          pieza.append(G.svg("line", { class: "trazo trazo-x", x1: 24, y1: 24, x2: 76, y2: 76, "stroke-width": 11, "stroke-linecap": "round" }),
                       G.svg("line", { class: "trazo trazo-x", x1: 76, y1: 24, x2: 24, y2: 76, "stroke-width": 11, "stroke-linecap": "round" }));
        } else {
          pieza.append(G.svg("circle", { class: "trazo trazo-o", cx: 50, cy: 50, r: 27, fill: "none", "stroke-width": 11 }));
        }
        g.append(pieza);
      }
      if (clicable) {
        g.addEventListener("click", () => op.onClick(pos));
        g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); op.onClick(pos); } });
      }
      svg.append(g);
    });
    // Líneas del tablero encima, para que se vea la cuadrícula aunque haya mapa de calor.
    if (op.linea) {
      const c = (i) => [(i % 3) * 100 + 50, Math.floor(i / 3) * 100 + 50];
      const [a, b] = [c(op.linea[0]), c(op.linea[2])];
      svg.append(G.svg("line", { class: "linea-ganadora", x1: a[0], y1: a[1], x2: b[0], y2: b[1] }));
    }
    previo = tablero.slice();
  }
  return { svg, render };
};

/* ---------------------------------------------------------------- Gato en movimiento N×N */
/* Se dibuja como un gato: rejilla "#", fichas X con el mismo trazo que en el modo Jugar, obstáculos
   O como anillos y, al llegar a la meta, la línea ganadora trazada. Además muestra lo que lo
   distingue de un puzzle: el costo de cada movimiento (recto 2, diagonal 3) y las líneas meta posibles. */
G.tableroMovil = function (contenedor, caso, { entrada = false } = {}) {
  const n = caso.n, lado = 300 / n, brazo = lado * 0.27, grosor = Math.max(5, lado * 0.12);
  const svg = G.svg("svg", { viewBox: "0 0 300 300", class: "tablero-svg", role: "img",
    "aria-label": `Tablero ${n} por ${n} con ${caso.k} fichas X y ${caso.o_fijas.length} obstáculos` });
  contenedor.append(svg);
  const centro = (i) => ({ x: (i % n) * lado + lado / 2, y: Math.floor(i / n) * lado + lado / 2 });
  const capas = Object.fromEntries(["calor", "lineasMeta", "meta", "flecha", "fichas", "ganadora", "insignia"].map((k) => [k, G.svg("g")]));

  svg.append(G.svg("rect", { class: "celda-fondo", x: 2, y: 2, width: 296, height: 296, rx: 12 }));
  for (let i = 0; i < n * n; i++) {                      // numeración pequeña de las casillas libres
    if (caso.o_fijas.includes(i)) continue;
    svg.append(G.svg("text", { class: "num-celda", x: (i % n) * lado + 13, y: Math.floor(i / n) * lado + 19, style: `font-size:${Math.max(9, lado / 6.5)}px` }, i + 1));
  }
  svg.append(capas.calor, capas.lineasMeta, capas.meta);
  for (let k = 1; k < n; k++) {                          // la rejilla del gato (#)
    svg.append(G.svg("line", { class: "rejilla-gato", x1: k * lado, y1: 10, x2: k * lado, y2: 290 }),
               G.svg("line", { class: "rejilla-gato", x1: 10, y1: k * lado, x2: 290, y2: k * lado }));
  }
  for (const i of caso.o_fijas) {                        // obstáculos: O fija (anillo azul)
    const { x, y } = centro(i);
    svg.append(G.svg("circle", { class: "trazo-o obstaculo-anillo", cx: x, cy: y, r: lado * 0.28, fill: "none", "stroke-width": grosor }));
  }
  svg.append(capas.flecha, capas.fichas, capas.ganadora, capas.insignia);

  const fichas = [];      // { el, celda }: un elemento por ficha; se reasignan para deslizarse
  for (let k = 0; k < caso.k; k++) {
    const el = G.svg("g", { class: "ficha-movil" + (entrada && !G.reducir ? " pieza-nueva" : "") },
      G.svg("line", { class: "trazo trazo-x", x1: -brazo, y1: -brazo, x2: brazo, y2: brazo, "stroke-width": grosor, "stroke-linecap": "round" }),
      G.svg("line", { class: "trazo trazo-x", x1: brazo, y1: -brazo, x2: -brazo, y2: brazo, "stroke-width": grosor, "stroke-linecap": "round" }));
    capas.fichas.append(el);
    fichas.push({ el, celda: -1 });
  }
  if (entrada) setTimeout(() => fichas.forEach((f) => f.el.classList.remove("pieza-nueva")), 700);
  function colocar(f, celda) {
    f.celda = celda;
    const { x, y } = centro(celda);
    f.el.style.transform = `translate(${x}px, ${y}px)`;
  }
  const extremos = (celdas) => { const o = [...celdas].sort((a, b) => a - b); return [centro(o[0]), centro(o[o.length - 1])]; };

  return {
    svg,
    /* Pone las fichas en `estado` (lista de casillas). Las que ya estaban quietas no se mueven; las
       demás se reasignan a las casillas libres (así se ve el deslizamiento). */
    poner(estado, { animar = true } = {}) {
      svg.classList.toggle("sin-transicion", !animar || G.reducir);
      const destino = new Set(estado);
      const sobran = fichas.filter((f) => !destino.has(f.celda));
      const ocupadas = new Set(fichas.filter((f) => destino.has(f.celda)).map((f) => f.celda));
      const faltan = estado.filter((c) => !ocupadas.has(c));
      sobran.forEach((f, i) => colocar(f, faltan[i]));
    },
    /* Mueve la ficha de `origen` a `destino` conservando su identidad (deslizamiento exacto). */
    mover(origen, destino) {
      const f = fichas.find((x) => x.celda === origen);
      svg.classList.remove("sin-transicion");
      if (f) colocar(f, destino);
    },
    /* Mapa de calor: counts[i] = veces que la casilla i estuvo ocupada en los estados expandidos. */
    calor(counts) {
      G.vaciar(capas.calor);
      const max = Math.max(1, ...counts);
      counts.forEach((c, i) => {
        if (!c || caso.o_fijas.includes(i)) return;
        capas.calor.append(G.svg("rect", { x: (i % n) * lado + 4, y: Math.floor(i / n) * lado + 4, width: lado - 8, height: lado - 8, rx: 8,
          style: `fill: var(--acento); opacity: ${(0.08 + 0.55 * c / max).toFixed(2)}` }));
      });
    },
    /* Bandas tenues sobre cada línea que sirve de meta; donde varias se cruzan se ve más oscuro. */
    lineasPosibles(lineas) {
      G.vaciar(capas.lineasMeta);
      for (const l of lineas || []) {
        const [a, b] = extremos(l);
        capas.lineasMeta.append(G.svg("line", { class: "linea-meta-posible", x1: a.x, y1: a.y, x2: b.x, y2: b.y, "stroke-width": lado * 0.62 }));
      }
    },
    /* Marca con borde discontinuo las casillas de una línea (la meta alcanzada). */
    meta(celdas) {
      G.vaciar(capas.meta);
      for (const i of celdas || []) capas.meta.append(G.svg("rect", { class: "destino-meta", x: (i % n) * lado + 6, y: Math.floor(i / n) * lado + 6, width: lado - 12, height: lado - 12, rx: 8 }));
    },
    /* Traza la línea ganadora sobre las casillas de la meta (como al ganar en el gato). */
    linea(celdas) {
      G.vaciar(capas.ganadora);
      if (!celdas) return;
      const [a, b] = extremos(celdas);
      capas.ganadora.append(G.svg("line", { class: "linea-ganadora", x1: a.x, y1: a.y, x2: b.x, y2: b.y, "stroke-width": Math.max(6, lado * 0.1) }));
    },
    /* Flecha del movimiento con su costo: continua si es recto (+2), discontinua si es diagonal (+3). */
    movimiento(origen, destino, costo) {
      G.vaciar(capas.flecha); G.vaciar(capas.insignia);
      if (origen === null || origen === undefined) return;
      const a = centro(origen), b = centro(destino), d = Math.hypot(b.x - a.x, b.y - a.y), ux = (b.x - a.x) / d, uy = (b.y - a.y) / d;
      const fin = { x: b.x - ux * lado * 0.26, y: b.y - uy * lado * 0.26 }, ini = { x: a.x + ux * lado * 0.26, y: a.y + uy * lado * 0.26 };
      const cab = lado * 0.14;
      capas.flecha.append(
        G.svg("line", { class: "flecha-mov" + (costo === 3 ? " diagonal" : ""), x1: ini.x, y1: ini.y, x2: fin.x, y2: fin.y, "stroke-width": Math.max(3, lado * 0.05) }),
        G.svg("polygon", { class: "flecha-cabeza", points: `${fin.x},${fin.y} ${fin.x - ux * cab - uy * cab * 0.7},${fin.y - uy * cab + ux * cab * 0.7} ${fin.x - ux * cab + uy * cab * 0.7},${fin.y - uy * cab - ux * cab * 0.7}` }));
      const mx = (ini.x + fin.x) / 2 - uy * lado * 0.3, my = (ini.y + fin.y) / 2 + ux * lado * 0.3, w = lado * 0.5, alto = lado * 0.3;   // la insignia va al costado de la flecha
      capas.insignia.append(G.svg("g", { class: "insignia-costo", transform: `translate(${mx} ${my})` },
        G.svg("rect", { x: -w / 2, y: -alto / 2, width: w, height: alto, rx: alto / 2 }),
        G.svg("text", { x: 0, y: 1, style: `font-size:${Math.max(10, lado * 0.2)}px` }, "+" + costo)));
    },
    sinMovimiento() { G.vaciar(capas.flecha); G.vaciar(capas.insignia); },
  };
};
