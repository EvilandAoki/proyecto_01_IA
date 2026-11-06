import http.client
import json
import shutil
import subprocess
import threading
import unittest
from pathlib import Path

from gato.arbol import numerar
from gato.busqueda import ALGORITMOS, astar, dfs
from gato.movil import CASOS
from gato.tablero import desde_texto
from gato.web import api
from gato.web.servidor import ESTATICOS, crear_servidor

VACIO = [" "] * 9
EJEMPLO_A = list(desde_texto("XOX/.O./.X."))


class TestApi(unittest.TestCase):
    def test_casos_y_ejemplos(self):
        c = api.casos()
        self.assertEqual(len(c["casos"]), len(CASOS))
        self.assertEqual({e["id"] for e in c["ejemplos"]}, {"A", "B", "C"})
        self.assertEqual(c["algoritmos"], ["DFS", "BFS", "UCS", "A* (h1)", "A* (h2)"])

    def test_jugada_tiene_nodos_con_y_sin_poda(self):
        j = api.jugada(["X"] + [" "] * 8, prof_max=3)
        self.assertEqual(j["ia"], "O")
        self.assertLess(j["nodos_alfabeta"], j["nodos_minimax"])
        self.assertTrue(j["misma_jugada"])
        self.assertIn(str(j["mejor"]), j["valores"])
        json.dumps(j, allow_nan=False)        # sin infinitos sueltos

    def test_entradas_invalidas(self):
        for malo in (None, [], ["X"] * 9, [" "] * 8, ["Z"] + [" "] * 8):
            with self.assertRaises(ValueError):
                api.jugada(malo)
        with self.assertRaises(ValueError):
            api.jugada(VACIO, prof_max=0)
        with self.assertRaises(ValueError):
            api.jugada(VACIO, prof_max=True)
        with self.assertRaises(ValueError):
            api.jugada(VACIO, evaluador="inventado")
        with self.assertRaises(ValueError):                 # partida ya terminada
            api.jugada(list("XXXOO    "))
        with self.assertRaises(ValueError):
            api.busqueda("9", "BFS")
        with self.assertRaises(ValueError):
            api.busqueda("1", "Dijkstra")

    def test_arbol_con_poda_coincide_con_minimax(self):
        a, m = api.arbol(EJEMPLO_A, poda=True), api.arbol(EJEMPLO_A, poda=False)
        self.assertEqual((a["evaluados"], m["evaluados"]), (29, 61))
        self.assertEqual(a["total_sin_poda"], 61)
        self.assertEqual((a["mejor"], a["valor"]), (m["mejor"], m["valor"]))
        # cada nodo evaluado aparece una vez como evento "entrar"
        self.assertEqual(sum(e["tipo"] == "entrar" for e in a["eventos"]), a["evaluados"])
        ids = {n["id"] for n in a["nodos"]}
        self.assertTrue(all(e["nodo"] in ids for e in a["eventos"]))
        self.assertEqual(sum(e["tipo"] == "poda" for e in a["eventos"]), 11)
        self.assertTrue(all(e["texto"] for e in a["eventos"]))
        self.assertNotIn("\x1b", json.dumps(a))              # sin códigos de color de la consola
        json.dumps(a, allow_nan=False)

    def test_arbol_con_limite_marca_cortes(self):
        a = api.arbol(["X"] + [" "] * 8, poda=True, prof_max=2)
        self.assertIn("CORTE", {n["tipo"] for n in a["nodos"]})
        self.assertIn("corte", {e["tipo"] for e in a["eventos"]})

    def test_arbol_demasiado_grande_se_rechaza_con_mensaje(self):
        with self.assertRaisesRegex(ValueError, "máximo para dibujarlo"):
            api.arbol(VACIO, poda=True)

    def test_busqueda_traza_y_metricas(self):
        for alg, funcion in (("BFS", ALGORITMOS["BFS"]), ("A* (h1)", astar), ("DFS", dfs)):
            d = api.busqueda("2", alg)
            r = funcion(CASOS["2"])
            self.assertEqual(d["metricas"]["costo"], r.costo, alg)
            self.assertEqual(d["metricas"]["expandidos"], r.expandidos, alg)
            self.assertEqual(d["expandidos_totales"], r.expandidos, alg)     # la traza ve cada expansión
            self.assertEqual(len(d["camino"]), r.profundidad)
            ultimo = d["camino"][-1]["estado"]
            self.assertIn(frozenset(ultimo), CASOS["2"].lineas)               # termina en una línea
            json.dumps(d, allow_nan=False)

    def test_traza_no_cambia_el_resultado(self):
        eventos = []
        con = astar(CASOS["3"], traza=lambda n, f, e: eventos.append((f, e)))
        sin = astar(CASOS["3"])
        self.assertEqual((con.costo, con.expandidos, con.generados), (sin.costo, sin.expandidos, sin.generados))
        self.assertEqual(len(eventos), sin.expandidos)

    def test_traza_se_muestrea_si_es_enorme(self):
        d = api.busqueda("4", "UCS")             # UCS 5x5 expande 8.060 nodos
        self.assertGreater(d["muestreo"], 1)
        self.assertLessEqual(len(d["traza"]), api.LIMITE_TRAZA + 1)
        self.assertEqual(d["expandidos_totales"], d["metricas"]["expandidos"])

    def test_numerar_es_unico(self):
        from gato.minimax import alfabeta
        raiz = alfabeta(desde_texto("XOX/.O./.X.")).raiz
        ids = numerar(raiz)
        self.assertEqual(sorted(ids.values()), list(range(len(ids))))

    def test_poda_y_torneo(self):
        p = api.poda()
        self.assertTrue(all(s["alfabeta"] <= s["minimax"] for pos in p["posiciones"] for s in pos["serie"]))
        t = api.torneo(3)
        self.assertEqual(t["orden"][-1], "Aleatorio")
        self.assertEqual(len(t["matriz"]), len(t["orden"]))
        with self.assertRaises(ValueError):
            api.torneo(0)


class TestServidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = crear_servidor(0)                       # puerto libre
        cls.puerto = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def pedir(self, metodo, ruta, cuerpo=None, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=30)
        cabeceras = {"Content-Type": "application/json"}
        if host:
            cabeceras["Host"] = host
        c.request(metodo, ruta, body=json.dumps(cuerpo) if cuerpo is not None else None, headers=cabeceras)
        r = c.getresponse()
        datos = r.read()
        c.close()
        return r.status, r.getheader("Content-Type"), datos

    def test_pagina_y_estaticos(self):
        estado, tipo, cuerpo = self.pedir("GET", "/")
        self.assertEqual(estado, 200)
        self.assertIn("text/html", tipo)
        self.assertIn(b"Gato y algoritmos", cuerpo)
        for js in ("app.js", "tablero.js", "arbol.js", "busqueda.js", "graficos.js", "paginas.js", "estilos.css"):
            self.assertEqual(self.pedir("GET", "/" + js)[0], 200, js)

    def test_api_ok_y_errores(self):
        estado, tipo, cuerpo = self.pedir("GET", "/api/casos")
        self.assertEqual(estado, 200)
        self.assertEqual(len(json.loads(cuerpo)["casos"]), len(CASOS))
        estado, _, cuerpo = self.pedir("POST", "/api/gato/jugada", {"tablero": VACIO, "prof_max": 2})
        self.assertEqual(estado, 200)
        self.assertIn("mejor", json.loads(cuerpo))
        estado, _, cuerpo = self.pedir("POST", "/api/gato/jugada", {"tablero": VACIO, "prof_max": 99})
        self.assertEqual(estado, 400)
        self.assertIn("error", json.loads(cuerpo))
        self.assertEqual(self.pedir("GET", "/api/nada")[0], 404)

    def test_seguridad(self):
        self.assertEqual(self.pedir("GET", "/api/casos", host="evil.example.com")[0], 403)
        self.assertEqual(self.pedir("GET", "/../servidor.py")[0], 404)
        self.assertEqual(self.pedir("GET", "/%2e%2e/servidor.py")[0], 404)
        c = http.client.HTTPConnection("127.0.0.1", self.puerto)
        c.request("POST", "/api/gato/jugada", body=b"x" * 200_000, headers={"Content-Length": "200000"})
        self.assertEqual(c.getresponse().status, 413)
        c.close()
        self.assertEqual(self.servidor.server_address[0], "127.0.0.1")


@unittest.skipUnless(shutil.which("node"), "node no está instalado")
class TestJavaScript(unittest.TestCase):
    def test_sintaxis(self):
        for js in sorted(Path(ESTATICOS).glob("*.js")):
            r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{js.name}: {r.stderr}")


if __name__ == "__main__":
    unittest.main()
