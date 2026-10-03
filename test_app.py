import unittest
from app import Calculator, Inventario, Producto, app, is_feature_enabled


class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_sumar(self):
        self.assertEqual(self.calc.sumar(5, 3), 8)

    def test_restar(self):
        self.assertEqual(self.calc.restar(10, 4), 6)

    def test_multiplicar(self):
        self.assertEqual(self.calc.multiplicar(4, 5), 20)

    def test_dividir(self):
        self.assertEqual(self.calc.dividir(20, 4), 5)

    def test_division_por_cero(self):
        with self.assertRaises(ValueError):
            self.calc.dividir(10, 0)


class TestInventario(unittest.TestCase):
    def setUp(self):
        self.inventario = Inventario()
        self.p1 = Producto(1, "Laptop Pro", 1000.0, 5)
        self.p2 = Producto(2, "Mouse Gamer", 50.0, 20)
        self.inventario.agregar_producto(self.p1)
        self.inventario.agregar_producto(self.p2)

    def test_creacion_producto(self):
        self.assertEqual(self.p1.nombre, "Laptop Pro")
        self.assertEqual(self.p1.precio, 1000.0)
        self.assertEqual(self.p1.stock, 5)

    def test_precio_negativo_error(self):
        with self.assertRaises(ValueError):
            Producto(3, "Teclado", -10.0, 5)

    def test_stock_negativo_error(self):
        with self.assertRaises(ValueError):
            Producto(4, "Monitor", 200.0, -1)

    def test_aplicar_descuento(self):
        precio_final = self.p1.aplicar_descuento(20)
        self.assertEqual(precio_final, 800.0)
        self.assertEqual(self.p1.precio, 800.0)

    def test_aplicar_descuento_invalido(self):
        with self.assertRaises(ValueError):
            self.p1.aplicar_descuento(150)

    def test_realizar_venta(self):
        total = self.inventario.realizar_venta(2, 2)
        self.assertEqual(total, 116.0)
        self.assertEqual(self.p2.stock, 18)

    def test_venta_stock_insuficiente(self):
        with self.assertRaises(ValueError):
            self.inventario.realizar_venta(1, 10)

    def test_total_inventario(self):
        self.assertEqual(self.inventario.total_inventario(), 6000.0)


class TestWebEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "miweb")

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("despliegue", data)
        self.assertIn("endpoints", data)

    def test_inventario_endpoint(self):
        response = self.client.get("/inventario")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("productos", data)
        self.assertIn("total_valor_inventario", data)

    def test_toggle_endpoint(self):
        response = self.client.get("/toggle")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("flags", data)
        self.assertIn("calculadora_resta", data["flags"])

    def test_calculadora_restar_toggle_protection(self):
        """Verifica que el endpoint responda según el estado del flag."""
        response = self.client.get("/calculadora/restar?a=10&b=4")
        self.assertIn(response.status_code, [200, 403])

    def test_feature_toggle_fallback(self):
        self.assertFalse(is_feature_enabled("flag_inexistente", default=False))
        self.assertTrue(is_feature_enabled("flag_inexistente", default=True))


if __name__ == "__main__":
    unittest.main()
