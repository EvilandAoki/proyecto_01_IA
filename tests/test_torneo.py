import unittest

from gato.minimax import alfabeta
from gato.tablero import desde_texto, tablero_vacio
from gato.torneo import (COMPETIDORES, JUGADORES, PESOS, Jugador, _puntos_por_criterio,
                         competencia_busqueda, evaluacion_posicional, jugar_partida,
                         torneo_gato)
import random


class TestTorneoGato(unittest.TestCase):
    def test_evaluacion_posicional_acotada(self):
        for t in (tablero_vacio(), desde_texto("XOX/OXO/OXO"), desde_texto("X.O/.X./O.X")):
            for ia in "XO":
                self.assertLess(abs(evaluacion_posicional(t, ia)), 1)

    def test_evaluador_personalizado_se_usa(self):
        # Con un evaluador constante, todos los cortes valen lo mismo y el valor de la raíz también.
        r = alfabeta(tablero_vacio(), construir_arbol=False, prof_max=2, evaluador=lambda t, ia: 0.5)
        self.assertEqual(r.valor, 0.5)

    def test_completo_contra_completo_siempre_empata_sin_apertura(self):
        p = Jugador("completo")
        self.assertIsNone(jugar_partida(p, p, [], random.Random(0)))

    def test_completo_no_pierde_contra_aleatorio_sin_apertura(self):
        completo, azar = Jugador("completo"), Jugador("azar", aleatorio=True)
        for semilla in range(30):
            rng = random.Random(semilla)
            self.assertNotEqual(jugar_partida(azar, completo, [], rng), "X")
            self.assertNotEqual(jugar_partida(completo, azar, [], rng), "O")

    def test_torneo_reproducible_y_marcador_consistente(self):
        a, b = torneo_gato(partidas=3, semilla=7), torneo_gato(partidas=3, semilla=7)
        self.assertEqual(a.ganadas, b.ganadas)
        n = len(JUGADORES)
        self.assertEqual(sum(a.ganadas.values()), sum(a.perdidas.values()))
        # cada pareja juega 2 * partidas; cada jugador enfrenta a los otros n - 1
        for j in JUGADORES:
            self.assertEqual(a.partidas(j.nombre), 2 * 3 * (n - 1))
        # puntos totales = partidas jugadas en total (cada partida reparte exactamente 1 punto)
        self.assertEqual(sum(a.puntos(j.nombre) for j in JUGADORES), n * (n - 1) / 2 * 2 * 3)

    def test_el_aleatorio_queda_ultimo(self):
        res = torneo_gato(partidas=10, semilla=1)
        self.assertEqual(res.ranking()[-1], "Aleatorio")


class TestCompetenciaBusqueda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.comp = competencia_busqueda()     # tarda unos segundos: se corre una sola vez

    def test_puntos_con_empates(self):
        pts = _puntos_por_criterio({"a": 5, "b": 5, "c": 9, "d": 1})
        self.assertEqual(pts, {"a": 2, "b": 2, "c": 0, "d": 3})

    def test_los_optimos_se_llevan_todos_los_puntos_de_costo(self):
        comp = self.comp
        casos = len(comp["resultados"])
        tope = (len(COMPETIDORES) - 1) * casos
        for n in ("UCS", "A* (h1)", "A* (h2)"):
            self.assertEqual(comp["criterios"]["costo"][n], tope, n)
        self.assertLess(comp["criterios"]["costo"]["DFS"], tope)

    def test_total_ponderado(self):
        comp = self.comp
        for n in COMPETIDORES:
            self.assertEqual(comp["total"][n],
                             sum(PESOS[c] * comp["criterios"][c][n] for c in PESOS))
            self.assertLessEqual(comp["total"][n], comp["maximo"])


if __name__ == "__main__":
    unittest.main()
