"""Genera las tablas del informe (formato Markdown): python3 -m gato.experimentos

Mide los 4 algoritmos de búsqueda sobre todos los casos de gato/movil.py, las heurísticas de A*
y Minimax con y sin poda a varias profundidades límite.
"""

import time

from .busqueda import ALGORITMOS, astar, medir
from .minimax import alfabeta, minimax
from .movil import CASOS
from .torneo import COMPETIDORES, PESOS, competencia_busqueda, torneo_gato
from .tablero import desde_texto, tablero_vacio

ORDEN = ["DFS", "BFS", "UCS", "A*"]
POSICIONES_MINIMAX = [("Tablero vacío (mueve X)", tablero_vacio(), [1, 2, 3, 4, 5, 6, 9]),
                      ("X en el centro (mueve O)", desde_texto("....X...."), [1, 2, 3, 4, 5, 6, 8]),
                      ("Mitad de partida (5 libres)", desde_texto("XO./.X./..O"), [1, 2, 3, 5])]


def _miles(n):
    return f"{n:,}".replace(",", ".")


def tabla_busqueda():
    """Los 4 algoritmos × cada caso: costo, pasos, nodos, memoria y tiempo."""
    print("| Caso | Alg. | Costo | Pasos | Expandidos | Generados | Memoria máx. (nodos) "
          "| Pico (KB) | Tiempo (ms) |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for p in CASOS.values():
        for nombre in ORDEN:
            r = medir(ALGORITMOS[nombre], p)
            print(f"| {p.nombre if nombre == 'DFS' else ''} | {nombre} | {r.costo} | "
                  f"{r.profundidad} | {_miles(r.expandidos)} | {_miles(r.generados)} | "
                  f"{_miles(r.max_memoria)} | {r.pico_bytes // 1024} | {r.tiempo_ms:.1f} |")


def tabla_heuristicas():
    """UCS (h=0) contra A* con h2 (simple) y con h1 (asignación)."""
    print("| Caso | Algoritmo | Costo | Expandidos | Tiempo (ms) |")
    print("|---|---|---:|---:|---:|")
    for p in CASOS.values():
        filas = [("UCS (h = 0)", medir(ALGORITMOS["UCS"], p)),
                 ("A* con h2 (simple)", medir(astar, p, heuristica=p.heuristica_simple)),
                 ("A* con h1 (asignación)", medir(astar, p))]
        for i, (nombre, r) in enumerate(filas):
            print(f"| {p.nombre if i == 0 else ''} | {nombre} | {r.costo} | "
                  f"{_miles(r.expandidos)} | {r.tiempo_ms:.1f} |")


def tabla_minimax():
    """Nodos evaluados con y sin poda, para varias profundidades límite."""
    print("| Posición | Prof. límite | Jugada | Valor | Nodos Minimax | Nodos alfa-beta "
          "| Ahorro | t Minimax (ms) | t alfa-beta (ms) |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for nombre, t, profundidades in POSICIONES_MINIMAX:
        for i, d in enumerate(profundidades):
            t0 = time.perf_counter()
            a = minimax(t, construir_arbol=False, prof_max=d)
            t1 = time.perf_counter()
            b = alfabeta(t, construir_arbol=False, prof_max=d)
            t2 = time.perf_counter()
            assert (a.mejor_mov, a.valor) == (b.mejor_mov, b.valor)
            print(f"| {nombre if i == 0 else ''} | {d} | {a.mejor_mov} | {a.valor:+.2f} | "
                  f"{_miles(a.nodos)} | {_miles(b.nodos)} | {100 * (1 - b.nodos / a.nodos):.1f} % | "
                  f"{(t1 - t0) * 1000:.1f} | {(t2 - t1) * 1000:.1f} |")


def tabla_torneo():
    """Ranking del torneo de gato (todos contra todos, 10 aperturas por pareja, ambos colores)."""
    res = torneo_gato(partidas=10, semilla=1)
    print("| # | Jugador | Partidas | Ganadas | Empatadas | Perdidas | Puntos | % |")
    print("|---:|---|---:|---:|---:|---:|---:|---:|")
    for pos, n in enumerate(res.ranking(), 1):
        print(f"| {pos} | {n} | {res.partidas(n)} | {res.ganadas[n]} | {res.empatadas[n]} | "
              f"{res.perdidas[n]} | {res.puntos(n):.1f} | "
              f"{100 * res.puntos(n) / res.partidas(n):.1f} % |")


def tabla_competencia_busqueda():
    """Puntos por criterio y total de la competencia DFS / BFS / UCS / A* (h1) / A* (h2)."""
    comp = competencia_busqueda()
    print("| Competidor | " + " | ".join(f"{c} (×{w})" for c, w in PESOS.items()) + " | Total |")
    print("|---|" + "---:|" * (len(PESOS) + 1))
    for n in sorted(COMPETIDORES, key=lambda n: -comp["total"][n]):
        print(f"| {n} | " + " | ".join(str(comp["criterios"][c][n]) for c in PESOS)
              + f" | {comp['total'][n]} de {comp['maximo']} |")


def main():
    print("## Búsqueda en el Gato en movimiento\n")
    tabla_busqueda()
    print("\n## Heurísticas de A*\n")
    tabla_heuristicas()
    print("\n## Minimax con y sin poda alfa-beta\n")
    tabla_minimax()
    print("\n## Torneo de gato (todos contra todos)\n")
    tabla_torneo()
    print("\n## Competencia de búsqueda\n")
    tabla_competencia_busqueda()


if __name__ == "__main__":
    main()
