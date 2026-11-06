"""Partida humano vs. máquina, mostrando el razonamiento Minimax tras cada jugada de la IA."""

import time
from pathlib import Path

from .animacion import animar, puede_animar
from .arbol import contar_nodos, exportar_arbol, fmt_valor, imprimir_arbol
from .consola import color, limpiar, pedir, titulo
from .minimax import alfabeta, minimax
from .tablero import (aplicar, dibujar, esta_lleno, ganador, movimientos_validos,
                      oponente, tablero_vacio, turno)

# Profundidad máxima que se guarda del árbol con el tablero vacío (si no, ~550 mil nodos).
PROF_ARBOL_VACIO = 3   # con 9 casillas libres el árbol (549.946 nodos) no se guarda entero
# Carpeta donde [e] exportar guarda los árboles en .txt.
CARPETA_EXPORT = Path(__file__).resolve().parent.parent / "arboles"


def _miles(n):
    """12345 -> '12.345'."""
    return f"{n:,}".replace(",", ".")


def _pedir_jugada(tablero, humano):
    """Pide una casilla libre al humano. Devuelve 1-9, o None si escribe q. Lo llama jugar()."""
    libres = movimientos_validos(tablero)
    while True:
        r = pedir(f"Tu jugada ({color(humano, 'negrita')}) — casilla {libres} o [q] salir: ").lower()
        if r == "q":
            return None
        if r.isdigit() and int(r) in libres:
            return int(r)
        print(color("  Casilla no válida.", "rojo"))


def _explicar_ia(tablero, ia, prof_max=None):
    """Hace pensar a la IA, muestra su razonamiento y devuelve el Resultado de minimax.

    Corre Minimax puro (guardando el árbol) y alfa-beta (sin árbol) solo para comparar
    cuántos nodos se habría ahorrado. La jugada que se juega es la de Minimax.
    `prof_max` es la profundidad límite (None = hasta el final); con límite, los nodos de corte
    se valoran con minimax.evaluacion(). Lo llama jugar() en cada turno de la máquina."""
    prof_arbol = PROF_ARBOL_VACIO if len(movimientos_validos(tablero)) == 9 else None
    t0 = time.perf_counter()
    res = minimax(tablero, ia, construir_arbol=True, prof_arbol=prof_arbol, prof_max=prof_max)
    dt = (time.perf_counter() - t0) * 1000
    ab = alfabeta(tablero, ia, construir_arbol=False, prof_max=prof_max)

    print(color(f"\n🤖 La máquina ({ia}) evaluó {_miles(res.nodos)} nodos en {dt:.0f} ms "
                f"con Minimax.", "negrita"))
    print(color(f"   Con poda alfa-beta habría evaluado {_miles(ab.nodos)} "
                f"({100 * (1 - ab.nodos / res.nodos):.1f}% menos) y elegido la misma jugada "
                f"({ab.mejor_mov}).", "gris"))
    print("\n   Valor Minimax de cada jugada posible (+ gano, 0 empato, − pierdo"
          + (f"; |valor| < 1 = estimación a profundidad {prof_max}):" if prof_max else "):"))
    for h in res.raiz.hijos:
        marca = color("  ◀ elegida", "verde", "negrita") if h.movimiento == res.mejor_mov else ""
        v = fmt_valor(h.valor).rjust(5)
        print(f"     casilla {h.movimiento}:  {v}{marca}")
    return res


def _menu_razonamiento(res, tablero, ia):
    """Opciones tras la jugada de la IA (ver árbol, exportar, animar). Lo llama jugar()."""
    truncado = contar_nodos(res.raiz) < res.nodos   # el árbol no se guardó completo
    while True:
        opciones = ["[Enter] continuar", "[a] ver árbol", "[e] exportar árbol"]
        if puede_animar(tablero):
            opciones.append("[p] animar paso a paso")
        r = pedir(color("\n" + " · ".join(opciones) + ": ", "gris")).lower()
        if r == "":
            return
        if r == "a":
            d = pedir("Profundidad a mostrar (1-9, Enter=2, m=solo rama elegida): ").lower()
            if d == "m":
                imprimir_arbol(res.raiz, prof_max=99, solo_mejor=True)
            else:
                imprimir_arbol(res.raiz, prof_max=int(d) if d.isdigit() and d != "0" else 2)
            if truncado:
                print(color("\n(Con el tablero vacío el árbol completo no se guarda; "
                            f"solo se conservan los niveles hasta profundidad {PROF_ARBOL_VACIO}.)",
                            "gris"))
        elif r == "e":
            if truncado:
                print(color("  Este árbol es demasiado grande para exportarlo completo "
                            f"(solo está guardado hasta profundidad {PROF_ARBOL_VACIO}).", "rojo"))
                continue
            CARPETA_EXPORT.mkdir(exist_ok=True)
            ruta = CARPETA_EXPORT / f"arbol_{int(time.time())}.txt"
            n = exportar_arbol(res.raiz, ruta)
            print(color(f"  Árbol exportado ({_miles(n)} líneas): {ruta}", "verde"))
        elif r == "p" and puede_animar(tablero):
            animar(tablero)
            pedir(color("Enter para volver a la partida...", "gris"))
            return
        else:
            print(color("  Opción no válida.", "rojo"))


def jugar():
    """Bucle de la partida (opción 1 del menú): alterna humano / IA hasta que termine."""
    limpiar()
    titulo("Gato contra la máquina (Minimax)")
    print("X siempre empieza. Si juegas con X, empiezas tú.\n")
    r = pedir("¿Con qué ficha quieres jugar? [X/O] (Enter=X): ").upper() or "X"
    if r not in ("X", "O"):
        print("Opción no válida.")
        return
    humano, ia = r, oponente(r)
    d = pedir("Profundidad límite de la máquina (1-9, Enter=9 = hasta el final): ")
    prof_max = int(d) if d.isdigit() and 1 <= int(d) < 9 else None
    tablero = tablero_vacio()

    while not (ganador(tablero) or esta_lleno(tablero)):
        print("\n" + dibujar(tablero) + "\n")
        if turno(tablero) == humano:
            jugada = _pedir_jugada(tablero, humano)
            if jugada is None:
                return
            tablero = aplicar(tablero, jugada, humano)
        else:
            antes = tablero
            res = _explicar_ia(tablero, ia, prof_max)
            tablero = aplicar(tablero, res.mejor_mov, ia)
            print(f"\n   Resultado: la máquina juega en la casilla {res.mejor_mov}.")
            print("\n" + dibujar(tablero, resaltar=res.mejor_mov))
            _menu_razonamiento(res, antes, ia)

    print("\n" + dibujar(tablero) + "\n")
    g = ganador(tablero)
    if g == humano:
        if prof_max:
            print(color("¡Ganaste! Con profundidad límite la máquina no ve toda la partida.",
                        "verde", "negrita"))
        else:
            print(color("¡Ganaste! (Esto no debería pasar: ¿encontraste un bug?)",
                        "verde", "negrita"))
    elif g == ia:
        print(color("Ganó la máquina.", "rojo", "negrita"))
    else:
        print(color("Empate: el mejor resultado posible contra Minimax.", "amarillo", "negrita"))
