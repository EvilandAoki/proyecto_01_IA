import unittest

from gato.arbol import contar_nodos
from gato.estadisticas import POSICIONES_COMPARACION, enumerar_arbol_completo
from gato.minimax import alfabeta, evaluacion, minimax, valores_por_movimiento
from gato.tablero import (LINEAS_GANADORAS, aplicar, desde_texto, esta_lleno, ganador,
                          movimientos_validos, oponente, tablero_vacio, turno)


class TestTablero(unittest.TestCase):
    def test_detecta_las_8_lineas(self):
        for linea in LINEAS_GANADORAS:
            for jugador in "XO":
                celdas = [" "] * 9
                for i in linea:
                    celdas[i] = jugador
                self.assertEqual(ganador(tuple(celdas)), jugador, linea)

    def test_empate_y_sin_ganador(self):
        t = desde_texto("XOX/XOO/OXX")
        self.assertIsNone(ganador(t))
        self.assertTrue(esta_lleno(t))
        self.assertIsNone(ganador(tablero_vacio()))

    def test_turno_y_aplicar(self):
        t = tablero_vacio()
        self.assertEqual(turno(t), "X")
        t2 = aplicar(t, 5, "X")
        self.assertEqual(t2[4], "X")
        self.assertEqual(t, tablero_vacio())          # no muta el original
        self.assertEqual(turno(t2), "O")
        self.assertNotIn(5, movimientos_validos(t2))


class TestArbolCompleto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.est = enumerar_arbol_completo()

    def test_conteos_conocidos(self):
        self.assertEqual(self.est.nodos, 549_946)
        self.assertEqual(self.est.terminales, 255_168)
        self.assertEqual(self.est.victorias, {"X": 131_184, "O": 77_904, "empate": 46_080})
        self.assertEqual(len(self.est.posiciones), 5_478)

    def test_nodos_por_nivel(self):
        self.assertEqual(self.est.nodos_por_prof,
                         [1, 9, 72, 504, 3024, 15120, 54720, 148176, 200448, 127872])


class TestMinimax(unittest.TestCase):
    def test_gato_perfecto_es_empate(self):
        r = minimax(tablero_vacio(), construir_arbol=False)
        self.assertEqual(r.valor, 0)
        self.assertEqual(r.nodos, 549_946)
        self.assertTrue(all(v == 0 for v in valores_por_movimiento(tablero_vacio()).values()))

    def test_gana_de_inmediato(self):
        t = desde_texto("XX./OO./...")        # X y O a un paso; mueve X
        self.assertEqual(minimax(t).mejor_mov, 3)
        self.assertEqual(alfabeta(t).mejor_mov, 3)

    def test_bloquea(self):
        t = desde_texto("XX./.O./...")        # mueve O: debe bloquear en 3
        self.assertEqual(turno(t), "O")
        self.assertEqual(minimax(t).mejor_mov, 3)
        self.assertEqual(alfabeta(t).mejor_mov, 3)

    def test_prefiere_ganar_rapido(self):
        r = minimax(desde_texto("XOX/OXO/..."))
        self.assertEqual(r.mejor_mov, 7)
        self.assertEqual(r.valor, 9)           # 10 - profundidad 1

    def test_arbol_guardado_es_consistente(self):
        r = minimax(desde_texto("XOX/.O./.X."))
        self.assertEqual(contar_nodos(r.raiz), r.nodos)
        self.assertEqual(r.raiz.valor, r.valor)

    def test_prof_arbol_no_cambia_el_resultado(self):
        a = minimax(tablero_vacio(), construir_arbol=False)
        b = minimax(tablero_vacio(), prof_arbol=2)
        self.assertEqual((a.mejor_mov, a.valor, a.nodos), (b.mejor_mov, b.valor, b.nodos))
        self.assertLess(contar_nodos(b.raiz), b.nodos)


class TestAlfaBeta(unittest.TestCase):
    def test_mismo_resultado_y_menos_nodos(self):
        for nombre, t in POSICIONES_COMPARACION:
            a = minimax(t, construir_arbol=False)
            b = alfabeta(t, construir_arbol=False)
            self.assertEqual((a.mejor_mov, a.valor), (b.mejor_mov, b.valor), nombre)
            self.assertLessEqual(b.nodos, a.nodos, nombre)

    def test_arbol_guardado_cuenta_solo_evaluados(self):
        t = desde_texto("XOX/.O./.X.")
        r = alfabeta(t)
        self.assertEqual(contar_nodos(r.raiz), r.nodos)
        self.assertLess(r.nodos, minimax(t).nodos)

    def test_igual_en_todas_las_posiciones_alcanzables_pequenas(self):
        # Todas las posiciones con <= 6 casillas libres alcanzables jugando limpio.
        vistas = set()

        def rec(t):
            if t in vistas or ganador(t) or esta_lleno(t):
                return
            vistas.add(t)
            if len(movimientos_validos(t)) <= 6:
                a, b = minimax(t, construir_arbol=False), alfabeta(t, construir_arbol=False)
                self.assertEqual((a.mejor_mov, a.valor), (b.mejor_mov, b.valor), t)
            for m in movimientos_validos(t):
                rec(aplicar(t, m, turno(t)))

        rec(tablero_vacio())
        self.assertGreater(len(vistas), 1000)


class TestLaIANuncaPierde(unittest.TestCase):
    def _probar(self, ia):
        """El humano prueba TODAS sus jugadas posibles; la IA responde con alfa-beta."""
        cache = {}
        partidas = [0]

        def rec(t):
            g = ganador(t)
            if g or esta_lleno(t):
                partidas[0] += 1
                self.assertNotEqual(g, oponente(ia), f"La IA perdió: {t}")
                return
            if turno(t) == ia:
                if t not in cache:
                    cache[t] = alfabeta(t, ia, construir_arbol=False).mejor_mov
                rec(aplicar(t, cache[t], ia))
            else:
                for m in movimientos_validos(t):
                    rec(aplicar(t, m, oponente(ia)))

        rec(tablero_vacio())
        self.assertGreater(partidas[0], 50)   # se recorrieron muchas partidas, no un caso aislado

    def test_ia_como_x(self):
        self._probar("X")

    def test_ia_como_o(self):
        self._probar("O")

    def test_minimax_puro_tambien_como_o(self):
        # Con O, la IA responde a cada primera jugada de X con minimax puro.
        for m in range(1, 10):
            t = aplicar(tablero_vacio(), m, "X")
            self.assertEqual(minimax(t, "O", construir_arbol=False).valor, 0)


if __name__ == "__main__":
    unittest.main()


class TestProfundidadLimite(unittest.TestCase):
    def test_evaluacion_nunca_supera_una_victoria(self):
        # En todas las posiciones no terminales alcanzables: |evaluacion| < 1.
        vistas = set()

        def rec(t):
            if t in vistas or ganador(t) or esta_lleno(t):
                return
            vistas.add(t)
            for ia in "XO":
                self.assertLess(abs(evaluacion(t, ia)), 1, t)
            for m in movimientos_validos(t):
                rec(aplicar(t, m, turno(t)))

        rec(tablero_vacio())

    def test_evaluacion_prefiere_centro_y_dobles(self):
        self.assertGreater(evaluacion(desde_texto("....X...."), "X"), 0)
        self.assertLess(evaluacion(desde_texto("....X...."), "O"), 0)
        # Dos fichas en una línea abierta valen más que una sola.
        self.assertGreater(evaluacion(desde_texto("XX.O.O..."), "X"),
                           evaluacion(desde_texto("X..O.O..."), "X"))

    def test_none_equivale_a_profundidad_9(self):
        t = desde_texto("XOX/.O./.X.")
        a, b = minimax(t, construir_arbol=False), minimax(t, construir_arbol=False, prof_max=9)
        self.assertEqual((a.mejor_mov, a.valor, a.nodos), (b.mejor_mov, b.valor, b.nodos))

    def test_alfabeta_igual_que_minimax_en_cada_profundidad(self):
        for t, maxima in ((desde_texto("XOX/.O./.X."), 9), (desde_texto("X........"), 6),
                          (tablero_vacio(), 5)):
            for d in range(1, maxima + 1):
                a = minimax(t, construir_arbol=False, prof_max=d)
                b = alfabeta(t, construir_arbol=False, prof_max=d)
                self.assertEqual((a.mejor_mov, a.valor), (b.mejor_mov, b.valor), (t, d))
                self.assertLessEqual(b.nodos, a.nodos)

    def test_limite_reduce_nodos_y_marca_cortes(self):
        t = tablero_vacio()
        r = minimax(t, prof_max=3)
        self.assertEqual(r.nodos, 1 + 9 + 72 + 504)
        self.assertEqual(contar_nodos(r.raiz), r.nodos)
        tipos = {h.tipo for h in r.raiz.hijos[0].hijos[0].hijos}
        self.assertEqual(tipos, {"CORTE"})

    def test_con_limite_no_deja_ganar_en_una_jugada(self):
        # Aun a profundidad 2 bloquea (ve su jugada y la respuesta del rival).
        t = desde_texto("XX./.O./...")
        self.assertEqual(minimax(t, "O", construir_arbol=False, prof_max=2).mejor_mov, 3)
