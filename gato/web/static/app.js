/* Núcleo de la interfaz: utilidades de DOM, cliente de la API, tema y pestañas.
   Todo cuelga del objeto global G para que los demás archivos lo compartan. */
"use strict";
const G = (window.G = { paginas: [], pendiente: null });

/* ---- DOM ---- */
const NS_SVG = "http://www.w3.org/2000/svg";
G.h = function (tag, atrib, ...hijos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(atrib || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  G.añadir(el, hijos);
  return el;
};
G.svg = function (tag, atrib, ...hijos) {
  const el = document.createElementNS(NS_SVG, tag);
  for (const [k, v] of Object.entries(atrib || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.setAttribute("class", v);
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v);
  }
  G.añadir(el, hijos);
  return el;
};
G.añadir = function (el, hijos) {
  for (const hijo of hijos.flat()) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
  return el;
};
G.vaciar = (el) => { while (el.firstChild) el.removeChild(el.firstChild); return el; };

/* ---- Formato ---- */
G.miles = (n) => Number(n).toLocaleString("es-CO");
G.fmt = function (v) {            // valores de Minimax: +3, -2, 0, +0.12, ±∞
  if (v === null || v === undefined) return "?";
  if (v === "+inf") return "+∞";
  if (v === "-inf") return "−∞";
  if (v === 0) return "0";
  return Number.isInteger(v) ? (v > 0 ? "+" : "−") + Math.abs(v) : (v > 0 ? "+" : "−") + Math.abs(v).toFixed(2);
};
G.kb = (b) => (b / 1024).toFixed(b < 10240 ? 1 : 0) + " KB";
G.esperar = (ms) => new Promise((r) => setTimeout(r, ms));

/* ---- Movimiento reducido ---- */
G.reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---- API ---- */
G.api = {
  async pedir(ruta, opciones) {
    let r;
    try { r = await fetch(ruta, opciones); }
    catch (e) { throw new Error("No hay conexión con el servidor local. ¿Sigue corriendo `python3 -m gato.web`?"); }
    let datos = null;
    try { datos = await r.json(); } catch (e) { /* respuesta sin JSON */ }
    if (!r.ok) throw new Error((datos && datos.error) || `Error ${r.status}`);
    return datos;
  },
  get: (ruta) => G.api.pedir(ruta),
  post: (ruta, cuerpo) => G.api.pedir(ruta, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) }),
};
/* Datos que se piden una sola vez */
G._catalogo = null;
G.catalogo = async function () { return (G._catalogo ||= await G.api.get("/api/casos")); };

/* ---- Tema ---- */
G.tema = function () {            // colores ya resueltos (los gráficos exportados no pueden usar var())
  const s = getComputedStyle(document.documentElement);
  const c = (n) => s.getPropertyValue(n).trim();
  return { fondo: c("--superficie"), texto: c("--texto"), suave: c("--suave"), borde: c("--borde"),
    acento: c("--acento"), bien: c("--bien"), mal: c("--mal"), x: c("--x"), o: c("--o"),
    series: [c("--serie-1"), c("--serie-2"), c("--serie-3"), c("--serie-4"), c("--serie-5")] };
};
G.aplicarTema = function (modo) {
  const raiz = document.documentElement;
  if (modo === "light" || modo === "dark") raiz.setAttribute("data-theme", modo); else raiz.removeAttribute("data-theme");
  const oscuro = modo === "dark" || (modo !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const b = document.getElementById("btn-tema");
  b.textContent = oscuro ? "☀" : "☾";
  b.title = oscuro ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
  document.dispatchEvent(new CustomEvent("tema-cambiado"));
};
G.iniciarTema = function () {
  let guardado = null;
  try { guardado = localStorage.getItem("gato-tema"); } catch (e) { /* sin almacenamiento */ }
  G.aplicarTema(guardado);
  document.getElementById("btn-tema").addEventListener("click", () => {
    const oscuro = getComputedStyle(document.documentElement).getPropertyValue("--fondo").trim() === "#0f1216";
    const nuevo = oscuro ? "light" : "dark";
    try { localStorage.setItem("gato-tema", nuevo); } catch (e) { /* sin almacenamiento */ }
    G.aplicarTema(nuevo);
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => G.aplicarTema(document.documentElement.getAttribute("data-theme")));
};

/* ---- Pestañas ---- */
G.registrar = function (id, titulo, montar) { G.paginas.push({ id, titulo, montar, panel: null, montada: false }); };
G.ir = function (id, datos) {
  const pagina = G.paginas.find((p) => p.id === id);
  if (!pagina) return;
  G.pendiente = datos || null;
  for (const p of G.paginas) {
    p.boton.setAttribute("aria-selected", String(p === pagina));
    p.boton.tabIndex = p === pagina ? 0 : -1;
    p.panel.hidden = p !== pagina;
  }
  if (!pagina.montada) { pagina.montada = true; pagina.api = pagina.montar(pagina.panel) || {}; }
  if (pagina.api.alActivar) pagina.api.alActivar(G.pendiente);
  G.pendiente = null;
  try { history.replaceState(null, "", "#" + id); } catch (e) { /* ignorar */ }
};
G.iniciar = function () {
  G.iniciarTema();
  const nav = document.getElementById("pestanas"), main = document.getElementById("contenido");
  for (const p of G.paginas) {
    p.boton = G.h("button", { type: "button", role: "tab", id: "tab-" + p.id, "aria-controls": "panel-" + p.id, "aria-selected": "false", onclick: () => G.ir(p.id) }, p.titulo);
    p.panel = G.h("section", { role: "tabpanel", id: "panel-" + p.id, "aria-labelledby": "tab-" + p.id, hidden: true });
    nav.append(p.boton); main.append(p.panel);
  }
  nav.addEventListener("keydown", (e) => {          // flechas entre pestañas
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const i = G.paginas.findIndex((p) => p.boton.getAttribute("aria-selected") === "true");
    const j = (i + (e.key === "ArrowRight" ? 1 : -1) + G.paginas.length) % G.paginas.length;
    G.ir(G.paginas[j].id); G.paginas[j].boton.focus();
  });
  const inicial = location.hash.slice(1);
  G.ir(G.paginas.some((p) => p.id === inicial) ? inicial : G.paginas[0].id);
};
window.addEventListener("DOMContentLoaded", () => setTimeout(G.iniciar, 0));   // espera a que carguen las páginas
