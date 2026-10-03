"""Módulo principal de miweb con Despliegue Continuo (Render)

y Feature Flags en tiempo real (ConfigCat).
"""

import os
from flask import Flask, jsonify, request
import configcatclient

app = Flask(__name__)

# Configuración de ConfigCat
CONFIGCAT_KEY = os.environ.get(
    "CONFIGCAT_SDK_KEY",
    "configcat-sdk-1/fiHfCI6V1EGE_EUYiFYw8A/-pyqt4kFY0CTfDjixfi6JA",
).strip()

_configcat_client = None


def get_configcat_client():
    """Obtiene o inicializa el cliente singleton de ConfigCat."""
    global _configcat_client
    if _configcat_client is None and CONFIGCAT_KEY:
        try:
            _configcat_client = configcatclient.get(CONFIGCAT_KEY)
        except Exception as e:
            print(f"Advertencia al conectar ConfigCat: {e}")
            _configcat_client = None
    return _configcat_client


def is_feature_enabled(feature_key: str, default: bool = False) -> bool:
    """Consulta de forma segura el estado de un Feature Toggle."""
    client = get_configcat_client()
    if client:
        try:
            return client.get_value(feature_key, default)
        except Exception:
            return default
    return default


class Calculator:
    """Lógica de operaciones matemáticas para el proyecto."""

    def sumar(self, a: float, b: float) -> float:
        return a + b

    def restar(self, a: float, b: float) -> float:
        return a - b

    def multiplicar(self, a: float, b: float) -> float:
        return a * b

    def dividir(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("No es posible dividir entre cero")
        return a / b


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
        subtotal = producto.precio * cantidad
        total = subtotal * 1.16
        return round(total, 2)

    def total_inventario(self) -> float:
        """Calcula el valor total del inventario."""
        total = sum(p.precio * p.stock for p in self.productos.values())
        return round(total, 2)


# Instancias globales
inventario = Inventario()
inventario.agregar_producto(Producto(1, "Laptop Pro", 1000.0, 10))
inventario.agregar_producto(Producto(2, "Mouse Gamer", 50.0, 50))
inventario.agregar_producto(Producto(3, "Teclado Mecanico", 80.0, 30))

calculadora = Calculator()


@app.route("/health")
def health():
    """Health check endpoint para Render."""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "miweb",
                "version": "1.0.0",
                "configcat_connected": bool(CONFIGCAT_KEY),
            }
        ),
        200,
    )


@app.route("/")
def index():
    """Ruta principal con estado de Feature Flags en producción."""
    resta_activa = is_feature_enabled("calculadora_resta", default=False)
    descuento_activo = is_feature_enabled("descuento_iva_toggle", default=False)
    return (
        jsonify(
            {
                "aplicacion": "miweb - Gestión de Inventario y Calculadora TBD",
                "despliegue": "Render Continuous Deployment",
                "feature_flags": {
                    "calculadora_resta": {
                        "activo": resta_activa,
                        "descripcion": "Operación de resta protegida por ConfigCat",
                    },
                    "descuento_iva_toggle": {
                        "activo": descuento_activo,
                        "descripcion": "Descuentos automáticos en ventas",
                    },
                },
                "endpoints": [
                    "/health",
                    "/toggle",
                    "/calculadora/restar",
                    "/inventario",
                    "/venta",
                ],
            }
        ),
        200,
    )


@app.route("/toggle")
def toggle_status():
    """Consulta el estado en vivo de los Feature Flags en ConfigCat."""
    resta_activa = is_feature_enabled("calculadora_resta", default=False)
    descuento_activo = is_feature_enabled("descuento_iva_toggle", default=False)
    return (
        jsonify(
            {
                "flags": {
                    "calculadora_resta": resta_activa,
                    "descuento_iva_toggle": descuento_activo,
                },
                "configcat_sdk_configured": bool(CONFIGCAT_KEY),
            }
        ),
        200,
    )


@app.route("/calculadora/restar", methods=["GET", "POST"])
def calc_restar():
    """Operación de resta protegida por el Feature Toggle 'calculadora_resta'."""
    resta_activa = is_feature_enabled("calculadora_resta", default=False)

    if not resta_activa:
        return (
            jsonify(
                {
                    "error": "Operación de resta desactivada por Feature Flag (Dark Launch / TBD)",
                    "feature_flag": "calculadora_resta",
                    "estado": "OFF (0% Rollout)",
                    "mensaje": "El código existe en producción pero permanece dormido hasta que el PO active el toggle en ConfigCat.",
                }
            ),
            403,
        )

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        a = float(data.get("a", 10))
        b = float(data.get("b", 4))
    else:
        a = float(request.args.get("a", 10))
        b = float(request.args.get("b", 4))

    resultado = calculadora.restar(a, b)
    return (
        jsonify(
            {
                "status": "exitoso",
                "operacion": "resta",
                "a": a,
                "b": b,
                "resultado": resultado,
                "feature_flag": "calculadora_resta",
                "estado": "ON (Activo)",
            }
        ),
        200,
    )


@app.route("/inventario")
def ver_inventario():
    """Lista los productos y el valor total del inventario."""
    prods = [
        {
            "id": p.id_producto,
            "nombre": p.nombre,
            "precio": p.precio,
            "stock": p.stock,
        }
        for p in inventario.productos.values()
    ]
    return (
        jsonify(
            {
                "productos": prods,
                "total_valor_inventario": inventario.total_inventario(),
            }
        ),
        200,
    )


@app.route("/venta", methods=["POST"])
def procesar_venta():
    """Procesa una venta considerando el estado del Feature Toggle."""
    data = request.get_json(silent=True) or {}
    id_prod = int(data.get("id_producto", 1))
    cant = int(data.get("cantidad", 1))
    descuento = float(data.get("descuento", 0.0))

    toggle_activo = is_feature_enabled("descuento_iva_toggle", default=False)

    try:
        prod = inventario.obtener_producto(id_prod)
        if toggle_activo and descuento > 0:
            prod.aplicar_descuento(descuento)

        total = inventario.realizar_venta(id_prod, cant)
        return (
            jsonify(
                {
                    "status": "venta_exitosa",
                    "producto": prod.nombre,
                    "cantidad": cant,
                    "total_con_iva": total,
                    "descuento_aplicado": descuento if toggle_activo else 0.0,
                    "feature_flag_utilizado": toggle_activo,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
