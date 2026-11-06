"""Capa de datos de la interfaz web: funciones puras, entrada validada -> dict listo para JSON.

No hay nada de HTTP aquí (eso es servidor.py), así que se puede probar sin levantar el servidor.
Todas las funciones lanzan ValueError con un mensaje en español si la entrada no es válida; el
servidor lo convierte en una respuesta de error.

Reutiliza la lógica que ya existe: minimax.py (búsqueda adversaria), busqueda.py (DFS/BFS/UCS/A*),
movil.py (casos), torneo.py y animacion.explicar_evento (frases de cada paso).
"""

import threading
import time

from ..animacion import EJEMPLOS, explicar_evento
from ..arbol import nodo_a_dict, numerar
from ..busqueda import ALGORITMOS, astar, medir
from ..consola import sin_color
from ..minimax import alfabeta, minimax
from ..movil import CASOS
from ..tablero import (LINEAS_GANADORAS, desde_texto, esta_lleno, ganador, movimientos_validos,
                       tablero_vacio, turno)
from ..torneo import (COMPETIDORES, PESOS, competencia_busqueda, evaluacion_posicional, torneo_gato)

LIMITE_NODOS_ARBOL = 1500     # más nodos que esto no se dibujan (ver arbol.nodo_a_dict)
LIMITE_TRAZA = 6000           # eventos de búsqueda que se envían; si hay más, se muestrea
EVALUADORES = {"lineas": None, "posicional": evaluacion_posicional}
ALGORITMOS_WEB = ["DFS", "BFS", "UCS", "A* (h1)", "A* (h2)"]

_cache = {}
_candado = threading.Lock()   # evita calcular dos veces lo mismo si llegan peticiones a la vez


def _guardado(clave, calcular):
    """Calcula `calcular()` una sola vez por `clave` (los resultados pesados se reutilizan)."""
    with _candado:
        if clave not in _cache:
            _cache[clave] = calcular()
        return _cache[clave]


# ------------------------------------------------------------------ validación

def _tablero(celdas):
    """Valida un tablero recibido como lista de 9 strings ('X', 'O' o ' ') y devuelve la tupla."""
    if not isinstance(celdas, list) or len(celdas) != 9 or any(c not in ("X", "O", " ") for c in celdas):
        raise ValueError("El tablero debe ser una lista de 9 celdas con 'X', 'O' o ' '.")
    t = tuple(celdas)
    x, o = t.count("X"), t.count("O")
    if x - o not in (0, 1):
        raise ValueError("Tablero imposible: X empieza, así que hay igual número de X y O, o una X más.")
    return t


def _entero(valor, nombre, minimo, maximo, defecto=None):
    """Entero en [minimo, maximo]; si `valor` es None devuelve `defecto`."""
    if valor is None:
        return defecto
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise ValueError(f"{nombre} debe ser un entero entre {minimo} y {maximo}.")
    return valor


def _evaluador(nombre):
    if nombre is None:
        nombre = "lineas"
    if nombre not in EVALUADORES:
        raise ValueError(f"Evaluación desconocida: {nombre!r}. Opciones: {', '.join(EVALUADORES)}.")
    return EVALUADORES[nombre]


def _num(v):
    """Valor apto para JSON (los infinitos pasan a texto)."""
    if v in (float("inf"), float("-inf")):
        return "+inf" if v > 0 else "-inf"
    return v


def _caso(clave):
    if clave not in CASOS:
        raise ValueError(f"Caso desconocido: {clave!r}. Opciones: {', '.join(CASOS)}.")
    return CASOS[clave]


# ------------------------------------------------------------------ catálogo

def casos():
    """Casos del Gato en movimiento y posiciones de ejemplo para el árbol de Minimax."""
    return {
        "casos": [{"id": k, "nombre": p.nombre, "n": p.n, "k": p.k,
                   "o_fijas": sorted(p.o_fijas), "x_iniciales": sorted(p.estado_inicial),
                   "lineas": [sorted(l) for l in p.lineas]} for k, p in CASOS.items()],
        "ejemplos": [{"id": k, "descripcion": desc, "tablero": list(t), "turno": turno(t)}
                     for k, (desc, t) in EJEMPLOS.items()],
        "algoritmos": ALGORITMOS_WEB,
        "lineas_ganadoras": [list(l) for l in LINEAS_GANADORAS],
    }


# ------------------------------------------------------------------ Gato adversario

def jugada(tablero, prof_max=None, evaluador=None):
    """Analiza la posición para quien le toca mover (la IA) y devuelve su razonamiento.

    Devuelve: mejor casilla, valor de cada casilla (Minimax exacto con el límite pedido), nodos
    evaluados con y sin poda, tiempo y si la partida ya terminó.
    """
    t = _tablero(tablero)
    prof_max = _entero(prof_max, "La profundidad límite", 1, 9)
    ev = _evaluador(evaluador)
    if ganador(t) or esta_lleno(t):
        raise ValueError("La partida ya terminó: no hay jugada que analizar.")
    t0 = time.perf_counter()
    # prof_arbol=1 guarda solo la raíz y sus hijos: lo justo para leer el valor de cada casilla.
    mm = minimax(t, construir_arbol=True, prof_arbol=1, prof_max=prof_max, evaluador=ev)
    ms = (time.perf_counter() - t0) * 1000
    ab = alfabeta(t, construir_arbol=False, prof_max=prof_max, evaluador=ev)
    return {
        "ia": turno(t), "mejor": mm.mejor_mov, "valor": _num(mm.valor),
        "valores": {str(h.movimiento): _num(h.valor) for h in mm.raiz.hijos},
        "nodos_minimax": mm.nodos, "nodos_alfabeta": ab.nodos,
        "ahorro": round(100 * (1 - ab.nodos / mm.nodos), 1) if mm.nodos else 0.0,
        "misma_jugada": mm.mejor_mov == ab.mejor_mov and mm.valor == ab.valor,
        "ms": round(ms, 2), "prof_max": prof_max,
        "libres": len(movimientos_validos(t)),
    }


def arbol(tablero, poda=True, prof_max=None, evaluador=None):
    """Árbol de búsqueda de la posición, más la lista de eventos para animarlo paso a paso.

    Cada evento trae: tipo (entrar, hoja, corte, subir, poda), id del nodo, valor, alfa, beta y la
    frase explicativa (la misma que usa la animación de consola).
    """
    t = _tablero(tablero)
    prof_max = _entero(prof_max, "La profundidad límite", 1, 9)
    ev = _evaluador(evaluador)
    if ganador(t) or esta_lleno(t):
        raise ValueError("La partida ya terminó: no hay árbol que mostrar.")
    algoritmo = alfabeta if poda else minimax
    # Contar antes de construir: si el árbol es enorme, avisar sin gastar memoria.
    previo = algoritmo(t, construir_arbol=False, prof_max=prof_max, evaluador=ev)
    if previo.nodos > LIMITE_NODOS_ARBOL:
        raise ValueError(f"El árbol tiene {previo.nodos} nodos y el máximo para dibujarlo es "
                         f"{LIMITE_NODOS_ARBOL}. Baja la profundidad límite o elige una posición "
                         "con menos casillas libres.")
    crudos = []
    resultado = algoritmo(t, construir_arbol=True, prof_max=prof_max, evaluador=ev,
                          callback=lambda e, n, valor=None, alfa=None, beta=None:
                          crudos.append((e, n, valor, alfa, beta)))
    ids = numerar(resultado.raiz)
    valores, eventos = {}, []
    with sin_color():
        for e, n, valor, alfa, beta in crudos:
            if e in ("hoja", "corte", "subir"):
                valores[id(n)] = valor
            eventos.append({"tipo": e, "nodo": ids[id(n)], "valor": _num(valor),
                            "alfa": _num(alfa), "beta": _num(beta),
                            "texto": explicar_evento(e, n, valor, alfa, beta, valores, poda)})
    return {"nodos": nodo_a_dict(resultado.raiz, ids, LIMITE_NODOS_ARBOL), "eventos": eventos,
            "evaluados": resultado.nodos, "valor": _num(resultado.valor),
            "mejor": resultado.mejor_mov, "poda": poda, "ia": turno(t),
            "total_sin_poda": minimax(t, construir_arbol=False, prof_max=prof_max, evaluador=ev).nodos}


# ------------------------------------------------------------------ Gato en movimiento

def _ejecutar(problema, nombre, traza=None):
    """Corre un competidor del Gato en movimiento (con o sin traza)."""
    if nombre == "A* (h1)":
        return astar(problema, traza=traza)
    if nombre == "A* (h2)":
        return astar(problema, heuristica=problema.heuristica_simple, traza=traza)
    return ALGORITMOS[nombre](problema, traza=traza)


def _medido(problema, nombre):
    if nombre == "A* (h1)":
        return medir(astar, problema)
    if nombre == "A* (h2)":
        return medir(astar, problema, heuristica=problema.heuristica_simple)
    return medir(ALGORITMOS[nombre], problema)


def _resumen(r):
    return {"encontrado": r.encontrado, "costo": r.costo, "pasos": r.profundidad,
            "expandidos": r.expandidos, "generados": r.generados, "memoria_nodos": r.max_memoria,
            "memoria_bytes": r.pico_bytes, "ms": round(r.tiempo_ms, 2)}


def busqueda(caso, algoritmo):
    """Resuelve un caso con un algoritmo y devuelve solución, métricas y traza de expansiones.

    traza: un evento por nodo expandido [estado, g, f, tamaño_frontera, tamaño_explorados]; si hay
    más de LIMITE_TRAZA se muestrea (y `muestreo` dice cada cuántos se guardó uno).
    """
    problema = _caso(caso)
    if algoritmo not in ALGORITMOS_WEB:
        raise ValueError(f"Algoritmo desconocido: {algoritmo!r}. Opciones: {', '.join(ALGORITMOS_WEB)}.")

    def calcular():
        h = {"A* (h1)": problema.heuristica, "A* (h2)": problema.heuristica_simple}.get(algoritmo)
        eventos = []

        def traza(nodo, frontera, explorados):
            eventos.append([sorted(nodo.estado), nodo.g, nodo.g + (h(nodo.estado) if h else 0),
                            frontera, explorados])

        r = _ejecutar(problema, algoritmo, traza)
        m = _medido(problema, algoritmo)
        paso = -(-len(eventos) // LIMITE_TRAZA)       # techo de len / LIMITE
        muestreados = eventos[::paso]
        if eventos and muestreados[-1] is not eventos[-1]:
            muestreados.append(eventos[-1])
        camino, estado = [], problema.estado_inicial
        for accion, nuevo in r.camino:
            camino.append({"accion": list(accion), "texto": problema.describir(accion),
                           "costo": problema.costo(estado, accion), "estado": sorted(nuevo)})
            estado = nuevo
        return {"caso": caso, "algoritmo": algoritmo, "metricas": _resumen(m), "camino": camino,
                "inicial": sorted(problema.estado_inicial), "traza": muestreados,
                "muestreo": paso, "expandidos_totales": len(eventos)}

    return _guardado(("busqueda", caso, algoritmo), calcular)


# ------------------------------------------------------------------ comparaciones

def comparacion():
    """Métricas crudas de los 5 competidores en todos los casos (el navegador calcula puntajes)."""
    def calcular():
        comp = competencia_busqueda()
        return {"competidores": COMPETIDORES, "pesos": PESOS,
                "casos": [{"nombre": nombre,
                           "resultados": {n: _resumen(r) for n, r in rs.items()}}
                          for nombre, rs in comp["resultados"].items()]}
    return _guardado(("comparacion",), calcular)


POSICIONES_PODA = [("Tablero vacío (mueve X)", tablero_vacio(), [1, 2, 3, 4, 5, 6, 9]),
                   ("X en el centro (mueve O)", desde_texto("....X...."), [1, 2, 3, 4, 5, 6, 8])]


def poda():
    """Nodos evaluados con y sin poda según la profundidad límite (para la gráfica de ahorro)."""
    def calcular():
        filas = []
        for nombre, t, profundidades in POSICIONES_PODA:
            serie = []
            for d in profundidades:
                a = minimax(t, construir_arbol=False, prof_max=d)
                b = alfabeta(t, construir_arbol=False, prof_max=d)
                serie.append({"prof": d, "minimax": a.nodos, "alfabeta": b.nodos,
                              "ahorro": round(100 * (1 - b.nodos / a.nodos), 1)})
            filas.append({"posicion": nombre, "serie": serie})
        return {"posiciones": filas}
    return _guardado(("poda",), calcular)


def torneo(partidas=10):
    """Ranking y matriz del torneo de gato (semilla fija: el resultado es reproducible)."""
    partidas = _entero(partidas, "El número de aperturas", 1, 50, 10)

    def calcular():
        res = torneo_gato(partidas=partidas, semilla=1)
        orden = res.ranking()
        return {"partidas_por_pareja": 2 * partidas,
                "ranking": [{"nombre": n, "partidas": res.partidas(n), "ganadas": res.ganadas[n],
                             "empatadas": res.empatadas[n], "perdidas": res.perdidas[n],
                             "puntos": res.puntos(n)} for n in orden],
                "matriz": [[None if a == b else round(res.versus[(a, b)][0] / res.versus[(a, b)][1], 4)
                            for b in orden] for a in orden],
                "orden": orden}
    return _guardado(("torneo", partidas), calcular)
