"""
Módulo de Gestión de Inventario y Ventas
Contiene la lógica principal del sistema.
"""

class Producto:
    def __init__(self, id_producto: int, nombre: str, precio: float, stock: int):
        if precio < 0:
            raise ValueError("El precio no puede ser negativo")
        if stock < 0:
            raise ValueError("El stock no puede ser negativo")
            
        self.id_producto = id_producto
        self.nombre = nombre
        self.precio = precio
        self.stock = stock

    def aplicar_descuento(self, porcentaje: float) -> float:
        """Aplica un porcentaje de descuento al precio del producto."""
        if not (0 <= porcentaje <= 100):
            raise ValueError("El porcentaje debe estar entre 0 y 100")
        descuento = self.precio * (porcentaje / 100.0)
        self.precio -= descuento
        return round(self.precio, 2)


class Inventario:
    def __init__(self):
        self.productos = {}

    def agregar_producto(self, producto: Producto):
        """Agrega un nuevo producto al inventario."""
        if producto.id_producto in self.productos:
            raise ValueError(f"El producto con ID {producto.id_producto} ya existe")
        self.productos[producto.id_producto] = producto

    def obtener_producto(self, id_producto: int) -> Producto:
        """Obtiene un producto según su ID."""
        if id_producto not in self.productos:
            raise KeyError("Producto no encontrado")
        return self.productos[id_producto]

    def realizar_venta(self, id_producto: int, cantidad: int) -> float:
        """Procesa una venta, actualiza el stock y retorna el total con IVA (16%)."""
        producto = self.obtener_producto(id_producto)
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        if producto.stock < cantidad:
            raise ValueError("Stock insuficiente")
            
        producto.stock -= cantidad
        # ERROR A PROPÓSITO: Se cambió el cálculo del IVA de 1.16 a 1.50 (50% de impuesto erróneo)
        total = subtotal * 1.50
        return round(total, 2)


    def total_inventario(self) -> float:
        """Calcula el valor total del inventario."""
        total = sum(p.precio * p.stock for p in self.productos.values())
        return round(total, 2)
