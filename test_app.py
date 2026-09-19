import unittest

from app import Inventario, Producto


class TestInventario(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de cada prueba."""
        self.inventario = Inventario()
        self.p1 = Producto(1, "Laptop Pro", 1000.0, 5)
        self.p2 = Producto(2, "Mouse Gamer", 50.0, 20)
        self.inventario.agregar_producto(self.p1)
        self.inventario.agregar_producto(self.p2)

    def test_creacion_producto(self):
        """Verifica la creación de un producto con sus atributos."""
        self.assertEqual(self.p1.nombre, "Laptop Pro")
        self.assertEqual(self.p1.precio, 1000.0)
        self.assertEqual(self.p1.stock, 5)

    def test_precio_negativo_error(self):
        """Verifica que un precio negativo lance un error."""
        with self.assertRaises(ValueError):
            Producto(3, "Teclado", -10.0, 5)

    def test_aplicar_descuento(self):
        """Verifica el cálculo del precio con descuento."""
        precio_final = self.p1.aplicar_descuento(20)
        self.assertEqual(precio_final, 800.0)
        self.assertEqual(self.p1.precio, 800.0)

    def test_realizar_venta(self):
        """Verifica la venta de productos, descuento de stock y total con IVA."""
        total = self.inventario.realizar_venta(2, 2) # 2 mouses * 50 = 100 + 16% IVA = 116
        self.assertEqual(total, 116.0)
        self.assertEqual(self.p2.stock, 18)

    def test_venta_stock_insuficiente(self):
        """Verifica que no se pueda vender más stock del disponible."""
        with self.assertRaises(ValueError):
            self.inventario.realizar_venta(1, 10)

    def test_total_inventario(self):
        """Verifica el cálculo total del valor de inventario."""
        self.assertEqual(self.inventario.total_inventario(), 6000.0)

if __name__ == "__main__":
    unittest.main()
