import unittest
from app import Inventario, Producto, Wishlist, app, is_feature_enabled


class TestWishlist(unittest.TestCase):
    def setUp(self):
        self.wishlist = Wishlist()

    def test_agregar_item(self):
        self.wishlist.agregar_item(1)
        self.assertIn(1, self.wishlist.obtener_items())

    def test_remover_item(self):
        self.wishlist.agregar_item(1)
        self.wishlist.remover_item(1)
        self.assertNotIn(1, self.wishlist.obtener_items())

    def test_items_unicos(self):
        self.wishlist.agregar_item(2)
        self.wishlist.agregar_item(2)
        self.assertEqual(len(self.wishlist.obtener_items()), 1)

    def test_obtener_items_ordenados(self):
        self.wishlist.agregar_item(5)
        self.wishlist.agregar_item(1)
        self.wishlist.agregar_item(3)
        self.assertEqual(self.wishlist.obtener_items(), [1, 3, 5])


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
        self.assertIn("wishlist_enabled", data["feature_flags"])

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
        self.assertIn("wishlist_enabled", data["flags"])

    def test_wishlist_endpoint_toggle_protection(self):
        """Verifica que el endpoint responda 200 o 403 dependiendo del estado del flag."""
        response = self.client.get("/wishlist")
        self.assertIn(response.status_code, [200, 403])

    def test_feature_toggle_fallback(self):
        self.assertFalse(is_feature_enabled("flag_inexistente", default=False))
        self.assertTrue(is_feature_enabled("flag_inexistente", default=True))

    def test_dashboard_route(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"miweb", response.data)

    def test_crear_producto_endpoint(self):
        response = self.client.post(
            "/inventario/producto",
            json={"nombre": "Audifonos Pro", "precio": 75.0, "stock": 15},
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["producto"]["nombre"], "Audifonos Pro")


if __name__ == "__main__":
    unittest.main()
