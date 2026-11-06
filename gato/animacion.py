"""Animación paso a paso: cómo Minimax recorre el árbol y hace subir los valores."""

import time

from .arbol import fmt_valor, imprimir_arbol
from .consola import color, limpiar, pedir, titulo
from .minimax import alfabeta, minimax
from .tablero import desde_texto, dibujar, dibujar_mini, ganador, movimientos_validos, turno

# Posiciones pequeñas (pocas casillas libres) para poder seguir todo el árbol en pantalla.
EJEMPLOS = {
    "A": ("4 casillas libres, mueve O (nadie gana de inmediato)", desde_texto("XOX/.O./.X.")),
    "B": ("3 casillas libres, X puede ganar de inmediato", desde_texto("XOX/OXO/...")),
    "C": ("5 casillas libres, mueve X (el árbol más grande)", desde_texto("XO./.X./..O")),
}


def _fmt(v):
    """Formatea un valor (+3, -2, 0, ±∞, +0.12) para los mensajes."""
    return fmt_valor(v)


def _grabar(tablero, usar_poda):
    """Ejecuta la búsqueda COMPLETA de antemano, guardando cada evento que emite el callback.

    La animación no calcula nada en vivo: solo reproduce esta lista. Cada evento es
    (nombre, nodo, valor, alfa, beta) con nombre en entrar / hoja / subir / poda."""
    eventos = []

    def cb(evento, nodo, valor=None, alfa=None, beta=None):
        """Lo llama minimax._evaluar en cada evento; solo lo anota."""
        eventos.append((evento, nodo, valor, alfa, beta))

    algoritmo = alfabeta if usar_poda else minimax
    resultado = algoritmo(tablero, construir_arbol=True, callback=cb)
    return resultado, eventos


def explicar_evento(evento, nodo, valor, alfa, beta, valores, usar_poda):
    """Frase en español que describe el evento actual (qué hace el algoritmo en este paso).

    `valores` es un dict id(nodo) -> valor ya calculado. La usan animar() y la interfaz web."""
    ab = f"   (α={_fmt(alfa)}, β={_fmt(beta)})" if usar_poda else ""
    if evento == "entrar":
        mov = f"jugada {nodo.movimiento}" if nodo.movimiento else "raíz"
        resto = "es un estado terminal." if nodo.tipo == "HOJA" else f"le toca a {nodo.turno}."
        return f"Bajamos al nodo {mov} (profundidad {nodo.profundidad}); {resto}{ab}"
    if evento == "hoja":
        g = ganador(nodo.tablero)
        quien = f"gana {g}" if g else "empate (tablero lleno)"
        return (f"Estado terminal: {quien}. Utilidad = {_fmt(valor)} "
                f"(profundidad {nodo.profundidad}).")
    if evento == "corte":
        return (f"Profundidad límite ({nodo.profundidad}): no se baja más. "
                f"Valor estimado por la función de evaluación = {valor:+.2f}.")
    if evento == "subir":
        hijos = [valores[id(h)] for h in nodo.hijos if id(h) in valores and not h.podado]
        lista = ", ".join(_fmt(x) for x in hijos)
        if nodo.tipo == "MAX":
            return (f"Sube el valor: nodo MAX elige el MÁXIMO de [{lista}] = {_fmt(valor)}"
                    f"  → mejor jugada: {nodo.elegido}.{ab}")
        return (f"Sube el valor: nodo MIN elige el MÍNIMO de [{lista}] = {_fmt(valor)}"
                f"  → mejor jugada: {nodo.elegido}.{ab}")
    if evento == "poda":
        n = sum(1 for h in nodo.hijos if h.podado)
        return (color(f"✂ PODA: β={_fmt(beta)} ≤ α={_fmt(alfa)}. El rival ya tiene una opción "
                      f"mejor en otra rama, así que se descartan {n} hermano(s) sin evaluarlos.",
                      "amarillo", "negrita"))
    return ""


def animar(tablero, usar_poda=False, retardo=0.35):
    """Reproduce la búsqueda desde `tablero` evento por evento.

    visible = ids de nodos ya descubiertos; valores = id -> valor ya calculado.
    Ambos crecen con cada evento y se pasan a imprimir_arbol para dibujar el estado actual.
    Lo llaman menu_animacion() y juego._menu_razonamiento."""
    resultado, eventos = _grabar(tablero, usar_poda)
    raiz = resultado.raiz
    nombre = "Minimax con poda alfa-beta" if usar_poda else "Minimax"
    visible = {id(raiz)}
    valores = {}
    modo_auto = False
    total = len(eventos)

    for i, (evento, nodo, valor, alfa, beta) in enumerate(eventos, 1):
        if evento == "entrar":
            visible.add(id(nodo))
        elif evento in ("hoja", "corte", "subir"):
            valores[id(nodo)] = valor
        elif evento == "poda":
            visible.update(id(h) for h in nodo.hijos if h.podado)

        limpiar()
        titulo(f"{nombre} — paso {i}/{total}")
        print(f"Posición inicial: {dibujar_mini(tablero)}   (MAX = {turno(tablero)})")
        print(color("MAX maximiza la utilidad de la máquina · MIN la minimiza · "
                    "▶ nodo actual · v=? aún sin valor\n", "gris"))
        imprimir_arbol(raiz, prof_max=99, visible=visible, valores=valores,
                       actual=nodo, mostrar_ab=False)
        print("\n" + explicar_evento(evento, nodo, valor, alfa, beta, valores, usar_poda) + "\n")

        if i == total:
            break
        if modo_auto:
            try:
                time.sleep(retardo)
                continue
            except KeyboardInterrupt:
                modo_auto = False
        resp = pedir(color("[Enter] siguiente · [a] automático · [f] ir al final · "
                           "[q] salir: ", "gris")).lower()
        if resp == "q":
            return
        if resp == "a":
            modo_auto = True
        if resp == "f":
            return _final(raiz, tablero, resultado, nombre, usar_poda)

    _final(raiz, tablero, resultado, nombre, usar_poda)


def _final(raiz, tablero, resultado, nombre, usar_poda):
    """Pantalla de cierre: árbol completo, nodos evaluados y mejor jugada."""
    limpiar()
    titulo(f"{nombre} — árbol final")
    print(f"Posición inicial: {dibujar_mini(tablero)}\n")
    imprimir_arbol(raiz, prof_max=99, mostrar_ab=usar_poda)
    print(f"\nNodos evaluados: {resultado.nodos}   ·   valor de la raíz: {_fmt(resultado.valor)}"
          f"   ·   mejor jugada: {resultado.mejor_mov}")
    print("La rama verde es la variante principal: la secuencia que Minimax cree que se jugará.")


def menu_animacion():
    """Opción 2 del menú: elegir ejemplo y algoritmo, y lanzar animar()."""
    print()
    print("Elige una posición de ejemplo (pocas casillas libres para ver todo el árbol):")
    for clave, (desc, t) in EJEMPLOS.items():
        print(f"  [{clave}] {desc}")
        print("      " + dibujar(t).replace("\n", "\n      "))
    clave = pedir("Posición (A/B/C, Enter=A): ").upper() or "A"
    if clave not in EJEMPLOS:
        print("Opción no válida.")
        return
    algo = pedir("Algoritmo: [1] Minimax  [2] Minimax con poda alfa-beta (Enter=1): ") or "1"
    animar(EJEMPLOS[clave][1], usar_poda=(algo == "2"))


def puede_animar(tablero):
    """Una posición es animable si queda poco por explorar (1-5 casillas libres)."""
    return 0 < len(movimientos_validos(tablero)) <= 5
