"""Estadísticas del árbol completo del gato y comparación Minimax vs. alfa-beta."""

import time
from dataclasses import dataclass, field

from .arbol import imprimir_arbol
from .consola import color, pedir, titulo
from .minimax import alfabeta, minimax, valores_por_movimiento
from .tablero import (aplicar, desde_texto, dibujar_mini, esta_lleno, ganador,
                      movimientos_validos, oponente, tablero_vacio, turno)
from .animacion import EJEMPLOS


@dataclass
class EstadisticasArbol:
    """Contadores del recorrido completo del árbol (índice de las listas = profundidad)."""
    nodos_por_prof: list = field(default_factory=lambda: [0] * 10)
    terminales_por_prof: list = field(default_factory=lambda: [0] * 10)
    victorias: dict = field(default_factory=lambda: {"X": 0, "O": 0, "empate": 0})
    posiciones: set = field(default_factory=set)

    @property
    def nodos(self):
        """Total de nodos de todos los niveles."""
        return sum(self.nodos_por_prof)

    @property
    def terminales(self):
        """Total de partidas terminadas (hojas)."""
        return sum(self.terminales_por_prof)


def enumerar_arbol_completo(tablero=None):
    """Recorre todo el árbol de juego (sin podar) y lo cuenta, sin guardar nodos."""
    est = EstadisticasArbol()
    tablero = tablero if tablero is not None else tablero_vacio()

    def rec(t, jugador, prof):
        """Visita `t`, lo cuenta y baja por cada jugada legal (sin utilidades ni poda)."""
        est.nodos_por_prof[prof] += 1
        est.posiciones.add(t)
        g = ganador(t)
        if g or esta_lleno(t):
            est.terminales_por_prof[prof] += 1
            est.victorias[g or "empate"] += 1
            return
        for m in movimientos_validos(t):
            rec(aplicar(t, m, jugador), oponente(jugador), prof + 1)

    rec(tablero, turno(tablero), 0)
    return est


def _miles(n):
    """12345 -> '12.345'."""
    return f"{n:,}".replace(",", ".")


def mostrar_estadisticas():
    """Opción 3 del menú: tabla de nodos por nivel y valor de cada primera jugada."""
    titulo("Árbol completo del gato (tablero vacío)")
    print("Recorriendo las 9 jugadas posibles en cada nivel... (unos segundos)\n")
    t0 = time.perf_counter()
    est = enumerar_arbol_completo()
    dt = time.perf_counter() - t0

    print(color("Nodos por nivel (profundidad = jugadas hechas)", "negrita"))
    print(f"  {'prof':>4}  {'quién mueve':>11}  {'nodos':>9}  {'terminales':>10}")
    for d in range(10):
        quien = "X" if d % 2 == 0 else "O"
        quien = quien if d < 9 else "—"
        print(f"  {d:>4}  {quien:>11}  {_miles(est.nodos_por_prof[d]):>9}  "
              f"{_miles(est.terminales_por_prof[d]):>10}")
    print(f"  {'':>4}  {'TOTAL':>11}  {_miles(est.nodos):>9}  {_miles(est.terminales):>10}\n")

    v = est.victorias
    print(f"Partidas posibles (hojas):  {_miles(est.terminales)}")
    print(f"  · gana X:  {_miles(v['X'])}   · gana O:  {_miles(v['O'])}   · empate:  {_miles(v['empate'])}")
    print(f"Posiciones distintas (sin repetir transposiciones): {_miles(len(est.posiciones))}")
    print(f"Cota ingenua 9! = 362.880 partidas llenas; las reales son {_miles(est.terminales)} "
          f"porque muchas terminan antes de llenar el tablero.")
    print(f"Tiempo de enumeración: {dt:.2f} s\n")

    print(color("Valor Minimax de cada primera jugada de X", "negrita"))
    t0 = time.perf_counter()
    valores = valores_por_movimiento(tablero_vacio(), "X")
    dt = time.perf_counter() - t0
    for fila in range(3):
        celdas = [f"{p}: {valores[p]:+d}" if valores[p] else f"{p}:  0"
                  for p in range(3 * fila + 1, 3 * fila + 4)]
        print("  " + "   ".join(celdas))
    print(f"\nTodas valen 0: con juego perfecto de ambos lados el gato SIEMPRE termina en empate. ({dt:.2f} s)")


# Posiciones sobre las que comparar() mide Minimax contra alfa-beta.
POSICIONES_COMPARACION = [
    ("Tablero vacío (mueve X)", tablero_vacio()),
    ("X en esquina (mueve O)", desde_texto("X........")),
    ("X centro, O esquina (mueve X)", desde_texto("O...X....")),
    ("Ejemplo A (4 libres)", EJEMPLOS["A"][1]),
    ("Ejemplo C (5 libres)", EJEMPLOS["C"][1]),
    ("Ejemplo B (3 libres)", EJEMPLOS["B"][1]),
]


def comparar():
    """Opción 4 del menú: corre ambos algoritmos en cada posición y compara nodos y tiempo."""
    titulo("Minimax vs. poda alfa-beta")
    cab = (f"  {'posición':<32} {'Minimax':>9} {'Alfa-beta':>10} {'ahorro':>7}  "
           f"{'t mm':>7} {'t ab':>7}  {'jugada':>6}")
    print(cab)
    print("  " + "─" * (len(cab) - 2))
    for nombre, t in POSICIONES_COMPARACION:
        t0 = time.perf_counter()
        a = minimax(t, construir_arbol=False)
        t1 = time.perf_counter()
        b = alfabeta(t, construir_arbol=False)
        t2 = time.perf_counter()
        igual = a.mejor_mov == b.mejor_mov and a.valor == b.valor
        ahorro = 100 * (1 - b.nodos / a.nodos)
        marca = color(f"{a.mejor_mov} = {b.mejor_mov}", "verde") if igual else color("¡difieren!", "rojo")
        print(f"  {nombre:<32} {_miles(a.nodos):>9} {_miles(b.nodos):>10} {ahorro:>6.1f}%  "
              f"{(t1 - t0) * 1000:>5.0f}ms {(t2 - t1) * 1000:>5.0f}ms  {marca}")
    print("\nAmbos algoritmos eligen la misma jugada y el mismo valor; alfa-beta solo se ahorra "
          "ramas que no pueden cambiar el resultado.")

    resp = pedir("\n¿Ver el árbol alfa-beta del ejemplo A con las ramas podadas (✂)? [s/N]: ").lower()
    if resp == "s":
        t = EJEMPLOS["A"][1]
        r = alfabeta(t, construir_arbol=True)
        print(f"\nPosición: {dibujar_mini(t)}   ·   nodos evaluados: {r.nodos}\n")
        imprimir_arbol(r.raiz, prof_max=99, mostrar_ab=True)
