"""Gato en movimiento: problema de UN agente para DFS, BFS, UCS y A*.

Tablero N×N con k fichas X móviles y algunas O fijas (obstáculos). Una jugada mueve una X a una
casilla vecina libre (8 direcciones). La meta es dejar las k fichas X formando una línea
(fila, columna o diagonal de k casillas). Es la idea del gato, pero moviendo fichas en vez de
colocarlas.

Formulación como espacio de estados:
    estado          frozenset con los índices (0..N*N-1) de las casillas ocupadas por X.
                    Las O y N no cambian durante la búsqueda, así que no forman parte del estado.
    estado inicial  `x_iniciales` de cada caso.
    acciones        (origen, destino): mover una X a una casilla vecina que no tenga X ni O.
    transición      quita `origen` del conjunto y agrega `destino`.
    meta            las X ocupan exactamente las k casillas de una línea válida.
    costo           paso ortogonal = 2, paso diagonal = 3 (costos distintos: BFS y UCS difieren).

Interfaz que usa gato/busqueda.py: estado_inicial, acciones(s), resultado(s, a), costo(s, a),
es_meta(s) y heuristica(s).
"""

from itertools import permutations

from .consola import color

COSTO_ORTOGONAL = 2
COSTO_DIAGONAL = 3
_DIRECCIONES = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]


def distancia(a, b, n):
    """Costo mínimo de llevar UNA ficha de la casilla `a` a la `b` sin estorbos (distancia octil).

    Se usan todas las diagonales posibles (cuestan 3, menos que dos pasos ortogonales = 4) y se
    completa con pasos ortogonales (2). Es el costo exacto en un tablero vacío.
    """
    dr = abs(a // n - b // n)
    dc = abs(a % n - b % n)
    return COSTO_DIAGONAL * min(dr, dc) + COSTO_ORTOGONAL * abs(dr - dc)


class ProblemaMovil:
    """Una instancia concreta: tamaño N, k fichas, obstáculos O y posición inicial de las X."""

    def __init__(self, nombre, n, k, o_fijas, x_iniciales):
        self.nombre = nombre
        self.n = n
        self.k = k
        self.o_fijas = frozenset(o_fijas)
        self.estado_inicial = frozenset(x_iniciales)
        assert len(self.estado_inicial) == k and not (self.estado_inicial & self.o_fijas)
        self.lineas = self._lineas_validas()    # se calculan una vez; heuristica() las reutiliza

    def _lineas_validas(self):
        """Todas las ventanas de k casillas seguidas (fila, columna, diagonal) sin ninguna O."""
        n, k = self.n, self.k
        lineas = []
        for r in range(n):
            for c in range(n):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    fin_r, fin_c = r + dr * (k - 1), c + dc * (k - 1)
                    if 0 <= fin_r < n and 0 <= fin_c < n:
                        celdas = frozenset((r + dr * i) * n + c + dc * i for i in range(k))
                        if not (celdas & self.o_fijas):
                            lineas.append(celdas)
        return lineas

    def acciones(self, estado):
        """Jugadas legales: (origen, destino) para cada X y cada vecino libre. Orden fijo."""
        n = self.n
        jugadas = []
        for origen in sorted(estado):
            r, c = divmod(origen, n)
            for dr, dc in _DIRECCIONES:
                rr, cc = r + dr, c + dc
                destino = rr * n + cc
                if 0 <= rr < n and 0 <= cc < n and destino not in estado \
                        and destino not in self.o_fijas:
                    jugadas.append((origen, destino))
        return jugadas

    def resultado(self, estado, accion):
        """Estado que resulta de aplicar la jugada. No modifica `estado` (es inmutable)."""
        origen, destino = accion
        return (estado - {origen}) | {destino}

    def costo(self, estado, accion):
        """2 si la ficha se mueve en línea recta, 3 si se mueve en diagonal."""
        origen, destino = accion
        diagonal = origen // self.n != destino // self.n and origen % self.n != destino % self.n
        return COSTO_DIAGONAL if diagonal else COSTO_ORTOGONAL

    def es_meta(self, estado):
        """True si las X ocupan exactamente alguna línea válida."""
        return estado in self.lineas

    def heuristica(self, estado):
        """h1 de A*: costo mínimo de asignar las X a las casillas de la mejor línea.

        Para cada línea válida se prueban todas las asignaciones ficha -> casilla (k! <= 24) y
        se suman las distancias octiles; h es el mínimo. Admisible (ignora que las fichas se
        estorben) y consistente (ver DOCUMENTACION.md).
        """
        fichas = sorted(estado)
        mejor = None
        for linea in self.lineas:
            destinos = sorted(linea)
            for perm in permutations(destinos):
                total = sum(distancia(f, d, self.n) for f, d in zip(fichas, perm))
                if mejor is None or total < mejor:
                    mejor = total
        return mejor or 0

    def heuristica_simple(self, estado):
        """h2, más débil: 2 por cada casilla de la mejor línea que aún no tiene X.

        Cada jugada llena como mucho una casilla y cuesta al menos 2, así que es admisible.
        Sirve para comparar contra `heuristica` en el informe.
        """
        return min(COSTO_ORTOGONAL * len(linea - estado) for linea in self.lineas)

    def describir(self, accion):
        """'4→5': texto de una jugada con casillas numeradas desde 1 (izquierda a derecha)."""
        return f"{accion[0] + 1}→{accion[1] + 1}"

    def dibujar(self, estado, resaltar=None):
        """Tablero en texto; las casillas libres muestran su número. `resaltar` = casilla recién movida."""
        n = self.n
        ancho = len(str(n * n))
        filas = []
        for r in range(n):
            celdas = []
            for c in range(n):
                i = r * n + c
                if i in estado:
                    txt = color("X", "negrita", "rojo")
                    pad = " " * (ancho - 1)
                    if i == resaltar:
                        txt = color("X", "negrita", "amarillo")
                elif i in self.o_fijas:
                    txt, pad = color("O", "negrita", "azul"), " " * (ancho - 1)
                else:
                    txt, pad = color(str(i + 1), "gris"), " " * (ancho - len(str(i + 1)))
                celdas.append(f" {pad}{txt} ")
            filas.append("  " + "│".join(celdas))
        sep = "\n  " + "┼".join("─" * (ancho + 2) for _ in range(n)) + "\n"
        return sep.join(filas)


def _caso(nombre, n, k, texto):
    """Crea un caso desde un dibujo por filas: 'X' ficha móvil, 'O' obstáculo, '.' libre."""
    filas = texto.split("/")
    assert len(filas) == n and all(len(f) == n for f in filas), nombre
    celdas = "".join(filas)
    return ProblemaMovil(nombre, n, k,
                         [i for i, c in enumerate(celdas) if c == "O"],
                         [i for i, c in enumerate(celdas) if c == "X"])


# Casos de prueba fijos (los usan la interfaz, los tests y gato/experimentos.py).
CASOS = {
    "1": _caso("Pequeño 3×3 (3 fichas)", 3, 3, "X.X/.O./X.O"),
    "2": _caso("Mediano 4×4 (BFS y UCS difieren)", 4, 4, "..../XO.X/.XO./..X."),
    "3": _caso("Esquinas 4×4 (4 fichas)", 4, 4, "X..X/.O../..O./X..X"),
    "4": _caso("Grande 5×5 (4 fichas)", 5, 4, "X...X/...../..O../...../X...X"),
}
