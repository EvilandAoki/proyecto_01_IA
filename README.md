# Gato (3 en línea): algoritmos de búsqueda (Proyecto 1, IA)

**Integrantes:** Alejandro Villamil Carmona (2610338-3743), Sebastian Rey Escobar 2610344-3743 

**Curso / docente:** Inteligencia Artificial 750022C / Andrés Mauricio Valencia Restrepo 

Todo el proyecto gira alrededor del gato y cubre los cinco algoritmos pedidos:

| Modo | Problema | Algoritmos |
|---|---|---|
| **Gato en movimiento** (un agente) | Mover fichas X por el tablero hasta formar una línea, con costos distintos | DFS, BFS, costo uniforme, A\* (heurística propia) |
| **Gato contra la máquina** (adversario) | Juego normal de gato, dos jugadores por turnos | Minimax con poda alfa-beta, profundidad límite y función de evaluación |

## Requisitos y ejecución

Solo Python 3.12 o superior y la biblioteca estándar (no hay que instalar nada).

```bash
python3 main.py                  # menú principal (consola)
python3 -m gato.web              # interfaz gráfica en el navegador (ver sección 11)
python3 -m unittest              # pruebas (60, ≈ 30 s)
python3 -m gato.experimentos     # tablas de resultados del informe (Markdown)
python3 -m gato.web              # interfaz web local (http://127.0.0.1:8765/), ver sección 11
```


## Contenido del menú

| Opción | Qué hace |
|---|---|
| 1. Jugar | Partida contra la máquina. Tras cada jugada suya muestra cuántos nodos evaluó, el valor Minimax de cada casilla, y permite ver el árbol (`a`), exportarlo a `.txt` (`e`) o animarlo (`p`). |
| 2. Animación | Recorre paso a paso el árbol de una posición pequeña: cómo se baja a las hojas y cómo los valores *suben* hasta la raíz. Con o sin poda. |
| 3. Estadísticas | Enumera el árbol **completo** del gato: nodos por nivel, partidas posibles, victorias/empates. |
| 4. Comparar | Minimax vs. alfa-beta en varias posiciones, y el árbol podado con sus ramas descartadas (`✂`). |
| 5. Gato en movimiento | Elegir un caso y DFS / BFS / costo uniforme / A\*; muestra solución, costo, pasos, nodos expandidos, memoria y tiempo; compara los 4 algoritmos y las heurísticas de A\*. |
| 6. Torneo | Competencias: torneo de gato entre jugadores Minimax con distinta profundidad y evaluación, y competencia puntuada entre DFS, BFS, UCS y A\*. |

---

## 1. Juegos como árboles

El gato es un juego **de suma cero, por turnos, de información perfecta y determinista**: lo que gana
un jugador lo pierde el otro, ambos ven todo el tablero y no hay azar. Un juego así se modela con un
**árbol de juego**:

- **Nodo** = una posición del tablero.
- **Arista** = una jugada legal.
- **Raíz** = la posición actual.
- **Hojas** = posiciones terminales (alguien ganó o el tablero se llenó).
- Los niveles se **alternan** entre los dos jugadores.

```
                     raíz (mueve X)
              ┌──────────┼──────────┐
           X en 1      X en 2      X en 3 …      9 hijos
         ┌─────┼─────┐
      O en 2  O en 3 …                           8 hijos cada uno
```

Etiquetamos a la máquina como **MAX** (quiere maximizar su puntaje) y a su rival como **MIN**
(quiere minimizarlo, porque lo que es bueno para MIN es malo para MAX).

## 2. Función de utilidad

Solo las hojas tienen un valor "real". Se mide desde el punto de vista de la máquina:

| Hoja | Utilidad |
|---|---|
| Gana la máquina | `+10 − profundidad` |
| Gana el rival | `profundidad − 10` |
| Empate | `0` |

Restar la profundidad hace que la máquina **prefiera ganar rápido y perder tarde**: ganar en la
jugada 3 vale `+7`, ganar en la 5 vale `+5`. Sin ese detalle, la máquina vería igual de buenas todas
las victorias y podría "jugar con su comida" en lugar de cerrar la partida.

## 3. El algoritmo Minimax

Idea: **suponer que el rival siempre juega lo mejor posible** y propagar los valores de las hojas
hacia la raíz.

- En un nodo **MAX** (le toca a la máquina) el valor es el **máximo** de los valores de sus hijos.
- En un nodo **MIN** (le toca al rival) el valor es el **mínimo** de los valores de sus hijos.
- La jugada elegida en la raíz es la que lleva al hijo con el mejor valor.

```text
función MINIMAX(estado, turno, profundidad):
    si estado es terminal:
        devolver UTILIDAD(estado, profundidad)

    si turno es MAX:
        mejor ← −∞
        para cada jugada m legal en estado:
            mejor ← max(mejor, MINIMAX(aplicar(estado, m), MIN, profundidad + 1))
        devolver mejor
    sino:                                   # turno de MIN
        mejor ← +∞
        para cada jugada m legal en estado:
            mejor ← min(mejor, MINIMAX(aplicar(estado, m), MAX, profundidad + 1))
        devolver mejor
```

Es una **búsqueda en profundidad**: baja hasta una hoja, y al regresar cada nodo calcula su valor.
En el código es una única función recursiva, `_evaluar` en [`gato/minimax.py`](gato/minimax.py).

### Ejemplo resuelto (salida real del programa)

Posición `X O X / O X O / · · ·` con 3 casillas libres, le toca a **X** (la máquina, MAX):

```
[MAX(X)]  raíz  v=+9  X O X | O X O | · · ·
├── [HOJA]  mov=7  v=+9  X O X | O X O | X · ·  gana X
├── [MIN(O)]  mov=8  v=+7  X O X | O X O | · X ·
│   ├── [MAX(X)]  mov=7  v=+7  X O X | O X O | O X ·
│   │   └── [HOJA]  mov=9  v=+7  X O X | O X O | O X X  gana X
│   └── [MAX(X)]  mov=9  v=+7  X O X | O X O | · X O
│       └── [HOJA]  mov=7  v=+7  X O X | O X O | X X O  gana X
└── [HOJA]  mov=9  v=+9  X O X | O X O | · · X  gana X
```

Cómo se lee:

1. Jugar en **7** o en **9** gana de inmediato (profundidad 1) → utilidad `10 − 1 = +9`.
2. Jugar en **8** no gana al instante; el rival responde y X gana después (profundidad 3) →
   `10 − 3 = +7`. Los dos hijos de ese nodo valen `+7`; MIN elige el mínimo, que también es `+7`.
3. La raíz es MAX: `max(+9, +7, +9) = +9`. Hay empate entre 7 y 9; se elige la **primera** (la 7),
   así el programa es determinista.

## 4. ¿Qué tan grande es el árbol del gato?

Medido con la opción 3 del menú (recorriendo el árbol completo desde el tablero vacío):

| Profundidad | Mueve | Nodos | Hojas |
|---:|:--:|---:|---:|
| 0 | X | 1 | 0 |
| 1 | O | 9 | 0 |
| 2 | X | 72 | 0 |
| 3 | O | 504 | 0 |
| 4 | X | 3.024 | 0 |
| 5 | O | 15.120 | 1.440 |
| 6 | X | 54.720 | 5.328 |
| 7 | O | 148.176 | 47.952 |
| 8 | X | 200.448 | 72.576 |
| 9 | — | 127.872 | 127.872 |
| **Total** | | **549.946** | **255.168** |

- **255.168 partidas posibles**: 131.184 ganan las X, 77.904 ganan las O y 46.080 empatan.
- La cota ingenua `9! = 362.880` no se alcanza porque muchas partidas terminan antes de llenar el tablero.
- Hay solo **5.478 posiciones distintas**: el árbol tiene muchas repeticiones (se llega a la misma
  posición por distinto orden de jugadas). Minimax no lo aprovecha; una tabla de transposición sí podría.
- El valor Minimax de **cada una de las 9 primeras jugadas es 0**: con juego perfecto de ambos lados
  el gato **siempre termina en empate**.

Complejidad general: con factor de ramificación `b` y profundidad máxima `m`, Minimax visita
`O(b^m)` nodos. Aquí `b ≤ 9` y `m = 9`, lo que es pequeño; en ajedrez (`b ≈ 35`, `m ≈ 80`) sería
imposible sin podas y heurísticas.

## 5. Poda alfa-beta

Minimax evalúa ramas que **no pueden cambiar la decisión**. Alfa-beta lleva dos cotas:

- **α**: el mejor valor que MAX ya tiene asegurado en el camino hacia la raíz.
- **β**: el mejor valor (el más bajo) que MIN ya tiene asegurado.

Si en algún nodo ocurre **β ≤ α**, las ramas restantes de ese nodo se descartan: quien esté
arriba ya tiene una alternativa al menos igual de buena y nunca dejaría llegar a esa rama.

```text
función ALFABETA(estado, turno, α, β):
    si estado es terminal: devolver UTILIDAD(...)
    si turno es MAX:
        mejor ← −∞
        para cada jugada m:
            mejor ← max(mejor, ALFABETA(hijo, MIN, α, β))
            α ← max(α, mejor)
            si α ≥ β: romper           # poda: MIN nunca permitiría llegar aquí
        devolver mejor
    sino: (simétrico con min y β)
```

Ejemplo real (posición `X O X / · O · / · X ·`, le toca a O). Las ramas `✂` ni siquiera se evaluaron:

```
├── [MIN(X)]  mov=6  v=0  X O X | · O O | · X ·  α=0 β=0
│   ├── [MAX(O)]  mov=4  v=0  X O X | X O O | · X ·  α=0 β=+∞
│   │   ├── [MIN(X)]  mov=7  v=0 ...
│   │   └── [MIN(X)]  mov=9  v=-6 ...
│   ├── ✂ mov=7  podado  (β=0 ≤ α=0)
│   └── ✂ mov=9  podado  (β=0 ≤ α=0)
```

La raíz (MAX) ya tenía `α = 0` por una rama anterior. Aquí el primer hijo de este nodo MIN vale 0,
así que `β = 0`. MIN nunca ofrecerá más de 0, y MAX ya tiene 0 asegurado: las jugadas 7 y 9 no
pueden mejorar el resultado, por lo que se descartan.

### Resultados medidos (opción 4 del menú)

| Posición | Minimax | Alfa-beta | Ahorro | Misma jugada |
|---|---:|---:|---:|:--:|
| Tablero vacío (mueve X) | 549.946 | 20.866 | 96,2 % | sí |
| X en esquina (mueve O) | 59.705 | 2.788 | 95,3 % | sí |
| X centro, O esquina (mueve X) | 6.812 | 832 | 87,8 % | sí |
| Ejemplo A (4 libres) | 61 | 29 | 52,5 % | sí |
| Ejemplo C (5 libres) | 238 | 93 | 60,9 % | sí |
| Ejemplo B (3 libres) | 8 | 6 | 25,0 % | sí |

Desde el tablero vacío, Minimax tarda ≈ 1 s en Python y alfa-beta ≈ 0,05 s, con **exactamente** la
misma jugada y el mismo valor. La poda no es una aproximación: solo omite lo irrelevante. Su
rendimiento depende del orden en que se exploran las jugadas (aquí, orden de casilla 1 a 9, sin
heurística, por lo que el ahorro podría ser aún mayor con un mejor orden).

## 6. ¿Por qué la máquina nunca pierde?

(Con la profundidad por defecto, hasta el final de la partida; con una profundidad límite baja la
máquina sí puede perder, porque no ve toda la partida.) Porque Minimax supone un rival perfecto. Como el valor de la raíz del gato es 0, la máquina
siempre puede asegurar al menos el empate, y en cuanto el rival se equivoca, el árbol le muestra
una rama con valor positivo y la toma. Las pruebas lo verifican **exhaustivamente**: prueban todas
las jugadas posibles del humano, jugando la máquina como X y como O, y ninguna partida la derrota.

## 7. Estructura del proyecto

```
main.py                 menú principal
gato/
  tablero.py            reglas: tablero (tupla de 9), turnos, ganador, dibujo
  arbol.py              clase Nodo + dibujo del árbol en ASCII + exportación a .txt
  minimax.py            Minimax y alfa-beta (una sola función recursiva con poda opcional)
  animacion.py          reproduce la búsqueda paso a paso (usa los eventos del algoritmo)
  estadisticas.py       enumeración del árbol completo y comparación Minimax vs. alfa-beta
  juego.py              partida humano vs. máquina (con profundidad límite configurable)
  movil.py              problema "Gato en movimiento": estados, acciones, costos, meta, heurísticas
  busqueda.py           DFS, BFS, costo uniforme y A* (genéricos) + medición de tiempo y memoria
  solitario.py          interfaz de consola del Gato en movimiento
  torneo.py             torneo de gato y competencia de búsqueda (opción 6)
  web/                  interfaz gráfica: api.py, servidor.py y static/ (HTML, CSS, JS)
  experimentos.py       genera las tablas del informe
  consola.py            colores ANSI, entrada, pantalla
  web/                  interfaz web local: servidor.py, api.py y static/ (sección 11)
tests/test_minimax.py   23 pruebas de Minimax, alfa-beta y profundidad límite
tests/test_busqueda.py  13 pruebas de DFS/BFS/UCS/A* y de las heurísticas
tests/test_torneo.py    9 pruebas del torneo y de la competencia de búsqueda
tests/test_web.py       15 pruebas de la API, el servidor (seguridad incluida) y la sintaxis del JS
arboles/                árboles exportados desde el juego (se crea al exportar)
```

Detalles de implementación que conviene saber:

- **X siempre empieza**; el turno se deduce contando fichas. Si juegas con O, la máquina abre.
- La animación no duplica la lógica: el algoritmo acepta un `callback` que recibe los eventos
  (`entrar`, `hoja`, `subir`, `poda`) y la animación solo los reproduce sobre el árbol ya construido.
- Cuando la máquina abre en un tablero vacío, el árbol tiene 549.946 nodos: se evalúa completo,
  pero solo se **guardan** los primeros 3 niveles (`prof_arbol`), por eso en ese caso no se puede
  exportar el árbol completo. Con 8 o menos casillas libres (≈ 60 mil nodos o menos) el árbol se guarda entero.
- Los árboles exportados con `e` quedan en `arboles/arbol_<timestamp>.txt`.

## 8. Gato en movimiento (DFS, BFS, costo uniforme y A\*)

Tablero N×N con **k fichas X móviles** y algunas **O fijas** (obstáculos). Cada jugada mueve una X
a una casilla vecina libre (8 direcciones). **Meta:** que las k fichas X formen una línea (fila,
columna o diagonal). No es un laberinto: la meta es un patrón de varias fichas, no una casilla.

| Elemento | Definición |
|---|---|
| Estado | `frozenset` con las casillas ocupadas por X (las O y N son fijas por caso) |
| Acciones | `(origen, destino)`: una X a una casilla vecina sin X ni O |
| Costo | paso recto = 2, paso en diagonal = 3 |
| Meta | las X ocupan exactamente una línea de k casillas sin O |

Los casos de prueba están en `gato/movil.py` (`CASOS`). El caso 2 está elegido para que **BFS (menos
pasos) y UCS (menor costo) den soluciones distintas**.

**Frontera de cada algoritmo** (`gato/busqueda.py`): DFS pila, BFS cola, UCS y A\* cola de
prioridad (`heapq`). Todos descartan estados repetidos con un conjunto de explorados.

**Heurística propia de A\*** (`ProblemaMovil.heuristica`): para cada línea posible se asignan las
fichas a sus casillas del modo más barato (distancia con costos 2 y 3, ignorando que las fichas
se estorben) y se toma la mejor línea. Es admisible y consistente; la prueba está en
`DOCUMENTACION.md` y las pruebas la verifican en **todos** los estados de los casos pequeños. También
hay una heurística más simple (`heuristica_simple`) para compararlas.

## 9. Profundidad límite y función de evaluación (Minimax)

Al jugar se puede fijar una **profundidad límite** (1-9). Al llegar a ella el nodo no se expande
(se marca `CORTE` en el árbol) y se valora con `minimax.evaluacion()`:

- línea abierta con solo fichas de la IA: +1 (una ficha) o +10 (dos); del rival: −1 o −10;
- +1 si la IA tiene el centro; el total se divide entre 100.

Así la evaluación siempre queda en (−1, 1) y nunca supera una victoria o derrota real
(que valen al menos 1 en valor absoluto). La poda alfa-beta funciona igual con el límite y da la
misma jugada que Minimax en cada profundidad (hay pruebas para esto). `python3 -m gato.experimentos`
muestra los nodos con y sin poda para varias profundidades.

## 10. Competencias entre algoritmos (opción 6)

El torneo enfrenta 7 jugadores de máquina todos contra todos: un aleatorio (referencia),
alfa-beta con profundidad 1, 2, 3 y completa (9), y dos con una evaluación alternativa "posicional"
(centro +3, esquinas +1) a profundidad 2 y 3. Minimax y alfa-beta **no** compiten entre sí: dan la misma
jugada, solo empatarían; por eso todos usan alfa-beta y lo que compite es la profundidad y la evaluación.

Para que no se repita la misma partida (los jugadores son deterministas) cada pareja juega 10
**aperturas aleatorias de 2 jugadas**, y cada apertura se juega **dos veces, con cada jugador como X**.
Victoria = 1 punto, empate = 0,5. Los resultados salen de `python3 -m gato.experimentos` con semilla 1
(reproducibles):

| # | Jugador | Ganadas | Empatadas | Perdidas | % de puntos |
|---:|---|---:|---:|---:|---:|
| 1 | Prof 9 (completo) | 48 | 52 | 20 | 61,7 % |
| 2 | Prof 3 posicional | 53 | 40 | 27 | 60,8 % |
| 3 | Prof 3 | 53 | 39 | 28 | 60,4 % |
| 4 | Prof 2 | 45 | 46 | 29 | 56,7 % |
| 5 | Prof 1 | 41 | 49 | 30 | 54,6 % |
| 6 | Prof 2 posicional | 32 | 55 | 33 | 49,6 % |
| 7 | Aleatorio | 2 | 11 | 107 | 6,2 % |

**Cómo leerlo (con honestidad):**
- El **aleatorio queda último con claridad** (6 %): lo único que se afirma con seguridad.
- La profundidad completa queda primera, pero **por poco** frente a profundidad 3 (61,7 % contra 60,4 %). Con 120 partidas por jugador
  esa diferencia está dentro del ruido; más aperturas o más semillas la afinarían. Lo que sí se ve es una tendencia: más profundidad, más puntos.
- **El jugador perfecto pierde partidas (20).** No es un error: las 2 primeras jugadas son aleatorias y no las juega nadie, así que a veces
  dejan a su color en una posición ya perdida. Como cada apertura se juega con ambos colores, el efecto es parejo.
- A profundidad 2 la evaluación **por líneas** (56,7 %) supera a la **posicional** (49,6 %); a profundidad 3 son casi iguales
  (60,4 % contra 60,8 %). La evaluación importa más cuanto menos se ve del árbol.

### Competencia de búsqueda
Aquí "ganar" depende de qué se mida, así que se puntúa cada criterio por caso (el mejor recibe 4 puntos, el peor 0;
los empates comparten puntos) y se suman con pesos: **costo de la solución ×3**, nodos expandidos ×1, memoria ×1, tiempo ×1.
Se pesa más el costo porque una solución rápida pero 20 veces más cara no es mejor. Competidores: DFS, BFS, UCS, A\* con h1 y A\* con h2.

| Competidor | costo (×3) | expandidos | memoria | tiempo | Total (máx. 96) |
|---|---:|---:|---:|---:|---:|
| A\* (h1) | 16 | 15 | 15 | 0 | **78** |
| BFS | 13 | 9 | 9 | 13 | 70 |
| A\* (h2) | 16 | 5 | 7 | 9 | 69 |
| UCS | 16 | 0 | 0 | 4 | 52 |
| DFS | 0 | 12 | 9 | 14 | 35 |

Campeón con estos pesos: **A\* (h1)**. Pero **no es el mejor en todo** y el resultado depende de los pesos:
UCS, A\* (h1) y A\* (h2) empatan en costo (todos óptimos); A\* (h1) gana en nodos y memoria; **DFS gana en tiempo**
(y es último en costo); y A\* (h1) saca **0 puntos en tiempo** (su heurística es cara de calcular). Si el tiempo pesara mucho,
BFS o A\* (h2) pasarían adelante. Es una buena demostración de que la elección del algoritmo es un compromiso.

**Código:** `gato/torneo.py` (`torneo_gato`, `competencia_busqueda`, `menu_torneo`). `minimax()` y `alfabeta()` aceptan el
parámetro `evaluador` (por defecto `evaluacion`) para poder enfrentar evaluaciones distintas. Pruebas: `tests/test_torneo.py`.

---

## 11. Interfaz web (`gato/web/`)

Interfaz gráfica local para ver los mismos algoritmos en el navegador. Solo usa la biblioteca estándar de Python
(`http.server`) y archivos estáticos HTML/CSS/JS, sin internet ni dependencias.

```bash
python3 -m gato.web                      # abre http://127.0.0.1:8765/
python3 -m gato.web --puerto 9000 --no-abrir
```

| Archivo | Responsabilidad |
|---|---|
| `gato/web/__main__.py` | Arranque: levanta el servidor, abre el navegador, se cierra con Ctrl+C. |
| `gato/web/servidor.py` | Servidor HTTP. Escucha **solo en 127.0.0.1**, rechaza un `Host` no local, limita los POST a 100 KB, evita salir de `static/` (`../`). Tabla `RUTAS` -> función de `api.py`. |
| `gato/web/api.py` | Capa de datos: funciones puras `entrada -> dict` listas para JSON, con validación (`ValueError` en español). No sabe nada de HTTP, por eso se prueba sin servidor. Guarda en caché los cálculos pesados. |
| `gato/web/static/` | `index.html`, `estilos.css` (tema claro/oscuro), `app.js` (utilidades DOM, cliente de la API, pestañas), `tablero.js` (dibujo del tablero). |

**API JSON**

| Ruta | Qué devuelve |
|---|---|
| `GET /api/casos` | Casos del Gato en movimiento, posiciones de ejemplo, algoritmos y líneas ganadoras. |
| `POST /api/gato/jugada` | `{tablero, prof_max, evaluador}` -> mejor casilla, valor de cada casilla, nodos con y sin poda, ahorro, tiempo. |
| `POST /api/gato/arbol` | `{tablero, poda, prof_max, evaluador}` -> árbol plano de nodos + lista de **eventos** (entrar, hoja, corte, subir, poda) con la frase de cada paso. Máximo 1.500 nodos. |
| `POST /api/busqueda` | `{caso, algoritmo}` -> camino, métricas y traza de expansiones (se muestrea a 6.000 eventos). |
| `GET /api/comparacion` | Métricas de los 5 competidores de búsqueda en todos los casos. |
| `GET /api/poda` | Nodos con y sin poda por profundidad límite. |
| `GET /api/torneo?partidas=N` | Ranking y matriz del torneo (semilla fija: reproducible). |

**Cambios en el núcleo que lo hacen posible** (sin alterar el comportamiento de la consola):
- `animacion.explicar_evento` (antes `_explicar`) es pública: la frase de cada paso es la misma en consola y web.
- `arbol.numerar(raiz)` asigna un entero a cada nodo (preorden) y `arbol.nodo_a_dict(raiz, ids, limite)` aplana el árbol a
  una lista de dicts con `padre`; los infinitos se envían como `"+inf"`/`"-inf"` (JSON no admite `Infinity`).
- `busqueda.dfs/bfs/ucs/astar` aceptan `traza=None`: una función `traza(nodo, tamaño_frontera, tamaño_explorados)` que se
  llama tras expandir cada nodo, para animar la búsqueda. Con `traza=None` no cambia nada.

**Estado:** el servidor, la API y `app.js`/`tablero.js` están hechos y la API responde. `index.html` ya referencia
`graficos.js`, `arbol.js`, `busqueda.js` y `paginas.js` (dibujo de gráficas, del árbol, de la búsqueda y las páginas de cada
pestaña), que **todavía no existen**; hasta crearlos la página no muestra contenido. La API aún no tiene pruebas automáticas.

## 11. Interfaz gráfica web (`python3 -m gato.web`)

Además de la consola hay una **interfaz gráfica en el navegador**. Python arranca un servidor local
(solo en `127.0.0.1`, sin internet y sin instalar nada) y se abre la página sola:

```bash
python3 -m gato.web              # abre http://127.0.0.1:8765/ ; Ctrl+C para cerrar
python3 main.py --web            # equivalente
python3 -m gato.web --puerto 9000 --no-abrir
```

| Pestaña | Qué muestra |
|---|---|
| **Inicio** | Los dos modos, los 5 algoritmos y un glosario (MAX/MIN, α/β, g/h/f). |
| **Jugar** | Gato clicable contra la máquina. Cada casilla se colorea con su valor Minimax (verde conviene, rojo no), tarjetas de nodos **con y sin poda**, tiempo y una explicación de por qué eligió esa casilla. Profundidad límite y evaluación configurables. |
| **Árbol de Minimax** | El árbol **crece paso a paso**: nodos MAX ▲ / MIN ▼, hojas, cortes por profundidad, ramas podadas tachadas (✂), valores que suben, α/β del nodo actual y la variante principal. Controles de reproducir, pausa, paso a paso, velocidad, zoom y barra de posición (teclas: espacio, ← →). Modo **comparar con y sin poda** lado a lado. |
| **Gato en movimiento** | DFS, BFS, UCS y A\*: el estado que se expande en cada paso, contadores en vivo (expandidos, frontera, explorados), gráfica de la frontera, mapa de calor de casillas, y luego la **solución con las fichas deslizándose**. El tablero se ve como un gato (rejilla #, X con trazo, obstáculos O en anillo, línea ganadora al llegar a la meta), cada movimiento muestra su **costo** (flecha continua +2, discontinua +3) y se pueden resaltar las **líneas meta posibles**. Tabla con los resultados de la sesión (BFS 14 contra UCS 10 en el caso 2). |
| **Comparación** | Barras por caso y algoritmo (nodos, tiempo, memoria, costo, pasos; escala log), competencia con **pesos ajustables**, ahorro de la poda por profundidad y torneo de gato (ranking y matriz). Cada gráfica se descarga como PNG o SVG y su tabla se copia en Markdown, para el informe y las diapositivas. |

La lógica sigue siendo la de Python (`minimax.py`, `busqueda.py`...): el navegador solo dibuja lo que el
servidor le entrega como JSON. Tema claro y oscuro automático (y botón), responsive, respeta
`prefers-reduced-motion`. Código: `gato/web/` (`api.py`, `servidor.py`, `static/*.js|css|html`).
