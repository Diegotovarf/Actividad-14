"""
Pruebas de funcionamiento: se compara Karatsuba contra la multiplicación
escolar y contra la multiplicación nativa de Python (sin el algoritmo).

Ejecutar:  python -m unittest -v
"""

import random
import unittest

from karatsuba import Estadisticas, karatsuba, multiplicacion_escolar


def numero_aleatorio(digitos: int, rng: random.Random) -> int:
    """Entero aleatorio con exactamente ``digitos`` dígitos."""
    return rng.randint(10 ** (digitos - 1), 10 ** digitos - 1)


class TestKaratsuba(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(14)

    def test_casos_pequenos(self):
        for x in range(0, 120):
            for y in range(0, 120, 7):
                self.assertEqual(karatsuba(x, y), x * y)

    def test_signos(self):
        self.assertEqual(karatsuba(-1234, 5678), -1234 * 5678)
        self.assertEqual(karatsuba(1234, -5678), 1234 * -5678)
        self.assertEqual(karatsuba(-1234, -5678), 1234 * 5678)
        self.assertEqual(multiplicacion_escolar(-99, 99), -9801)

    def test_cero_y_uno(self):
        n = numero_aleatorio(100, self.rng)
        self.assertEqual(karatsuba(n, 0), 0)
        self.assertEqual(karatsuba(0, n), 0)
        self.assertEqual(karatsuba(n, 1), n)

    def test_longitudes_distintas(self):
        x = numero_aleatorio(100, self.rng)
        y = numero_aleatorio(7, self.rng)
        self.assertEqual(karatsuba(x, y), x * y)
        self.assertEqual(karatsuba(y, x), x * y)

    def test_20_50_100_digitos(self):
        for digitos in (20, 50, 100):
            for _ in range(25):
                x = numero_aleatorio(digitos, self.rng)
                y = numero_aleatorio(digitos, self.rng)
                with self.subTest(digitos=digitos):
                    esperado = x * y                      # sin el algoritmo
                    self.assertEqual(karatsuba(x, y), esperado)
                    self.assertEqual(multiplicacion_escolar(x, y), esperado)

    def test_variantes_umbral(self):
        for digitos in (20, 50, 100):
            x = numero_aleatorio(digitos, self.rng)
            y = numero_aleatorio(digitos, self.rng)
            for umbral in (1, 4, 8, 16, 32, 200):
                with self.subTest(digitos=digitos, umbral=umbral):
                    self.assertEqual(karatsuba(x, y, umbral=umbral), x * y)

    def test_numeros_enormes(self):
        x = numero_aleatorio(1000, self.rng)
        y = numero_aleatorio(1000, self.rng)
        self.assertEqual(karatsuba(x, y), x * y)

    def test_karatsuba_hace_menos_multiplicaciones(self):
        for digitos in (20, 50, 100):
            x = numero_aleatorio(digitos, self.rng)
            y = numero_aleatorio(digitos, self.rng)
            s_k, s_e = Estadisticas(), Estadisticas()
            karatsuba(x, y, s_k)
            multiplicacion_escolar(x, y, s_e)
            with self.subTest(digitos=digitos):
                self.assertEqual(s_e.multiplicaciones, digitos * digitos)
                self.assertLess(s_k.multiplicaciones, s_e.multiplicaciones)


if __name__ == "__main__":
    unittest.main(verbosity=2)
