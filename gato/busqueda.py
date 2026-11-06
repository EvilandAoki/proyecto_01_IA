"""DFS, BFS, costo uniforme y A* sobre cualquier problema de un agente.

Los cuatro algoritmos comparten el mismo esqueleto: una frontera (nodos descubiertos que aún
no se expanden) y un conjunto `explorados` (estados ya expandidos, para no repetirlos). Solo
cambia la estructura de la frontera, y con ella el orden en que se sacan los nodos:

    DFS  pila (LIFO)                        -> baja por una rama hasta el fondo
    BFS  cola (FIFO, deque)                 -> avanza nivel por nivel
    UCS  cola de prioridad por g            -> expande primero lo más barato hasta ahora
    A*   cola de prioridad por g + h        -> como UCS, pero guiado por la heurística

El problema debe ofrecer: estado_inicial, acciones(s), resultado(s, a), costo(s, a),
es_meta(s) y heuristica(s) (ver gato/movil.py). Quién llama: gato/solitario.py y
gato/experimentos.py, siempre a través de medir().

Traza opcional: cada algoritmo acepta `traza`, una función que se llama después de expandir cada
nodo como traza(nodo, tamaño_frontera, tamaño_explorados). La interfaz web la usa para animar la
búsqueda; con `traza=None` (lo normal) no ocurre nada.

Convención de métricas:
    expandidos  nodos de los que se generaron sucesores (el nodo meta no se cuenta)
    generados   nodos creados (incluye los que estaban repetidos y se descartaron)
"""

import heapq
import time
import tracemalloc
from collections import deque
from dataclasses import dataclass, field


class NodoBusqueda:
    """Un nodo del árbol de búsqueda: un estado + cómo se llegó a él."""
    __slots__ = ("estado", "padre", "accion", "g", "prof")

    def __init__(self, estado, padre=None, accion=None, g=0, prof=0):
        self.estado = estado    # el estado del problema
        self.padre = padre      # nodo del que viene (None en la raíz)
        self.accion = accion    # jugada que llevó del padre a este nodo
        self.g = g              # costo acumulado desde el estado inicial
        self.prof = prof        # número de pasos desde el estado inicial

    def hijo(self, problema, accion):
        """Nodo sucesor al aplicar `accion`. Acumula costo y profundidad."""
        return NodoBusqueda(problema.resultado(self.estado, accion), self, accion,
                            self.g + problema.costo(self.estado, accion), self.prof + 1)

    def camino(self):
        """Lista de (accion, estado) desde el primer paso hasta este nodo."""
        pasos, n = [], self
        while n.padre is not None:
            pasos.append((n.accion, n.estado))
            n = n.padre
        return pasos[::-1]


@dataclass
class ResultadoBusqueda:
    algoritmo: str
    encontrado: bool = False
    camino: list = field(default_factory=list)   # [(accion, estado), ...]
    costo: int | None = None
    profundidad: int | None = None               # pasos de la solución
    expandidos: int = 0
    generados: int = 0
    max_memoria: int = 0        # máximo de |frontera| + |explorados| (nodos en memoria a la vez)
    pico_bytes: int = 0         # pico de memoria de Python durante la búsqueda (tracemalloc)
    tiempo_ms: float = 0.0


def _terminar(res, nodo):
    """Anota en `res` la solución que termina en `nodo`."""
    res.encontrado = True
    res.camino = nodo.camino()
    res.costo, res.profundidad = nodo.g, nodo.prof
    return res


def dfs(problema, traza=None):
    """Búsqueda en profundidad: pila LIFO. Encuentra UNA solución, no necesariamente la mejor."""
    res = ResultadoBusqueda("DFS")
    raiz = NodoBusqueda(problema.estado_inicial)
    if problema.es_meta(raiz.estado):
        return _terminar(res, raiz)
    pila, explorados = [raiz], set()
    while pila:
        nodo = pila.pop()                       # el último en entrar es el primero en salir
        if nodo.estado in explorados:
            continue
        explorados.add(nodo.estado)
        res.expandidos += 1
        # Se apilan al revés para que la primera jugada de la lista sea la primera en explorarse.
        for accion in reversed(problema.acciones(nodo.estado)):
            h = nodo.hijo(problema, accion)
            res.generados += 1
            if h.estado in explorados:
                continue
            if problema.es_meta(h.estado):
                if traza:
                    traza(nodo, len(pila), len(explorados))     # último nodo expandido
                return _terminar(res, h)
            pila.append(h)
        res.max_memoria = max(res.max_memoria, len(pila) + len(explorados))
        if traza:
            traza(nodo, len(pila), len(explorados))
    return res


def bfs(problema, traza=None):
    """Búsqueda en amplitud: cola FIFO. Halla la solución con MENOS PASOS (no menor costo)."""
    res = ResultadoBusqueda("BFS")
    raiz = NodoBusqueda(problema.estado_inicial)
    if problema.es_meta(raiz.estado):
        return _terminar(res, raiz)
    cola = deque([raiz])
    vistos = {raiz.estado}      # frontera + explorados: un estado se encola una sola vez
    while cola:
        nodo = cola.popleft()                   # el primero en entrar es el primero en salir
        res.expandidos += 1
        for accion in problema.acciones(nodo.estado):
            h = nodo.hijo(problema, accion)
            res.generados += 1
            if h.estado in vistos:
                continue
            if problema.es_meta(h.estado):      # en BFS se puede probar la meta al generar
                if traza:
                    traza(nodo, len(cola), res.expandidos)      # último nodo expandido
                return _terminar(res, h)
            vistos.add(h.estado)
            cola.append(h)
        res.max_memoria = max(res.max_memoria, len(vistos))
        if traza:
            traza(nodo, len(cola), res.expandidos)
    return res


def _mejor_primero(problema, nombre, prioridad, traza=None):
    """Núcleo común de UCS y A*: cola de prioridad ordenada por `prioridad(nodo)`.

    La meta se prueba al SACAR el nodo (no al generarlo): solo entonces se sabe que ningún
    camino pendiente es más barato. `mejor_g` guarda el menor costo conocido de cada estado;
    si aparece uno más barato se vuelve a encolar y la entrada vieja se ignora al sacarla.
    """
    res = ResultadoBusqueda(nombre)
    raiz = NodoBusqueda(problema.estado_inicial)
    contador = 0    # desempata prioridades iguales (NodoBusqueda no es comparable)
    frontera = [(prioridad(raiz), contador, raiz)]
    mejor_g = {raiz.estado: 0}
    explorados = set()
    while frontera:
        _, _, nodo = heapq.heappop(frontera)    # el de menor prioridad
        if nodo.estado in explorados:
            continue                            # entrada obsoleta: ya se expandió más barata
        if problema.es_meta(nodo.estado):
            return _terminar(res, nodo)
        explorados.add(nodo.estado)
        res.expandidos += 1
        for accion in problema.acciones(nodo.estado):
            h = nodo.hijo(problema, accion)
            res.generados += 1
            if h.estado in explorados or h.g >= mejor_g.get(h.estado, float("inf")):
                continue
            mejor_g[h.estado] = h.g
            contador += 1
            heapq.heappush(frontera, (prioridad(h), contador, h))
        res.max_memoria = max(res.max_memoria, len(frontera) + len(explorados))
        if traza:
            traza(nodo, len(frontera), len(explorados))
    return res


def ucs(problema, traza=None):
    """Costo uniforme: prioridad = g. Halla la solución de MENOR COSTO."""
    return _mejor_primero(problema, "UCS", lambda n: n.g, traza)


def astar(problema, heuristica=None, traza=None):
    """A*: prioridad = g + h. Con h admisible halla el costo mínimo y expande menos que UCS.

    `heuristica` es una función estado -> número; por defecto la del problema.
    """
    h = heuristica or problema.heuristica
    return _mejor_primero(problema, "A*", lambda n: n.g + h(n.estado), traza)


ALGORITMOS = {"DFS": dfs, "BFS": bfs, "UCS": ucs, "A*": astar}


def medir(algoritmo, problema, **kwargs):
    """Ejecuta `algoritmo` y devuelve su ResultadoBusqueda con tiempo y memoria medidos.

    Se corre dos veces: una limpia para el tiempo y otra con tracemalloc para el pico de
    memoria (tracemalloc ralentiza mucho, así que falsearía el tiempo si fuera la misma).
    """
    t0 = time.perf_counter()
    res = algoritmo(problema, **kwargs)
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    tracemalloc.start()
    try:
        algoritmo(problema, **kwargs)
        res.pico_bytes = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return res
