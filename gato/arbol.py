"""Nodo del árbol de juego y dibujo del árbol en ASCII."""

from dataclasses import dataclass, field

from .consola import color, sin_color
from .tablero import dibujar_mini, ganador


@dataclass(slots=True)
class Nodo:
    """Un nodo del árbol de búsqueda. Lo crea minimax._evaluar y lo lee el dibujo/animación.

    Un nodo = una posición del tablero alcanzada tras una jugada concreta.
    """
    tablero: tuple
    movimiento: int | None      # jugada que llevó a este nodo (None en la raíz)
    turno: str                  # jugador al que le toca mover en este nodo
    profundidad: int
    tipo: str = ""              # 'MAX', 'MIN', 'HOJA' (terminal), 'CORTE' (profundidad límite) o 'PODA'
    valor: int | None = None    # valor minimax que este nodo "sube" a su padre
    hijos: list = field(default_factory=list)
    elegido: int | None = None  # jugada hija con mejor valor
    podado: bool = False        # rama descartada por alfa-beta (nunca se evaluó)
    alfa: float | None = None   # α al terminar el nodo (solo con poda; si no, None)
    beta: float | None = None   # β al terminar el nodo (solo con poda; si no, None)
    sub: int = 0                # nodos evaluados en su subárbol (incluyéndose)


def contar_nodos(raiz):
    """Cuenta nodos guardados. juego._menu_razonamiento lo compara con res.nodos para saber
    si el árbol quedó truncado."""
    """Nodos evaluados guardados en el árbol (las ramas podadas no cuentan)."""
    if raiz.podado:
        return 0
    return 1 + sum(contar_nodos(h) for h in raiz.hijos)


def fmt_valor(v):
    """Formatea un valor: +3, -2, 0, +∞, -∞ o ? (sin calcular). Los decimales (evaluaciones) con 2 cifras."""
    if v is None:
        return "?"
    if v in (float("inf"), float("-inf")):
        return "+∞" if v > 0 else "-∞"
    if isinstance(v, float):
        return f"{v:+.2f}"
    return f"{v:+d}" if v else "0"


def _etiqueta(n):
    """(tipo, texto extra) de un nodo: las hojas dicen quién ganó o 'empate'."""
    if n.tipo == "HOJA":
        g = ganador(n.tablero)
        return "HOJA", f"gana {g}" if g else "empate"
    if n.tipo == "CORTE":
        return "CORTE", "evaluación heurística"
    return (f"{n.tipo}({n.turno})" if n.tipo else "?"), ""


def imprimir_arbol(raiz, prof_max=2, solo_mejor=False, visible=None, valores=None,
                   actual=None, mostrar_ab=False, salida=print):
    """Dibuja el árbol con ├── y └──.

    prof_max    -- niveles bajo la raíz que se detallan; el resto se resume como "… N nodos".
    solo_mejor  -- muestra únicamente la rama elegida (la variante principal).
    visible     -- conjunto de id(nodo) a mostrar (la animación lo va ampliando).
    valores     -- dict id(nodo) -> valor ya calculado (en la animación; None = todo el árbol final).
    actual      -- nodo que se está procesando (se marca con ▶).
    mostrar_ab  -- muestra α/β de cada nodo (para alfa-beta).
    """
    animando = valores is not None

    def linea(n):
        """Texto de una sola línea para el nodo `n`."""
        if n.podado:
            ab = ""
            if n.alfa is not None:
                ab = f"  (β={fmt_valor(n.beta)} ≤ α={fmt_valor(n.alfa)})"
            return color(f"✂ mov={n.movimiento}  podado{ab}", "gris")
        tipo, extra = _etiqueta(n)
        tcolor = {"MAX": "cian", "MIN": "magenta", "HOJA": "amarillo", "CORTE": "azul"}.get(n.tipo, "gris")
        v = valores.get(id(n)) if animando else n.valor
        mov = f"mov={n.movimiento}" if n.movimiento else "raíz"
        partes = [color(f"[{tipo}]", tcolor), mov, f"v={fmt_valor(v)}", dibujar_mini(n.tablero)]
        if extra:
            partes.append(extra)
        if mostrar_ab and n.alfa is not None and n.tipo not in ("HOJA", "CORTE"):
            partes.append(color(f"α={fmt_valor(n.alfa)} β={fmt_valor(n.beta)}", "gris"))
        return "  ".join(partes)

    def hijos_visibles(n, en_pv):
        """Filtra los hijos a dibujar (por `visible` y/o por solo_mejor)."""
        hs = n.hijos
        if visible is not None:
            hs = [h for h in hs if id(h) in visible]
        if solo_mejor:
            hs = [h for h in hs if en_pv and h.movimiento == n.elegido]
        return hs

    def rec(n, prefijo, ultimo, es_raiz, en_pv):
        """Dibuja `n` y baja a sus hijos. en_pv = 'estoy en la variante principal' (rama verde)."""
        resaltado = en_pv and not animando and not n.podado and not es_raiz
        if resaltado or actual is n:
            # Una sola capa de color: los colores internos cortarían el resaltado.
            with sin_color():
                texto = linea(n)
            texto = color("▶ " + texto if actual is n else texto,
                          *(("amarillo", "negrita") if actual is n else ("verde", "negrita")))
        else:
            texto = linea(n)
        if es_raiz:
            salida(texto)
            hijo_prefijo = ""
        else:
            salida(prefijo + ("└── " if ultimo else "├── ") + texto)
            hijo_prefijo = prefijo + ("    " if ultimo else "│   ")
        if n.podado:
            return
        if n.profundidad - raiz.profundidad >= prof_max:
            if n.sub > 1 and visible is None:
                salida(hijo_prefijo + "└── " + color(f"… ({n.sub - 1} nodos más)", "gris"))
            return
        hs = hijos_visibles(n, en_pv)
        for i, h in enumerate(hs):
            hijo_en_pv = en_pv and n.elegido == h.movimiento and not animando
            rec(h, hijo_prefijo, i == len(hs) - 1, False, hijo_en_pv)

    rec(raiz, "", True, True, True)


def exportar_arbol(raiz, ruta):
    """Vuelca el árbol completo (guardado) a un archivo de texto. Devuelve nº de líneas."""
    lineas = []
    with sin_color():
        imprimir_arbol(raiz, prof_max=99, mostrar_ab=raiz.alfa is not None,
                       salida=lineas.append)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    return len(lineas)


def numerar(raiz):
    """Asigna un entero a cada nodo del árbol (recorrido en preorden). Devuelve {id(nodo): n}.

    Los objetos Nodo no tienen un identificador estable fuera de Python; la interfaz web necesita
    uno para referirse a los nodos en los eventos.
    """
    ids = {}

    def rec(n):
        ids[id(n)] = len(ids)
        for h in n.hijos:
            rec(h)

    rec(raiz)
    return ids


def _num(v):
    """Valor apto para JSON: los infinitos pasan a texto ('+inf', '-inf')."""
    if v in (float("inf"), float("-inf")):
        return "+inf" if v > 0 else "-inf"
    return v


def nodo_a_dict(raiz, ids, limite=1500):
    """Lista plana de nodos (dicts) lista para JSON. Lanza ValueError si hay más de `limite`.

    Cada nodo trae `padre` (id del nodo padre, None en la raíz) para reconstruir el árbol.
    """
    if len(ids) > limite:
        raise ValueError(f"El árbol tiene {len(ids)} nodos y el máximo para dibujarlo es {limite}. "
                         "Baja la profundidad límite o elige una posición con menos casillas libres.")
    nodos = []

    def rec(n, padre):
        nodos.append({"id": ids[id(n)], "padre": padre, "mov": n.movimiento, "turno": n.turno,
                      "prof": n.profundidad, "tipo": n.tipo, "valor": _num(n.valor),
                      "alfa": _num(n.alfa), "beta": _num(n.beta), "podado": n.podado,
                      "elegido": n.elegido, "tablero": list(n.tablero), "sub": n.sub})
        for h in n.hijos:
            rec(h, ids[id(n)])

    rec(raiz, None)
    return nodos
