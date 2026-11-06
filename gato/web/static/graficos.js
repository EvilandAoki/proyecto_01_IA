/* Gráficos en SVG hechos a mano (sin librerías) y utilidades para exportarlos.
   Los colores se resuelven al dibujar (G.tema) para que el SVG exportado sea autónomo. */
"use strict";

const FUENTE = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";

G.corto = function (n) {                      // 1.234 -> "1.234"; 12.345 -> "12 k"; 1.250.000 -> "1,25 M"
  if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace(".", ",") + " M";
  if (n >= 1e4) return Math.round(n / 1e3) + " k";
  return Number.isInteger(n) ? G.miles(n) : n.toFixed(1).replace(".", ",");
};

function escalaNice(max) {                    // máximo "redondo" y paso para el eje lineal
  const paso0 = max / 5, mag = Math.pow(10, Math.floor(Math.log10(paso0 || 1)));
  const paso = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => p >= paso0) || mag;
  return { tope: Math.ceil(max / paso) * paso, paso };
}
function texto(atrib, contenido) { return G.svg("text", { "font-family": FUENTE, ...atrib }, contenido); }

/* ---------------------------------------------------------------- barras agrupadas */
/* opc: { grupos:[...], series:[...], valores[g][s], formato(v), log:boolean, ejeY:string } */
G.barrasAgrupadas = function (opc) {
  const t = G.tema(), W = 780, H = 380, m = { i: 70, d: 12, s: 44, b: 66 };
  const svg = G.svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opc.ejeY });
  const todos = opc.valores.flat().filter((v) => v !== null && v !== undefined);
  const maxV = Math.max(...todos, 1);
  let y;                                       // valor -> coordenada
  const alto = H - m.s - m.b;
  const ticks = [];
  if (opc.log) {
    const top = Math.ceil(Math.log10(maxV * 1.05)), min = 0;
    y = (v) => m.s + alto - (Math.log10(Math.max(v, 1)) - min) / (top - min || 1) * alto;
    for (let p = 0; p <= top; p++) ticks.push(Math.pow(10, p));
  } else {
    const { tope, paso } = escalaNice(maxV);
    y = (v) => m.s + alto - (v / tope) * alto;
    for (let v = 0; v <= tope + 1e-9; v += paso) ticks.push(v);
  }
  svg.append(G.svg("rect", { width: W, height: H, fill: t.fondo }));
  for (const v of ticks) {
    svg.append(G.svg("line", { x1: m.i, x2: W - m.d, y1: y(v), y2: y(v), stroke: t.borde, "stroke-width": 1 }),
               texto({ x: m.i - 8, y: y(v) + 4, "text-anchor": "end", "font-size": 11, fill: t.suave }, G.corto(v)));
  }
  svg.append(texto({ x: 14, y: m.s + alto / 2, "font-size": 12, fill: t.suave, "text-anchor": "middle",
    transform: `rotate(-90 14 ${m.s + alto / 2})` }, opc.ejeY + (opc.log ? " (escala log)" : "")));
  const ancho = W - m.i - m.d, anchoG = ancho / opc.grupos.length, nS = opc.series.length;
  const anchoB = Math.min(34, (anchoG * 0.8) / nS);
  opc.grupos.forEach((g, gi) => {
    const x0 = m.i + gi * anchoG + (anchoG - anchoB * nS) / 2;
    opc.series.forEach((s, si) => {
      const v = opc.valores[gi][si];
      if (v === null || v === undefined) return;
      const top = y(v), x = x0 + si * anchoB;
      const barra = G.svg("rect", { class: "barra-g", x: x + 1, y: top, width: anchoB - 2, height: Math.max(1.5, m.s + alto - top), fill: t.series[si % 5], rx: 3,
        style: `animation-delay:${si * 40}ms` }, G.svg("title", {}, `${s} — ${g}: ${(opc.formato || G.corto)(v)}`));
      svg.append(barra, texto({ x: x + anchoB / 2, y: top - 4, "text-anchor": "middle", "font-size": 10, fill: t.texto, "font-weight": 600 }, (opc.formato || G.corto)(v)));
    });
    // Nombre del grupo (puede ser largo: se parte en dos líneas)
    const partes = g.length > 24 ? [g.slice(0, g.lastIndexOf(" ", 24)), g.slice(g.lastIndexOf(" ", 24) + 1)] : [g];
    partes.forEach((p, k) => svg.append(texto({ x: m.i + gi * anchoG + anchoG / 2, y: H - m.b + 18 + k * 14, "text-anchor": "middle", "font-size": 12, fill: t.texto }, p)));
  });
  leyenda(svg, opc.series, t, m.i, 16);
  return svg;
};

function leyenda(svg, series, t, x0, y0) {
  let x = x0;
  series.forEach((s, i) => {
    svg.append(G.svg("rect", { x, y: y0 - 10, width: 13, height: 13, rx: 3, fill: t.series[i % 5] }),
               texto({ x: x + 19, y: y0 + 1, "font-size": 12, fill: t.texto }, s));
    x += 19 + s.length * 7 + 22;
  });
}

/* ---------------------------------------------------------------- líneas */
/* opc: { x:[...], series:[{nombre, valores[]}], log, ejeX, ejeY, formato } */
G.lineas = function (opc) {
  const t = G.tema(), W = 780, H = 340, m = { i: 70, d: 20, s: 44, b: 52 };
  const svg = G.svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opc.ejeY });
  const maxV = Math.max(...opc.series.flatMap((s) => s.valores), 1);
  const alto = H - m.s - m.b, ancho = W - m.i - m.d, ticks = [];
  let y;
  if (opc.log) {
    const top = Math.ceil(Math.log10(maxV * 1.05));
    y = (v) => m.s + alto - (Math.log10(Math.max(v, 1)) / (top || 1)) * alto;
    for (let p = 0; p <= top; p++) ticks.push(Math.pow(10, p));
  } else {
    const { tope, paso } = escalaNice(maxV);
    y = (v) => m.s + alto - (v / tope) * alto;
    for (let v = 0; v <= tope + 1e-9; v += paso) ticks.push(v);
  }
  const x = (i) => m.i + (opc.x.length === 1 ? ancho / 2 : (i / (opc.x.length - 1)) * ancho);
  svg.append(G.svg("rect", { width: W, height: H, fill: t.fondo }));
  for (const v of ticks) {
    svg.append(G.svg("line", { x1: m.i, x2: W - m.d, y1: y(v), y2: y(v), stroke: t.borde }),
               texto({ x: m.i - 8, y: y(v) + 4, "text-anchor": "end", "font-size": 11, fill: t.suave }, G.corto(v)));
  }
  opc.x.forEach((v, i) => svg.append(texto({ x: x(i), y: H - m.b + 18, "text-anchor": "middle", "font-size": 12, fill: t.texto }, v)));
  svg.append(texto({ x: m.i + ancho / 2, y: H - 10, "text-anchor": "middle", "font-size": 12, fill: t.suave }, opc.ejeX),
             texto({ x: 14, y: m.s + alto / 2, "font-size": 12, fill: t.suave, "text-anchor": "middle", transform: `rotate(-90 14 ${m.s + alto / 2})` }, opc.ejeY + (opc.log ? " (escala log)" : "")));
  opc.series.forEach((s, si) => {
    const color = t.series[si % 5];
    const d = s.valores.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(" ");
    svg.append(G.svg("path", { d, fill: "none", stroke: color, "stroke-width": 3, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    s.valores.forEach((v, i) => {
      const marca = si % 2 === 0 ? G.svg("circle", { cx: x(i), cy: y(v), r: 5, fill: color, stroke: t.fondo, "stroke-width": 2 })
                                 : G.svg("rect", { x: x(i) - 5, y: y(v) - 5, width: 10, height: 10, fill: color, stroke: t.fondo, "stroke-width": 2 });
      marca.append(G.svg("title", {}, `${s.nombre}, profundidad ${opc.x[i]}: ${G.miles(v)} nodos`));
      svg.append(marca);
    });
  });
  leyenda(svg, opc.series.map((s) => s.nombre), t, m.i, 16);
  return svg;
};

/* ---------------------------------------------------------------- barras horizontales apiladas */
/* opc: { filas:[{nombre, partes:[{valor, serie}]}], series:[...], maximo, ejeX, resaltar:nombre } */
G.barrasApiladas = function (opc) {
  const t = G.tema(), W = 780, fila = 40, m = { i: 120, d: 70, s: 40, b: 36 }, H = m.s + fila * opc.filas.length + m.b;
  const svg = G.svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opc.ejeX });
  svg.append(G.svg("rect", { width: W, height: H, fill: t.fondo }));
  const ancho = W - m.i - m.d, x = (v) => (v / (opc.maximo || 1)) * ancho;
  opc.filas.forEach((f, i) => {
    const y0 = m.s + i * fila;
    svg.append(texto({ x: m.i - 10, y: y0 + fila / 2 + 4, "text-anchor": "end", "font-size": 13, fill: t.texto, "font-weight": f.nombre === opc.resaltar ? 800 : 500 }, (f.nombre === opc.resaltar ? "🏆 " : "") + f.nombre));
    let acumulado = 0;
    f.partes.forEach((p) => {
      if (p.valor <= 0) return;
      svg.append(G.svg("rect", { class: "barra-h", x: m.i + x(acumulado), y: y0 + 6, width: Math.max(0, x(p.valor) - 1), height: fila - 12, fill: t.series[p.serie % 5], rx: 2 },
        G.svg("title", {}, `${f.nombre} — ${opc.series[p.serie]}: ${p.valor}`)));
      acumulado += p.valor;
    });
    svg.append(texto({ x: m.i + x(acumulado) + 8, y: y0 + fila / 2 + 4, "font-size": 13, fill: t.texto, "font-weight": 700 }, acumulado));
  });
  svg.append(G.svg("line", { x1: m.i, x2: m.i, y1: m.s - 4, y2: H - m.b + 4, stroke: t.suave }));
  leyenda(svg, opc.series, t, m.i, 18);
  svg.append(texto({ x: m.i + ancho / 2, y: H - 10, "text-anchor": "middle", "font-size": 12, fill: t.suave }, opc.ejeX));
  return svg;
};

/* ---------------------------------------------------------------- exportar y copiar */
G.svgATexto = function (svg) {
  const copia = svg.cloneNode(true);
  const vb = svg.viewBox.baseVal;
  copia.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  copia.setAttribute("width", vb.width); copia.setAttribute("height", vb.height);
  // Las animaciones de entrada no existen fuera de la página: se deja la barra en su tamaño final.
  copia.querySelectorAll(".barra-g,.barra-h").forEach((e) => e.removeAttribute("style"));
  return new XMLSerializer().serializeToString(copia);
};
function descargar(blob, nombre) {
  const url = URL.createObjectURL(blob);
  const a = G.h("a", { href: url, download: nombre });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
G.exportarSVG = (svg, nombre) => descargar(new Blob([G.svgATexto(svg)], { type: "image/svg+xml" }), nombre + ".svg");
G.exportarPNG = function (svg, nombre) {
  const vb = svg.viewBox.baseVal, esc = 2;
  const img = new Image();
  img.onload = () => {
    const lienzo = G.h("canvas", { width: vb.width * esc, height: vb.height * esc });
    lienzo.getContext("2d").drawImage(img, 0, 0, vb.width * esc, vb.height * esc);
    lienzo.toBlob((b) => b ? descargar(b, nombre + ".png") : G.aviso("No se pudo crear la imagen."));
  };
  img.onerror = () => G.aviso("No se pudo crear la imagen.");
  img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(G.svgATexto(svg));
};
G.aMarkdown = (cabeceras, filas) =>
  "| " + cabeceras.join(" | ") + " |\n|" + cabeceras.map((_, i) => (i ? "---:" : "---")).join("|") + "|\n" + filas.map((f) => "| " + f.join(" | ") + " |").join("\n") + "\n";
G.copiar = async function (txt) {
  try { await navigator.clipboard.writeText(txt); G.aviso("Tabla copiada en formato Markdown."); }
  catch (e) {
    const ta = G.h("textarea", { style: "position:fixed;left:-999px" }, txt);
    document.body.append(ta); ta.select();
    try { document.execCommand("copy"); G.aviso("Tabla copiada en formato Markdown."); } catch (e2) { G.aviso("No se pudo copiar."); }
    ta.remove();
  }
};
G.aviso = function (msg) {
  const el = G.h("div", { class: "toast", role: "status" }, msg);
  document.body.append(el);
  setTimeout(() => el.remove(), 2600);
};

/* Tarjeta con título, botones de exportación y el gráfico. `renderizar()` devuelve el <svg>;
   se vuelve a llamar al cambiar el tema o cuando la página pide actualizar(). */
G.tarjetaGrafico = function (titulo, subtitulo, renderizar, markdown) {
  const caja = G.h("div", { class: "grafico" });
  let svg = null;
  const nombre = titulo.toLowerCase().normalize("NFD").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const dibujar = () => { svg = renderizar(); G.vaciar(caja).append(svg); };
  dibujar();
  document.addEventListener("tema-cambiado", dibujar);
  const tarjeta = G.h("div", { class: "tarjeta" },
    G.h("div", { class: "cab-grafico" },
      G.h("div", {}, G.h("h3", {}, titulo), subtitulo ? G.h("p", { class: "suave pequeno", style: "margin:0" }, subtitulo) : null),
      G.h("div", { class: "grupo-botones" },
        G.h("button", { class: "boton chico", type: "button", onclick: () => G.exportarPNG(svg, nombre) }, "Descargar PNG"),
        G.h("button", { class: "boton chico", type: "button", onclick: () => G.exportarSVG(svg, nombre) }, "SVG"),
        markdown ? G.h("button", { class: "boton chico", type: "button", onclick: () => G.copiar(markdown()) }, "Copiar tabla (Markdown)") : null)),
    caja);
  tarjeta.actualizar = dibujar;
  return tarjeta;
};
