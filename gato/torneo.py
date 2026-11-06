"""Competencias entre algoritmos: quién gana y en qué.

1. Torneo de gato (todos contra todos): jugadores de máquina con distinta profundidad límite y
   distinta función de evaluación, más un jugador aleatorio como referencia.
   Minimax y alfa-beta NO compiten entre sí: dan siempre la misma jugada, solo empatarían. Aquí
   todos usan alfa-beta (mismo resultado, mucho más rápido) y lo que compite es la configuración.
2. Competencia de búsqueda: DFS, BFS, UCS, A* (h1) y A* (h2) sobre los casos de gato/movil.py,
   puntuados por costo de la solución, nodos expandidos, memoria y tiempo.

Quién llama: main.py (opción 6) a través de menu_torneo(), y gato/experimentos.py.
"""

import random
from dataclasses import dataclass
from itertools import combinations

from .busqueda import ALGORITMOS, astar, medir
from .consola import color, pedir, titulo
from .minimax import alfabeta
from .movil import CASOS
from .tablero import (aplicar, ganador, esta_lleno, movimientos_validos, oponente,
                      tablero_vacio, turno)

# ---------------------------------------------------------------- torneo de gato


def evaluacion_posicional(t, ia):
    """Evaluación alternativa: solo mira posiciones (centro +3, esquinas +1), no líneas.

    Es el rival "ingenuo" de minimax.evaluacion. Total máximo 7, dividido entre 100:
    |valor| < 1, igual que la evaluación por líneas, para no superar una victoria real.
    """
    rival = oponente(ia)
    total = 0
    for i, peso in ((4, 3), (0, 1), (2, 1), (6, 1), (8, 1)):
        total += peso if t[i] == ia else -peso if t[i] == rival else 0
    return total / 100


@dataclass(frozen=True)
class Jugador:
    """Una configuración que juega al gato."""
    nombre: str
    prof_max: int | None = None     # profundidad límite (None = hasta el final de la partida)
    evaluador: object = None        # función de evaluación (None = la de líneas, minimax.evaluacion)
    aleatorio: bool = False         # True = elige cualquier casilla libre


JUGADORES = [
    Jugador("Aleatorio", aleatorio=True),
    Jugador("Prof 1", prof_max=1),
    Jugador("Prof 2", prof_max=2),
    Jugador("Prof 3", prof_max=3),
    Jugador("Prof 9 (completo)"),
    Jugador("Prof 2 posicional", prof_max=2, evaluador=evaluacion_posicional),
    Jugador("Prof 3 posicional", prof_max=3, evaluador=evaluacion_posicional),
]


def elegir_jugada(jugador, tablero, rng):
    """Casilla (1-9) que juega `jugador` en `tablero`. `rng` solo lo usa el aleatorio."""
    if jugador.aleatorio:
        return rng.choice(movimientos_validos(tablero))
    return alfabeta(tablero, construir_arbol=False, prof_max=jugador.prof_max,
                    evaluador=jugador.evaluador).mejor_mov


def aperturas(partidas, rng, jugadas=2):
    """`partidas` aperturas al azar de `jugadas` jugadas cada una (lista de casillas).

    Los jugadores son deterministas: sin aperturas distintas cada enfrentamiento repetiría la
    misma partida. Una apertura NO la juega ninguno de los dos jugadores.
    """
    resultado = []
    for _ in range(partidas):
        t, ap = tablero_vacio(), []
        for _ in range(jugadas):
            m = rng.choice(movimientos_validos(t))
            ap.append(m)
            t = aplicar(t, m, turno(t))
        resultado.append(ap)
    return resultado


def jugar_partida(jugador_x, jugador_o, apertura, rng):
    """Juega una partida (tras `apertura`) y devuelve 'X', 'O' o None si empatan."""
    t = tablero_vacio()
    for m in apertura:
        t = aplicar(t, m, turno(t))
    while not (ganador(t) or esta_lleno(t)):
        j = jugador_x if turno(t) == "X" else jugador_o
        t = aplicar(t, elegir_jugada(j, t, rng), turno(t))
    return ganador(t)


@dataclass
class ResultadoTorneo:
    """Marcador de un torneo. Victoria = 1 punto, empate = 0,5, derrota = 0."""
    jugadores: list
    ganadas: dict          # nombre -> partidas ganadas
    empatadas: dict
    perdidas: dict
    versus: dict           # (a, b) -> [puntos de a contra b, partidas jugadas]

    def puntos(self, nombre):
        return self.ganadas[nombre] + 0.5 * self.empatadas[nombre]

    def partidas(self, nombre):
        return self.ganadas[nombre] + self.empatadas[nombre] + self.perdidas[nombre]

    def ranking(self):
        """Nombres ordenados del mejor al peor por puntos."""
        return sorted((j.nombre for j in self.jugadores), key=lambda n: -self.puntos(n))


def torneo_gato(jugadores=None, partidas=10, semilla=1):
    """Todos contra todos. Cada pareja juega `partidas` aperturas, y cada apertura dos veces
    (una con cada jugador como X) para que ninguno se beneficie de empezar. `semilla` hace el
    torneo reproducible."""
    jugadores = jugadores or JUGADORES
    rng = random.Random(semilla)
    nombres = [j.nombre for j in jugadores]
    res = ResultadoTorneo(jugadores, {n: 0 for n in nombres}, {n: 0 for n in nombres},
                          {n: 0 for n in nombres}, {})
    for a, b in combinations(jugadores, 2):
        pts = {a.nombre: 0.0, b.nombre: 0.0}
        for ap in aperturas(partidas, rng):
            for jx, jo in ((a, b), (b, a)):
                g = jugar_partida(jx, jo, ap, rng)
                if g is None:
                    for j in (a, b):
                        res.empatadas[j.nombre] += 1
                        pts[j.nombre] += 0.5
                else:
                    gana, pierde = (jx, jo) if g == "X" else (jo, jx)
                    res.ganadas[gana.nombre] += 1
                    res.perdidas[pierde.nombre] += 1
                    pts[gana.nombre] += 1
        res.versus[(a.nombre, b.nombre)] = [pts[a.nombre], 2 * partidas]
        res.versus[(b.nombre, a.nombre)] = [pts[b.nombre], 2 * partidas]
    return res


def mostrar_torneo(res):
    """Imprime el ranking y la matriz de resultados (% de puntos de la fila contra la columna)."""
    ancho = max(len(j.nombre) for j in res.jugadores)
    print(f"  {'#':>2}  {'jugador':<{ancho}}  {'partidas':>8}  {'G':>4} {'E':>4} {'P':>4}  "
          f"{'puntos':>7}  {'%':>6}")
    for pos, n in enumerate(res.ranking(), 1):
        print(f"  {pos:>2}  {n:<{ancho}}  {res.partidas(n):>8}  {res.ganadas[n]:>4} "
              f"{res.empatadas[n]:>4} {res.perdidas[n]:>4}  {res.puntos(n):>7.1f}  "
              f"{100 * res.puntos(n) / res.partidas(n):>5.1f}%")
    print("\n  Puntos de la fila contra la columna (100 % = ganó todas las partidas):")
    orden = res.ranking()
    print("  " + " " * ancho + "  " + " ".join(f"{i + 1:>5}" for i in range(len(orden))))
    for i, a in enumerate(orden):
        celdas = []
        for b in orden:
            if a == b:
                celdas.append(f"{'—':>5}")
            else:
                pts, total = res.versus[(a, b)]
                celdas.append(f"{100 * pts / total:>4.0f}%")
        print(f"  {a:<{ancho}}  " + " ".join(celdas) + f"   ({i + 1})")


# ---------------------------------------------------------- competencia de búsqueda

COMPETIDORES = ["DFS", "BFS", "UCS", "A* (h1)", "A* (h2)"]
# Qué tanto pesa cada criterio en el puntaje total. La calidad de la solución pesa más:
# una solución rápida pero 20 veces más cara no es mejor. Se muestran también los puntajes por
# criterio, porque con otros pesos el campeón puede cambiar.
PESOS = {"costo": 3, "expandidos": 1, "memoria": 1, "tiempo": 1}


def _correr(problema, nombre):
    """Ejecuta un competidor sobre el problema y devuelve su ResultadoBusqueda medido."""
    if nombre == "A* (h1)":
        return medir(astar, problema)
    if nombre == "A* (h2)":
        return medir(astar, problema, heuristica=problema.heuristica_simple)
    return medir(ALGORITMOS[nombre], problema)


def _puntos_por_criterio(valores):
    """{competidor: valor} -> {competidor: puntos}. El mejor recibe n−1 y el peor 0.

    Los empates comparten puntos (ranking de competencia): quien tiene `k` rivales estrictamente
    mejores recibe n − 1 − k.
    """
    n = len(valores)
    return {c: n - 1 - sum(1 for v in valores.values() if v < valores[c]) for c in valores}


def competencia_busqueda(casos=None):
    """Corre los 5 competidores en cada caso y los puntúa. Devuelve un diccionario con:

    resultados  {caso: {competidor: ResultadoBusqueda}}
    criterios   {criterio: {competidor: puntos sumados en todos los casos}}
    total       {competidor: puntaje ponderado por PESOS}
    maximo      puntaje total posible (para dar un porcentaje)
    """
    casos = casos or list(CASOS.values())
    resultados, criterios = {}, {c: {n: 0 for n in COMPETIDORES} for c in PESOS}
    for p in casos:
        resultados[p.nombre] = {n: _correr(p, n) for n in COMPETIDORES}
        rs = resultados[p.nombre]
        medidas = {"costo": {n: rs[n].costo for n in COMPETIDORES},
                   "expandidos": {n: rs[n].expandidos for n in COMPETIDORES},
                   "memoria": {n: rs[n].pico_bytes for n in COMPETIDORES},
                   "tiempo": {n: rs[n].tiempo_ms for n in COMPETIDORES}}
        for c, valores in medidas.items():
            for n, pts in _puntos_por_criterio(valores).items():
                criterios[c][n] += pts
    total = {n: sum(PESOS[c] * criterios[c][n] for c in PESOS) for n in COMPETIDORES}
    maximo = sum(PESOS.values()) * (len(COMPETIDORES) - 1) * len(casos)
    return {"resultados": resultados, "criterios": criterios, "total": total, "maximo": maximo}


def mostrar_competencia_busqueda(comp):
    """Imprime las medidas por caso y el puntaje final."""
    for caso, rs in comp["resultados"].items():
        print(color(f"\n  {caso}", "negrita"))
        print(f"    {'':<8} {'costo':>6} {'pasos':>6} {'expand.':>9} {'mem KB':>8} {'ms':>9}")
        for n in COMPETIDORES:
            r = rs[n]
            print(f"    {n:<8} {r.costo:>6} {r.profundidad:>6} {r.expandidos:>9} "
                  f"{r.pico_bytes // 1024:>8} {r.tiempo_ms:>9.1f}")
    cab = "    " + f"{'':<8}" + "".join(f"{c:>12}" for c in PESOS) + f"{'TOTAL':>10}"
    print(color("\n  Puntos por criterio (suma de todos los casos; mejor = más puntos)", "negrita"))
    print(cab + "    pesos: " + ", ".join(f"{c} ×{w}" for c, w in PESOS.items()))
    orden = sorted(COMPETIDORES, key=lambda n: -comp["total"][n])
    for n in orden:
        print("    " + f"{n:<8}" + "".join(f"{comp['criterios'][c][n]:>12}" for c in PESOS)
              + f"{comp['total'][n]:>10}")
    print(f"\n  Máximo posible: {comp['maximo']}.  Campeón: "
          + color(f"{orden[0]} ({comp['total'][orden[0]]} puntos)", "verde", "negrita"))
    for c in PESOS:
        tope = max(comp["criterios"][c].values())
        mejores = [n for n in COMPETIDORES if comp["criterios"][c][n] == tope]
        print(f"    mejor en {c}: {', '.join(mejores)}")


def menu_torneo():
    """Opción del menú principal: competencias entre algoritmos."""
    print("\n  [1] Torneo de gato: jugadores Minimax con distinta profundidad y evaluación")
    print("  [2] Competencia de búsqueda: DFS, BFS, UCS y A* sobre el Gato en movimiento")
    print("  [3] Ambas")
    op = pedir("Elige (Enter=3): ") or "3"
    if op not in ("1", "2", "3"):
        print(color("Opción no válida.", "rojo"))
        return
    if op in ("1", "3"):
        d = pedir("Aperturas por pareja (Enter=10; cada una se juega con ambos colores): ")
        n = int(d) if d.isdigit() and 1 <= int(d) <= 200 else 10
        titulo("Torneo de gato (todos contra todos)")
        print(f"  {len(JUGADORES)} jugadores, {n} aperturas por pareja, ambos colores. "
              "Victoria 1 · empate 0,5.\n")
        mostrar_torneo(torneo_gato(partidas=n))
    if op in ("2", "3"):
        titulo("Competencia de búsqueda")
        mostrar_competencia_busqueda(competencia_busqueda())
