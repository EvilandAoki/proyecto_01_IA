"""Arranca la interfaz web: python3 -m gato.web [--puerto N] [--no-abrir]"""

import argparse
import threading
import webbrowser

from .servidor import crear_servidor


def iniciar(puerto=8765, abrir=True):
    """Levanta el servidor y (opcional) abre el navegador. Termina con Ctrl+C."""
    servidor = crear_servidor(puerto)
    url = f"http://127.0.0.1:{servidor.server_address[1]}/"
    print(f"Interfaz del gato en {url}   (Ctrl+C para cerrar)")
    if abrir:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor cerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Interfaz web del proyecto del gato")
    ap.add_argument("--puerto", type=int, default=8765, help="puerto local (por defecto 8765)")
    ap.add_argument("--no-abrir", action="store_true", help="no abrir el navegador automáticamente")
    a = ap.parse_args()
    iniciar(a.puerto, not a.no_abrir)
