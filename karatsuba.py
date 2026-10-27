"""
Algoritmo de Karatsuba (Divide y Vencerás) para multiplicar enteros gigantes.

Se incluyen dos algoritmos que operan en base 10 y cuentan cuántas
multiplicaciones de un solo dígito realizan:

* ``karatsuba``           -> versión recursiva, 3 subproblemas de tamaño n/2.
* ``multiplicacion_escolar`` -> método tradicional "de primaria", O(n^2).

La multiplicación nativa de Python (``x * y``) se usa solo como referencia
para comprobar que los resultados son correctos.
"""

from dataclasses import dataclass


@dataclass
class Estadisticas:
    """Contadores que se llenan durante la ejecución de un algoritmo."""

    multiplicaciones: int = 0     # multiplicaciones de 1 dígito x 1 dígito
    llamadas: int = 0             # llamadas recursivas totales
    profundidad: int = 0          # profundidad actual de la recursión
    profundidad_max: int = 0      # profundidad máxima alcanzada (pila)


def num_digitos(x: int) -> int:
    """Cantidad de dígitos decimales de un entero no negativo."""
    return len(str(x))


def karatsuba(x: int, y: int, stats: Estadisticas | None = None, umbral: int = 1) -> int:
    """
    Multiplica ``x`` por ``y`` con el algoritmo recursivo de Karatsuba.

    ``umbral`` (variante híbrida): cuando ambos números tienen ``umbral``
    dígitos o menos se usa el método escolar en vez de seguir dividiendo.
    Con ``umbral=1`` se obtiene el Karatsuba "puro".

    Recurrencia:  T(n) = 3 T(n/2) + O(n)  =>  T(n) = O(n^log2(3)) ≈ O(n^1.585)
    Espacio:      S(n) = S(n/2) + O(n)    =>  S(n) = O(n)
    """
    if stats is None:
        stats = Estadisticas()

    # Manejo del signo: se trabaja con valores absolutos.
    signo = -1 if (x < 0) ^ (y < 0) else 1
    return signo * _karatsuba(abs(x), abs(y), stats, max(1, umbral))


def _karatsuba(x: int, y: int, stats: Estadisticas, umbral: int) -> int:
    stats.llamadas += 1
    stats.profundidad += 1
    stats.profundidad_max = max(stats.profundidad_max, stats.profundidad)

    n = max(num_digitos(x), num_digitos(y))

    # Variante híbrida: números pequeños se resuelven con el método escolar.
    if umbral > 1 and n <= umbral:
        resultado = _escolar(x, y, stats)
        stats.profundidad -= 1
        return resultado

    # Caso base: ambos números tienen un solo dígito.
    if x < 10 or y < 10:
        if x < 10 and y < 10:
            stats.multiplicaciones += 1
            resultado = x * y
        else:
            # Un número de 1 dígito por uno de varios: n multiplicaciones
            # de un dígito (se resuelve con el método escolar).
            resultado = _escolar(x, y, stats)
        stats.profundidad -= 1
        return resultado

    # ---------------- 1. DIVISIÓN ----------------
    # Se parte cada número en una mitad alta y una mitad baja:
    #   x = a * 10^m + b        y = c * 10^m + d
    m = n // 2
    potencia = 10 ** m            # desplazamiento en base 10 (no es una
    a, b = divmod(x, potencia)    # multiplicación de dígitos)
    c, d = divmod(y, potencia)

    # ---------------- 2. CONQUISTA ----------------
    # Solo 3 multiplicaciones recursivas en lugar de 4:
    z2 = _karatsuba(a, c, stats, umbral)              # a*c
    z0 = _karatsuba(b, d, stats, umbral)              # b*d
    z1 = _karatsuba(a + b, c + d, stats, umbral)      # (a+b)(c+d)

    # ---------------- 3. COMBINACIÓN ----------------
    # (a+b)(c+d) - ac - bd = ad + bc
    medio = z1 - z2 - z0
    resultado = z2 * 10 ** (2 * m) + medio * potencia + z0

    stats.profundidad -= 1
    return resultado


def multiplicacion_escolar(x: int, y: int, stats: Estadisticas | None = None) -> int:
    """
    Multiplicación tradicional dígito por dígito (sin Karatsuba).

    Cada dígito de ``y`` se multiplica por cada dígito de ``x``:
    T(n) = O(n^2),  S(n) = O(n).
    """
    if stats is None:
        stats = Estadisticas()
    signo = -1 if (x < 0) ^ (y < 0) else 1
    return signo * _escolar(abs(x), abs(y), stats)


def _escolar(x: int, y: int, stats: Estadisticas) -> int:
    dx = [int(c) for c in reversed(str(x))]   # dígitos, el menos significativo primero
    dy = [int(c) for c in reversed(str(y))]
    acumulado = [0] * (len(dx) + len(dy))

    for i, dig_y in enumerate(dy):
        acarreo = 0
        for j, dig_x in enumerate(dx):
            stats.multiplicaciones += 1
            total = acumulado[i + j] + dig_x * dig_y + acarreo
            acumulado[i + j] = total % 10
            acarreo = total // 10
        acumulado[i + len(dx)] += acarreo

    texto = "".join(str(d) for d in reversed(acumulado)).lstrip("0")
    return int(texto) if texto else 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    a = 3141592653589793238462643383279502884197
    b = 2718281828459045235360287471352662497757
    s_k, s_e = Estadisticas(), Estadisticas()
    r_k = karatsuba(a, b, s_k)
    r_e = multiplicacion_escolar(a, b, s_e)
    print(f"x = {a}")
    print(f"y = {b}")
    print(f"Karatsuba  = {r_k}  ({s_k.multiplicaciones} mult. de 1 dígito)")
    print(f"Escolar    = {r_e}  ({s_e.multiplicaciones} mult. de 1 dígito)")
    print(f"Python x*y = {a * b}")
    print("¿Coinciden?", r_k == r_e == a * b)
