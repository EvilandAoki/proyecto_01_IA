"""Reglas del gato. El tablero es una tupla de 9 celdas ('X', 'O' o ' ').

Las posiciones se numeran 1-9 como en un teclado numérico invertido (lectura normal):

    1 | 2 | 3
    4 | 5 | 6
    7 | 8 | 9

X siempre empieza, así que el turno se deduce contando fichas.
"""

from .consola import color

# Marca de celda libre.
VACIO = " "
# Las 8 combinaciones de índices (0-8) que dan victoria. Las usa ganador().
LINEAS_GANADORAS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # filas
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columnas
    (0, 4, 8), (2, 4, 6),             # diagonales
)


def tablero_vacio():
    """Tablero inicial: 9 celdas libres. Lo llaman juego.jugar y estadisticas."""
    return (VACIO,) * 9


def desde_texto(texto):
    """Crea un tablero desde un texto como 'XOX/.O./.X.' ('.', '-', '_' o '·' = vacío)."""
    celdas = []
    for c in texto:
        if c in "xX":
            celdas.append("X")
        elif c in "oO0":
            celdas.append("O")
        elif c in ".-_·":
            celdas.append(VACIO)
        elif c in "/ \n\t":
            continue
        else:
            raise ValueError(f"Carácter no válido en el tablero: {c!r}")
    if len(celdas) != 9:
        raise ValueError("El tablero debe tener exactamente 9 celdas")
    return tuple(celdas)


def oponente(jugador):
    """El otro jugador. Minimax lo usa en cada paso recursivo para alternar el turno."""
    return "O" if jugador == "X" else "X"


def turno(tablero):
    """Jugador al que le toca mover (X empieza): si hay igual nº de X y O, juega X."""
    return "X" if tablero.count("X") == tablero.count("O") else "O"


def movimientos_validos(tablero):
    """Posiciones libres en el rango 1-9 (las jugadas legales). Es el 'generador de hijos'
    del árbol: _evaluar() itera sobre esta lista."""
    return [i + 1 for i, c in enumerate(tablero) if c == VACIO]


def aplicar(tablero, posicion, jugador):
    """Devuelve un tablero nuevo con la jugada hecha (posicion en 1-9).

    Las tuplas son inmutables, así que el tablero del padre nunca se modifica y no hace
    falta "deshacer" la jugada al volver de la recursión."""
    i = posicion - 1
    return tablero[:i] + (jugador,) + tablero[i + 1:]


def ganador(tablero):
    """'X', 'O' o None. Revisa las 8 líneas de LINEAS_GANADORAS."""
    for a, b, c in LINEAS_GANADORAS:
        if tablero[a] != VACIO and tablero[a] == tablero[b] == tablero[c]:
            return tablero[a]
    return None


def esta_lleno(tablero):
    """True si no quedan casillas libres (empate si nadie ganó)."""
    return VACIO not in tablero


def es_terminal(tablero):
    """True si la partida terminó (hay ganador o tablero lleno)."""
    return ganador(tablero) is not None or esta_lleno(tablero)


def _ficha(c, indice, resaltar):
    """Texto coloreado de una celda; si está vacía muestra su número. `resaltar` = última jugada."""
    if c == "X":
        txt = color("X", "negrita", "rojo")
    elif c == "O":
        txt = color("O", "negrita", "azul")
    else:
        return color(str(indice + 1), "gris")
    return color(txt, "amarillo") if indice + 1 == resaltar else txt


def dibujar(tablero, resaltar=None):
    """Tablero grande; las celdas vacías muestran su número."""
    filas = []
    for r in range(3):
        celdas = [_ficha(tablero[3 * r + k], 3 * r + k, resaltar) for k in range(3)]
        filas.append("  " + "│".join(f" {c} " for c in celdas))
    return "\n  ───┼───┼───\n".join(filas)


def dibujar_mini(tablero):
    """Una sola línea: 'X O · | · X · | · · O' (para nodos del árbol)."""
    filas = []
    for r in range(3):
        filas.append(" ".join(c if c != VACIO else "·" for c in tablero[3 * r:3 * r + 3]))
    return " | ".join(filas)
