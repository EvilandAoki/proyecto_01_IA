"""Interfaz de consola del Gato en movimiento: elegir caso y algoritmo, ver solución y métricas."""

from .busqueda import ALGORITMOS, astar, medir
from .consola import color, pedir, titulo
from .movil import CASOS

ORDEN = ["DFS", "BFS", "UCS", "A*"]


def _miles(n):
    """12345 -> '12.345'."""
    return f"{n:,}".replace(",", ".")


def _kb(b):
    return f"{b / 1024:,.0f} KB".replace(",", ".")


def _elegir_caso():
    """Muestra los casos y devuelve el elegido (ProblemaMovil), o None si la opción no vale."""
    print("\nCasos de prueba (X = ficha móvil, O = obstáculo; las X deben formar una línea):")
    for clave, p in CASOS.items():
        print(f"  [{clave}] {p.nombre}")
        print("      " + p.dibujar(p.estado_inicial).replace("\n", "\n      "))
    clave = pedir(f"Caso (1-{len(CASOS)}, Enter=1): ") or "1"
    if clave not in CASOS:
        print(color("Opción no válida.", "rojo"))
        return None
    return CASOS[clave]


def _mostrar_solucion(problema, res):
    """Imprime la lista de jugadas y, si el usuario quiere, el tablero tras cada una."""
    if not res.encontrado:
        print(color("  No se encontró solución.", "rojo"))
        return
    jugadas = [f"{problema.describir(a)} (+{problema.costo(None, a)})" for a, _ in res.camino]
    print(f"  Jugadas ({res.profundidad}): " + "  ".join(jugadas))
    print(f"  Solución: {res.profundidad} pasos, costo total {res.costo}")
    if pedir("¿Ver el tablero paso a paso? [s/N]: ").lower() == "s":
        print("\n  Inicio:\n" + problema.dibujar(problema.estado_inicial))
        for i, (accion, estado) in enumerate(res.camino, 1):
            print(f"\n  Paso {i}: mover {problema.describir(accion)}\n"
                  + problema.dibujar(estado, resaltar=accion[1]))


def _metricas(res):
    """Texto de una línea con las métricas de un ResultadoBusqueda."""
    return (f"expandidos {_miles(res.expandidos)} · generados {_miles(res.generados)} · "
            f"memoria máx {_miles(res.max_memoria)} nodos ({_kb(res.pico_bytes)}) · "
            f"{res.tiempo_ms:.1f} ms")


def ejecutar_algoritmo(problema, nombre):
    """Corre un algoritmo sobre el caso y muestra solución y métricas."""
    res = medir(ALGORITMOS[nombre], problema)
    titulo(f"{nombre} — {problema.nombre}")
    print(f"  {_metricas(res)}")
    _mostrar_solucion(problema, res)


def comparar_algoritmos(problemas):
    """Tabla con los 4 algoritmos sobre cada caso de `problemas`. Devuelve los resultados."""
    cab = (f"  {'caso':<34} {'alg':<4} {'costo':>6} {'pasos':>6} {'expand.':>9} {'gener.':>9} "
           f"{'memoria':>9} {'KB pico':>8} {'ms':>9}")
    print(cab)
    print("  " + "─" * (len(cab) - 2))
    todos = {}
    for p in problemas:
        todos[p.nombre] = {}
        for nombre in ORDEN:
            r = medir(ALGORITMOS[nombre], p)
            todos[p.nombre][nombre] = r
            print(f"  {p.nombre if nombre == 'DFS' else '':<34} {nombre:<4} {r.costo:>6} "
                  f"{r.profundidad:>6} {_miles(r.expandidos):>9} {_miles(r.generados):>9} "
                  f"{_miles(r.max_memoria):>9} {r.pico_bytes // 1024:>8} {r.tiempo_ms:>9.1f}")
        print()
    return todos


def comparar_heuristicas(problema):
    """A* con la heurística de asignación (h1) contra la simple (h2) y contra UCS (h = 0)."""
    titulo(f"Heurísticas de A* — {problema.nombre}")
    filas = [("UCS (h = 0)", medir(ALGORITMOS["UCS"], problema)),
             ("A* con h2 (simple)", medir(astar, problema, heuristica=problema.heuristica_simple)),
             ("A* con h1 (asignación)", medir(astar, problema))]
    for nombre, r in filas:
        print(f"  {nombre:<24} costo {r.costo}  ·  {_metricas(r)}")


def menu_movil():
    """Opción del menú principal: Gato en movimiento (un agente)."""
    problema = _elegir_caso()
    if problema is None:
        return
    print("\nAlgoritmo: [1] DFS  [2] BFS  [3] Costo uniforme  [4] A*  "
          "[5] Comparar los 4  [6] Comparar heurísticas de A*")
    op = pedir("Elige (Enter=4): ") or "4"
    if op in "1234" and len(op) == 1:
        ejecutar_algoritmo(problema, ORDEN[int(op) - 1])
    elif op == "5":
        titulo(f"Comparación — {problema.nombre}")
        comparar_algoritmos([problema])
    elif op == "6":
        comparar_heuristicas(problema)
    else:
        print(color("Opción no válida.", "rojo"))
