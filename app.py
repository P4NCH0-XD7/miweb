"""Módulo principal de miweb con Despliegue Continuo (Render)

y Feature Flags en tiempo real (ConfigCat).
Ejemplo 1: Lista de Deseos (Wishlist) en e-commerce.
"""

import os
from flask import Flask, jsonify, render_template, request
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


class Wishlist:
    """Módulo de Lista de Deseos (Ejemplo 1 de Slicing Vertical)."""

    def __init__(self):
        self.items = set()

    def agregar_item(self, id_producto: int):
        self.items.add(id_producto)

    def remover_item(self, id_producto: int):
        self.items.discard(id_producto)

    def obtener_items(self):
        return sorted(list(self.items))


class PagosExpress:
    """Módulo de Pagos Express con un solo clic (Caso Taller 6).

    Incluye telemetría en tiempo real de conversión y tasa de error para
    habilitar una Liberación Segura (Canary 20%) y criterio de Kill-Switch.
    """

    UMBRAL_ERROR_ROLLBACK_PCT = 2.0

    def __init__(self):
        self.intentos = 0
        self.exitos = 0
        self.errores = 0
        self.ingresos_totales = 0.0
        self.historial = []

    def procesar_pago(
        self,
        inv: Inventario,
        id_producto: int,
        cantidad: int = 1,
        metodo_pago: str = "Tarjeta Guardada 1-Clic",
    ) -> dict:
        """Ejecuta un compra instantánea 1-clic registrando métricas de conversión y error."""
        self.intentos += 1
        try:
            prod = inv.obtener_producto(id_producto)
            total = inv.realizar_venta(id_producto, cantidad)
            self.exitos += 1
            self.ingresos_totales = round(self.ingresos_totales + total, 2)
            transaccion = {
                "id_transaccion": self.intentos,
                "producto": prod.nombre,
                "cantidad": cantidad,
                "total_con_iva": total,
                "metodo_pago": metodo_pago,
                "estado": "APROBADO",
            }
            self.historial.append(transaccion)
            return transaccion
        except Exception as exc:
            self.errores += 1
            self.historial.append(
                {
                    "id_transaccion": self.intentos,
                    "id_producto": id_producto,
                    "cantidad": cantidad,
                    "estado": "ERROR",
                    "detalle": str(exc),
                }
            )
            raise

    def registrar_error_pasarela(self, detalle: str = "Timeout en pasarela 1-Clic"):
        """Registra un fallo simulado para validar alertas de rollback y Kill-Switch."""
        self.intentos += 1
        self.errores += 1
        self.historial.append(
            {
                "id_transaccion": self.intentos,
                "estado": "ERROR_PASARELA",
                "detalle": detalle,
            }
        )

    def obtener_metricas(self) -> dict:
        """Calcula métricas de observabilidad para decidir avanzar o apagar el toggle."""
        if self.intentos > 0:
            tasa_conversion = round((self.exitos / self.intentos) * 100.0, 2)
            tasa_error = round((self.errores / self.intentos) * 100.0, 2)
        else:
            tasa_conversion = 100.0
            tasa_error = 0.0

        alerta_rollback = (
            self.intentos > 0 and tasa_error > self.UMBRAL_ERROR_ROLLBACK_PCT
        )

        return {
            "intentos_totales": self.intentos,
            "pagos_exitosos": self.exitos,
            "pagos_con_error": self.errores,
            "tasa_conversion_pct": tasa_conversion,
            "tasa_error_pct": tasa_error,
            "ingresos_express": round(self.ingresos_totales, 2),
            "umbral_max_error_pct": self.UMBRAL_ERROR_ROLLBACK_PCT,
            "alerta_rollback": alerta_rollback,
            "estado_salud": (
                "ALERTA_KILL_SWITCH" if alerta_rollback else "SALUDABLE"
            ),
            "accion_recomendada": (
                "Apagar toggle pagos_express_v1 en ConfigCat inmediatamente (Tasa de error > 2%)"
                if alerta_rollback
                else "Mantener rollout progresivo (Interno -> 20% Canary -> 100%)"
            ),
            "historial_reciente": self.historial[-5:],
        }


# Instancias globales
inventario = Inventario()
inventario.agregar_producto(Producto(1, "Laptop Pro", 1000.0, 10))
inventario.agregar_producto(Producto(2, "Mouse Gamer", 50.0, 50))
inventario.agregar_producto(Producto(3, "Teclado Mecanico", 80.0, 30))

wishlist = Wishlist()
pagos_express = PagosExpress()


@app.route("/health")
def health():
    """Health check endpoint para Render."""
    metricas_pe = pagos_express.obtener_metricas()
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "miweb",
                "version": "1.1.0",
                "configcat_connected": bool(CONFIGCAT_KEY),
                "observabilidad_pagos_express": metricas_pe["estado_salud"],
            }
        ),
        200,
    )


@app.route("/")
def index():
    """Ruta principal: renderiza la interfaz web interactiva en navegadores
    o devuelve JSON si es consultada como API/tests.
    """
    accept = request.headers.get("Accept", "")
    if (
        "text/html" in accept
        and "application/json" not in accept
        and request.args.get("format") != "json"
    ):
        return render_template("index.html")

    wishlist_activo = is_feature_enabled("wishlist_enabled", default=False)
    descuento_activo = is_feature_enabled("descuento_iva_toggle", default=False)
    pagos_express_activo = is_feature_enabled("pagos_express_v1", default=False)
    return (
        jsonify(
            {
                "aplicacion": "miweb - Tienda en Línea e Inventario TBD",
                "despliegue": "Render Continuous Deployment",
                "feature_flags": {
                    "wishlist_enabled": {
                        "activo": wishlist_activo,
                        "descripcion": "Lista de deseos para guardar productos favoritos",
                        "ejemplo": "Ejemplo 1 de Slicing Vertical",
                    },
                    "pagos_express_v1": {
                        "activo": pagos_express_activo,
                        "toggle_alias": "pagos-express-v1",
                        "descripcion": "Compra rápida 1-Clic con telemetría de conversión y error (Caso Taller 6)",
                        "estrategia_release": "Rollout progresivo: Interno -> 20% Canary -> 100%",
                    },
                    "descuento_iva_toggle": {
                        "activo": descuento_activo,
                        "descripcion": "Descuentos automáticos en ventas",
                    },
                },
                "endpoints": [
                    "/health",
                    "/toggle",
                    "/wishlist",
                    "/pagos-express",
                    "/pagos-express/metricas",
                    "/inventario",
                    "/venta",
                    "/dashboard",
                ],
            }
        ),
        200,
    )


@app.route("/dashboard")
@app.route("/app")
@app.route("/ui")
def dashboard():
    """Ruta directa para abrir la interfaz frontend interactiva."""
    return render_template("index.html")


@app.route("/toggle")
def toggle_status():
    """Consulta el estado en vivo de los Feature Flags en ConfigCat."""
    wishlist_activo = is_feature_enabled("wishlist_enabled", default=False)
    descuento_activo = is_feature_enabled("descuento_iva_toggle", default=False)
    pagos_express_activo = is_feature_enabled("pagos_express_v1", default=False)
    return (
        jsonify(
            {
                "flags": {
                    "wishlist_enabled": wishlist_activo,
                    "pagos_express_v1": pagos_express_activo,
                    "descuento_iva_toggle": descuento_activo,
                },
                "configcat_sdk_configured": bool(CONFIGCAT_KEY),
            }
        ),
        200,
    )


@app.route("/wishlist", methods=["GET", "POST"])
def gestionar_wishlist():
    """Endpoint de Lista de Deseos (Ticket 1 protegido por Feature Flag 'wishlist_enabled')."""
    wishlist_activo = is_feature_enabled("wishlist_enabled", default=False)

    if not wishlist_activo:
        return (
            jsonify(
                {
                    "error": "Funcionalidad de Lista de Deseos (Wishlist) desactivada por Feature Flag (Dark Launch / TBD)",
                    "feature_flag": "wishlist_enabled",
                    "estado": "OFF (0% Rollout)",
                    "mensaje": "El código existe en producción pero permanece dormido hasta que el Product Owner active el toggle en ConfigCat.",
                }
            ),
            403,
        )

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        id_prod = int(data.get("id_producto", 1))
        try:
            prod = inventario.obtener_producto(id_prod)
            wishlist.agregar_item(id_prod)
            return (
                jsonify(
                    {
                        "status": "exitoso",
                        "mensaje": f"Producto '{prod.nombre}' agregado a tu Lista de Deseos",
                        "id_producto": id_prod,
                        "producto": prod.nombre,
                        "precio": prod.precio,
                        "feature_flag": "wishlist_enabled",
                        "estado": "ON (Activo)",
                    }
                ),
                200,
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # GET: Listar productos guardados
    items_ids = wishlist.obtener_items()
    productos_guardados = [
        {
            "id": inventario.obtener_producto(p_id).id_producto,
            "nombre": inventario.obtener_producto(p_id).nombre,
            "precio": inventario.obtener_producto(p_id).precio,
        }
        for p_id in items_ids
        if p_id in inventario.productos
    ]

    return (
        jsonify(
            {
                "status": "exitoso",
                "feature_flag": "wishlist_enabled",
                "estado": "ON (Activo)",
                "total_productos_guardados": len(productos_guardados),
                "wishlist": productos_guardados,
            }
        ),
        200,
    )


@app.route("/wishlist/<int:id_producto>", methods=["DELETE"])
@app.route("/wishlist/remover", methods=["POST"])
def remover_de_wishlist(id_producto=None):
    """Permite eliminar un producto de la Lista de Deseos."""
    wishlist_activo = is_feature_enabled("wishlist_enabled", default=False)
    if not wishlist_activo:
        return (
            jsonify(
                {
                    "error": "Funcionalidad desactivada por Feature Flag (Dark Launch / TBD)",
                    "feature_flag": "wishlist_enabled",
                    "estado": "OFF (0% Rollout)",
                }
            ),
            403,
        )

    if id_producto is None:
        data = request.get_json(silent=True) or {}
        id_producto = int(data.get("id_producto", 0))

    wishlist.remover_item(id_producto)
    return (
        jsonify(
            {
                "status": "exitoso",
                "mensaje": f"Producto {id_producto} removido de la Lista de Deseos",
                "id_producto": id_producto,
                "wishlist": wishlist.obtener_items(),
            }
        ),
        200,
    )


@app.route("/pagos-express", methods=["POST"])
def ejecutar_pago_express():
    """Endpoint de Pagos Express 1-Clic protegido por Feature Flag 'pagos_express_v1'.

    Resuelve el Caso del Taller 6: 'La funcionalidad de Pagos Express ya está
    en main, pero nadie se atreve a activarla'.
    """
    pagos_express_activo = is_feature_enabled("pagos_express_v1", default=False)

    if not pagos_express_activo:
        return (
            jsonify(
                {
                    "error": "Pagos Express 1-Clic desactivado por Feature Flag (Deploy != Release)",
                    "feature_flag": "pagos_express_v1",
                    "toggle_alias": "pagos-express-v1",
                    "estado": "OFF (0% Rollout - Dark Launch)",
                    "mensaje": (
                        "El código ya está desplegado en main desde hace 9 días, "
                        "pero permanece apagado para el 100% de usuarios hasta que el PO "
                        "ejecute la estrategia de liberación gradual (Interno -> 20% Canary -> 100%)."
                    ),
                }
            ),
            403,
        )

    data = request.get_json(silent=True) or {}
    if data.get("simular_error"):
        pagos_express.registrar_error_pasarela(
            str(data.get("motivo", "Fallo simulado en pasarela 1-Clic"))
        )
        return (
            jsonify(
                {
                    "error": "Error en pasarela de Pago Express registrado en telemetría",
                    "feature_flag": "pagos_express_v1",
                    "metricas": pagos_express.obtener_metricas(),
                }
            ),
            502,
        )

    id_prod = int(data.get("id_producto", 1))
    cant = int(data.get("cantidad", 1))
    metodo = str(data.get("metodo_pago", "Tarjeta Guardada 1-Clic"))

    try:
        tx = pagos_express.procesar_pago(inventario, id_prod, cant, metodo)
        return (
            jsonify(
                {
                    "status": "pago_express_exitoso",
                    "mensaje": f"⚡ Pago Express 1-Clic completado para '{tx['producto']}'",
                    "transaccion": tx,
                    "feature_flag": "pagos_express_v1",
                    "estado": "ON (Liberación Controlada)",
                    "metricas": pagos_express.obtener_metricas(),
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": str(e),
                    "feature_flag": "pagos_express_v1",
                    "metricas": pagos_express.obtener_metricas(),
                }
            ),
            400,
        )


@app.route("/pagos-express/metricas", methods=["GET"])
def metricas_pagos_express():
    """Devuelve en tiempo real la telemetría de conversión, error y plan de liberación segura."""
    pagos_express_activo = is_feature_enabled("pagos_express_v1", default=False)
    metricas = pagos_express.obtener_metricas()
    return (
        jsonify(
            {
                "feature_flag": "pagos_express_v1",
                "toggle_alias": "pagos-express-v1",
                "activo": pagos_express_activo,
                "estado_release": (
                    "ON (Rollout Activo en Producción)"
                    if pagos_express_activo
                    else "OFF (Dark Launch en main - 0% usuarios)"
                ),
                "telemetria": metricas,
                "plan_liberacion_segura": {
                    "fase_1": "Usuarios internos / QA (Validación de telemetría y health check)",
                    "fase_2": "Canary 20% usuarios este viernes (Ventana de observación 24h-48h)",
                    "fase_3": "Escalamiento 50% -> 100% si tasa de error < 2.0% y conversión estable",
                    "criterio_kill_switch": "Desactivar toggle en ConfigCat (< 5 seg) si tasa_error > 2% o latencia > 800ms",
                },
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


@app.route("/inventario/producto", methods=["POST"])
def crear_producto():
    """Permite añadir un nuevo producto al inventario desde el frontend."""
    data = request.get_json(silent=True) or {}
    try:
        id_prod = int(
            data.get(
                "id_producto",
                max(inventario.productos.keys(), default=0) + 1,
            )
        )
        nombre = str(data.get("nombre", f"Producto #{id_prod}")).strip()
        precio = float(data.get("precio", 10.0))
        stock = int(data.get("stock", 5))

        prod = Producto(id_prod, nombre, precio, stock)
        inventario.agregar_producto(prod)
        return (
            jsonify(
                {
                    "status": "exitoso",
                    "mensaje": f"Producto '{nombre}' agregado exitosamente",
                    "producto": {
                        "id": prod.id_producto,
                        "nombre": prod.nombre,
                        "precio": prod.precio,
                        "stock": prod.stock,
                    },
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


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
