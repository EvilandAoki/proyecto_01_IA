"""Servidor HTTP local de la interfaz web (solo biblioteca estándar).

Sirve los archivos de static/ y expone la API JSON de api.py. Escucha ÚNICAMENTE en 127.0.0.1 y
rechaza peticiones cuyo encabezado Host no sea local (protege contra páginas externas que intenten
usar el servidor desde el navegador del usuario).
"""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import api

ESTATICOS = Path(__file__).resolve().parent / "static"
MAX_CUERPO = 100_000        # bytes aceptados en un POST
HOSTS_LOCALES = {"localhost", "127.0.0.1", "[::1]"}

# Rutas de la API: (método, ruta) -> función(entrada: dict) -> dict
RUTAS = {
    ("GET", "/api/casos"): lambda q: api.casos(),
    ("GET", "/api/comparacion"): lambda q: api.comparacion(),
    ("GET", "/api/poda"): lambda q: api.poda(),
    ("GET", "/api/torneo"): lambda q: api.torneo(int(q["partidas"]) if "partidas" in q else 10),
    ("POST", "/api/gato/jugada"): lambda q: api.jugada(q.get("tablero"), q.get("prof_max"), q.get("evaluador")),
    ("POST", "/api/gato/arbol"): lambda q: api.arbol(q.get("tablero"), q.get("poda", True),
                                                       q.get("prof_max"), q.get("evaluador")),
    ("POST", "/api/busqueda"): lambda q: api.busqueda(q.get("caso"), q.get("algoritmo")),
}


class Manejador(BaseHTTPRequestHandler):
    server_version = "GatoWeb/1.0"

    def log_message(self, formato, *args):
        pass    # sin ruido en la consola

    # ---- respuestas
    def _enviar(self, codigo, cuerpo, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, codigo, datos):
        # allow_nan=False: si algún infinito se cuela sin convertir, falla aquí y no en el navegador.
        self._enviar(codigo, json.dumps(datos, allow_nan=False).encode(), "application/json; charset=utf-8")

    def _host_valido(self):
        host = self.headers.get("Host") or ""
        nombre = host if host.endswith("]") else host.rsplit(":", 1)[0]     # quita el puerto
        return nombre in HOSTS_LOCALES

    # ---- GET: archivos estáticos y API
    def do_GET(self):
        if not self._host_valido():
            return self._json(403, {"error": "Host no permitido."})
        url = urlparse(self.path)
        if url.path.startswith("/api/"):
            return self._api("GET", url.path, {k: v[0] for k, v in parse_qs(url.query).items()})
        nombre = "index.html" if url.path in ("", "/") else url.path.lstrip("/")
        archivo = (ESTATICOS / nombre).resolve()
        if ESTATICOS not in archivo.parents or not archivo.is_file():     # evita ../ y rutas ajenas
            return self._json(404, {"error": "No encontrado."})
        tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo in ("application/javascript", "image/svg+xml"):
            tipo += "; charset=utf-8"
        self._enviar(200, archivo.read_bytes(), tipo)

    # ---- POST: solo API
    def do_POST(self):
        if not self._host_valido():
            return self._json(403, {"error": "Host no permitido."})
        url = urlparse(self.path)
        try:
            largo = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._json(400, {"error": "Content-Length inválido."})
        if largo > MAX_CUERPO:
            return self._json(413, {"error": "Petición demasiado grande."})
        try:
            entrada = json.loads(self.rfile.read(largo) or b"{}")
            if not isinstance(entrada, dict):
                raise ValueError
        except ValueError:
            return self._json(400, {"error": "El cuerpo debe ser un objeto JSON."})
        self._api("POST", url.path, entrada)

    def _api(self, metodo, ruta, entrada):
        funcion = RUTAS.get((metodo, ruta))
        if funcion is None:
            return self._json(404, {"error": "Ruta de API desconocida."})
        try:
            self._json(200, funcion(entrada))
        except (ValueError, KeyError, TypeError) as e:
            self._json(400, {"error": str(e) or "Entrada no válida."})


def crear_servidor(puerto=8765):
    """Crea el servidor en 127.0.0.1. Si el puerto está ocupado usa uno libre."""
    try:
        return ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    except OSError:
        return ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
