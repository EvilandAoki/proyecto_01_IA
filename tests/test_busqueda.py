import heapq
import unittest
from collections import deque

from gato.busqueda import ALGORITMOS, astar, bfs, dfs, ucs
from gato.movil import CASOS, ProblemaMovil, distancia


def _estados_alcanzables(p):
    """Todos los estados a los que se llega desde el inicial (recorrido simple)."""
    vistos, cola = {p.estado_inicial}, deque([p.estado_inicial])
    while cola:
        s = cola.popleft()
        for a in p.acciones(s):
            r = p.resultado(s, a)
            if r not in vistos:
                vistos.add(r)
                cola.append(r)
    return vistos


def _costo_a_la_meta(p, estados):
    """Costo exacto desde cada estado hasta la meta más cercana.

    Las jugadas son reversibles y cuestan lo mismo en ambos sentidos, así que basta un
    Dijkstra desde TODAS las metas a la vez (independiente de gato/busqueda.py).
    """
    dist = {s: 0 for s in estados if p.es_meta(s)}
    heap = [(0, i, s) for i, s in enumerate(dist)]
    heapq.heapify(heap)
    n = len(heap)
    while heap:
        d, _, s = heapq.heappop(heap)
        if d > dist[s]:
            continue
        for a in p.acciones(s):
            r = p.resultado(s, a)
            nd = d + p.costo(s, a)
            if nd < dist.get(r, float("inf")):
                dist[r] = nd
                n += 1
                heapq.heappush(heap, (nd, n, r))
    return dist


class TestProblema(unittest.TestCase):
    def test_distancia_octil(self):
        self.assertEqual(distancia(0, 1, 3), 2)     # un paso recto
        self.assertEqual(distancia(0, 4, 3), 3)     # una diagonal
        self.assertEqual(distancia(0, 5, 3), 5)     # diagonal + recto
        self.assertEqual(distancia(0, 8, 3), 6)     # dos diagonales

    def test_acciones_no_pisan_fichas_ni_obstaculos(self):
        p = CASOS["1"]
        for a in p.acciones(p.estado_inicial):
            self.assertNotIn(a[1], p.estado_inicial)
            self.assertNotIn(a[1], p.o_fijas)

    def test_meta_solo_con_linea_completa_sin_obstaculos(self):
        p = ProblemaMovil("t", 3, 3, [4], [0, 1, 2])
        self.assertTrue(p.es_meta(frozenset({0, 1, 2})))
        self.assertFalse(p.es_meta(frozenset({0, 4, 8})))   # la diagonal tiene una O


class TestAlgoritmos(unittest.TestCase):
    def test_todos_encuentran_solucion_valida(self):
        for p in CASOS.values():
            for nombre, alg in ALGORITMOS.items():
                r = alg(p)
                self.assertTrue(r.encontrado, (p.nombre, nombre))
                s, costo = p.estado_inicial, 0
                for accion, estado in r.camino:     # se repite el camino jugada por jugada
                    self.assertIn(accion, p.acciones(s))
                    costo += p.costo(s, accion)
                    s = p.resultado(s, accion)
                    self.assertEqual(s, estado)
                self.assertTrue(p.es_meta(s), (p.nombre, nombre))
                self.assertEqual((costo, len(r.camino)), (r.costo, r.profundidad))

    def test_bfs_menos_pasos_ucs_menos_costo(self):
        for p in CASOS.values():
            b, u, d = bfs(p), ucs(p), dfs(p)
            self.assertLessEqual(b.profundidad, u.profundidad, p.nombre)
            self.assertLessEqual(b.profundidad, d.profundidad, p.nombre)
            self.assertLessEqual(u.costo, b.costo, p.nombre)
            self.assertLessEqual(u.costo, d.costo, p.nombre)

    def test_caso_donde_bfs_y_ucs_difieren(self):
        b, u = bfs(CASOS["2"]), ucs(CASOS["2"])
        self.assertEqual((b.costo, u.costo), (14, 10))
        self.assertEqual(b.profundidad, u.profundidad)

    def test_ucs_y_astar_dan_el_costo_optimo(self):
        for clave in ("1", "2", "3"):
            p = CASOS[clave]
            optimo = _costo_a_la_meta(p, _estados_alcanzables(p))[p.estado_inicial]
            self.assertEqual(ucs(p).costo, optimo, p.nombre)
            self.assertEqual(astar(p).costo, optimo, p.nombre)
            self.assertEqual(astar(p, p.heuristica_simple).costo, optimo, p.nombre)

    def test_astar_expande_menos_que_ucs(self):
        for p in CASOS.values():
            u, a = ucs(p), astar(p)
            self.assertLess(a.expandidos, u.expandidos, p.nombre)

    def test_sin_solucion(self):
        # Tres fichas encerradas: no hay línea libre de obstáculos.
        p = ProblemaMovil("t", 3, 3, [1, 3, 4, 5, 7], [0, 2, 8])
        for alg in (dfs, bfs, ucs, astar):
            self.assertFalse(alg(p).encontrado)

    def test_estado_inicial_ya_es_meta(self):
        p = ProblemaMovil("t", 3, 3, [], [0, 1, 2])
        for alg in (dfs, bfs, ucs, astar):
            r = alg(p)
            self.assertEqual((r.encontrado, r.costo, r.expandidos), (True, 0, 0))


class TestHeuristica(unittest.TestCase):
    def test_admisible_y_consistente(self):
        for clave in ("1", "2", "3"):
            p = CASOS[clave]
            estados = _estados_alcanzables(p)
            real = _costo_a_la_meta(p, estados)
            for h in (p.heuristica, p.heuristica_simple):
                for s in estados:
                    self.assertLessEqual(h(s), real[s], (p.nombre, sorted(s)))      # admisible
                    for a in p.acciones(s):                                         # consistente
                        self.assertLessEqual(h(s), p.costo(s, a) + h(p.resultado(s, a)))

    def test_cero_en_la_meta(self):
        for p in CASOS.values():
            meta = ucs(p).camino[-1][1]
            self.assertEqual(p.heuristica(meta), 0)
            self.assertEqual(p.heuristica_simple(meta), 0)

    def test_h1_domina_a_h2(self):
        for p in CASOS.values():
            for s in list(_estados_alcanzables(p))[:300]:
                self.assertGreaterEqual(p.heuristica(s), p.heuristica_simple(s))


if __name__ == "__main__":
    unittest.main()
