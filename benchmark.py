"""
Medición de T(N) y S(N) para Karatsuba vs. multiplicación escolar.

Para cada tamaño N (20, 50, 100 dígitos y tamaños extra para ver la
tendencia) se mide:

* T(N): tiempo real (mediana de varias repeticiones) y número de
        multiplicaciones de un dígito.
* S(N): memoria pico (tracemalloc) y profundidad máxima de la recursión.

Además se comparan variantes de Karatsuba con distintos umbrales para el
caso base (1 = Karatsuba puro; k > 1 = híbrido con el método escolar).

Ejecutar:  python benchmark.py
Genera:    resultados/resultados.{csv,md}, resultados/variantes.{csv,md}
           y gráficas PNG.
"""

import csv
import math
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

from karatsuba import Estadisticas, karatsuba, multiplicacion_escolar

TAMANOS = [20, 50, 100, 200, 500, 1000]
UMBRALES = [1, 4, 8, 16, 32]   # variantes híbridas de Karatsuba (1 = puro)
REPETICIONES = 7
CARPETA = Path(__file__).parent / "resultados"


def numero_aleatorio(digitos: int, rng: random.Random) -> int:
    return rng.randint(10 ** (digitos - 1), 10 ** digitos - 1)


def medir(funcion, x: int, y: int, **opciones) -> dict:
    """Ejecuta ``funcion(x, y, stats)`` y regresa tiempo, memoria y contadores."""
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        funcion(x, y, Estadisticas(), **opciones)
        tiempos.append(time.perf_counter() - inicio)

    stats = Estadisticas()
    tracemalloc.start()
    resultado = funcion(x, y, stats, **opciones)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "resultado": resultado,
        "tiempo_ms": statistics.median(tiempos) * 1000,
        "memoria_kb": pico / 1024,
        "multiplicaciones": stats.multiplicaciones,
        "llamadas": stats.llamadas,
        "profundidad": stats.profundidad_max,
    }


def medir_nativa(x: int, y: int) -> float:
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        _ = x * y
        tiempos.append(time.perf_counter() - inicio)
    return statistics.median(tiempos) * 1000


def comparar_algoritmos(rng):
    """Karatsuba puro vs. multiplicación escolar vs. multiplicación nativa."""
    filas = []
    for n in TAMANOS:
        x, y = numero_aleatorio(n, rng), numero_aleatorio(n, rng)
        k = medir(karatsuba, x, y)
        e = medir(multiplicacion_escolar, x, y)
        filas.append({
            "N": n,
            "mult_karatsuba": k["multiplicaciones"],
            "mult_escolar": e["multiplicaciones"],
            "n^1.585": round(n ** math.log2(3)),
            "ahorro_%": round(100 * (1 - k["multiplicaciones"] / e["multiplicaciones"]), 1),
            "t_karatsuba_ms": round(k["tiempo_ms"], 3),
            "t_escolar_ms": round(e["tiempo_ms"], 3),
            "t_nativa_ms": round(medir_nativa(x, y), 4),
            "mem_karatsuba_kb": round(k["memoria_kb"], 2),
            "mem_escolar_kb": round(e["memoria_kb"], 2),
            "llamadas_recursivas": k["llamadas"],
            "profundidad_max": k["profundidad"],
            "correcto": k["resultado"] == e["resultado"] == x * y,
        })
    return filas


def comparar_variantes(rng):
    """T(N) y S(N) de Karatsuba con distintos umbrales de caso base."""
    filas = []
    for n in (20, 50, 100, 1000):
        x, y = numero_aleatorio(n, rng), numero_aleatorio(n, rng)
        for umbral in UMBRALES:
            r = medir(karatsuba, x, y, umbral=umbral)
            filas.append({
                "N": n,
                "umbral": umbral,
                "multiplicaciones": r["multiplicaciones"],
                "tiempo_ms": round(r["tiempo_ms"], 3),
                "memoria_kb": round(r["memoria_kb"], 2),
                "llamadas_recursivas": r["llamadas"],
                "profundidad_max": r["profundidad"],
                "correcto": r["resultado"] == x * y,
            })
    return filas


def imprimir_tabla(filas):
    encabezados = list(filas[0].keys())
    anchos = [max(len(h), *(len(str(f[h])) for f in filas)) for h in encabezados]
    print(" | ".join(h.ljust(a) for h, a in zip(encabezados, anchos)))
    print("-+-".join("-" * a for a in anchos))
    for f in filas:
        print(" | ".join(str(f[h]).ljust(a) for h, a in zip(encabezados, anchos)))


def guardar(filas, nombre):
    encabezados = list(filas[0].keys())
    with open(CARPETA / f"{nombre}.csv", "w", newline="", encoding="utf-8") as fh:
        escritor = csv.DictWriter(fh, fieldnames=encabezados)
        escritor.writeheader()
        escritor.writerows(filas)
    with open(CARPETA / f"{nombre}.md", "w", encoding="utf-8") as fh:
        fh.write("| " + " | ".join(encabezados) + " |\n")
        fh.write("|" + "---|" * len(encabezados) + "\n")
        for f in filas:
            fh.write("| " + " | ".join(str(f[h]) for h in encabezados) + " |\n")


def graficar(filas):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no está instalado; se omiten las gráficas.")
        return

    ns = [f["N"] for f in filas]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ns, [f["mult_escolar"] for f in filas], "o-", label="Escolar  (n²)")
    ax.plot(ns, [f["mult_karatsuba"] for f in filas], "s-", label="Karatsuba")
    ax.plot(ns, [f["n^1.585"] for f in filas], "--", color="gray", label="n^1.585 (teórico)")
    ax.set(xscale="log", yscale="log", xlabel="N (dígitos)",
           ylabel="Multiplicaciones de 1 dígito", title="T(N): multiplicaciones")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CARPETA / "T_multiplicaciones.png", dpi=120)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ns, [f["t_escolar_ms"] for f in filas], "o-", label="Escolar")
    ax.plot(ns, [f["t_karatsuba_ms"] for f in filas], "s-", label="Karatsuba")
    ax.plot(ns, [f["t_nativa_ms"] for f in filas], "^-", label="Python nativo (x*y)")
    ax.set(xscale="log", yscale="log", xlabel="N (dígitos)",
           ylabel="Tiempo (ms)", title="T(N): tiempo de ejecución")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CARPETA / "T_tiempo.png", dpi=120)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ns, [f["mem_escolar_kb"] for f in filas], "o-", label="Escolar")
    ax.plot(ns, [f["mem_karatsuba_kb"] for f in filas], "s-", label="Karatsuba")
    ax.set(xlabel="N (dígitos)", ylabel="Memoria pico (KB)", title="S(N): memoria")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CARPETA / "S_memoria.png", dpi=120)
    plt.close("all")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rng = random.Random(2026)
    CARPETA.mkdir(exist_ok=True)

    filas = comparar_algoritmos(rng)
    print("== Karatsuba (puro) vs. multiplicación escolar ==")
    imprimir_tabla(filas)
    guardar(filas, "resultados")

    variantes = comparar_variantes(rng)
    print("\n== Variantes de Karatsuba (umbral del caso base) ==")
    imprimir_tabla(variantes)
    guardar(variantes, "variantes")

    graficar(filas)
    print(f"\nResultados guardados en {CARPETA}")


if __name__ == "__main__":
    main()
