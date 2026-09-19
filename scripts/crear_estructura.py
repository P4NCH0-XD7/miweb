import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import pymongo
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def crear_estructura_ventas():
    client = pymongo.MongoClient(MONGO_URI)
    db = client["ventas_db"]
    
    print("🏗️ Creando estructura de base de datos de ventas...\n")
    
    # 1. Crear colecciones OLTP (Transaccionales)
    print("📦 Creando colecciones transaccionales (OLTP)...")
    colecciones_oltp = ["clientes", "productos", "ventas"]
    colecciones_existentes = db.list_collection_names()
    for col in colecciones_oltp:
        if col not in colecciones_existentes:
            db.create_collection(col)
            print(f"  ✅ Colección '{col}' creada")
        else:
            print(f"  ℹ️ Colección '{col}' ya existe")
    
    # 2. Crear índices para optimizar consultas
    print("\n🔍 Creando índices...")
    db.clientes.create_index([("email", 1)], unique=True)
    db.productos.create_index([("sku", 1)], unique=True)
    db.ventas.create_index([("fecha_venta", -1)])
    db.ventas.create_index([("cliente_id", 1)])
    print("  ✅ Índices creados")
    
    # 3. Insertar datos de prueba
    print("\n📝 Insertando datos de prueba...")
    
    cliente_existente = db.clientes.find_one({"email": "juan.perez@email.com"})
    if not cliente_existente:
        cliente_ejemplo = {
            "codigo_cliente": "CLI001",
            "nombre": "Juan Pérez",
            "email": "juan.perez@email.com",
            "telefono": "3001234567",
            "direccion": {
                "calle": "Calle 123 #45-67",
                "ciudad": "Bogotá",
                "pais": "Colombia"
            },
            "fecha_registro": datetime.now(),
            "activo": True
        }
        db.clientes.insert_one(cliente_ejemplo)
        print("  ✅ Cliente insertado")
    else:
        print("  ℹ️ Cliente de ejemplo ya existe")
    
    producto_existente = db.productos.find_one({"sku": "PROD001"})
    if not producto_existente:
        producto_ejemplo = {
            "sku": "PROD001",
            "nombre": "Laptop Dell XPS 15",
            "categoria": "Electrónica",
            "precio_unitario": 4500000,
            "stock": 25,
            "proveedor": "Dell Colombia S.A.S",
            "fecha_creacion": datetime.now()
        }
        db.productos.insert_one(producto_ejemplo)
        print("  ✅ Producto insertado")
    else:
        print("  ℹ️ Producto de ejemplo ya existe")
    
    cliente_id = db.clientes.find_one({"codigo_cliente": "CLI001"})["_id"]
    prod_id = db.productos.find_one({"sku": "PROD001"})["_id"]
    
    venta_existente = db.ventas.find_one({"numero_factura": "FAC-2026-0001"})
    if not venta_existente:
        venta_ejemplo = {
            "numero_factura": "FAC-2026-0001",
            "cliente_id": cliente_id,
            "fecha_venta": datetime.now(),
            "items": [
                {
                    "producto_id": prod_id,
                    "cantidad": 1,
                    "precio_unitario": 4500000,
                    "subtotal": 4500000
                }
            ],
            "total": 4500000,
            "metodo_pago": "Tarjeta de Crédito",
            "estado": "Completada"
        }
        db.ventas.insert_one(venta_ejemplo)
        print("  ✅ Venta insertada")
    else:
        print("  ℹ️ Venta de ejemplo ya existe")
    
    # 4. Crear colección OLAP (Analítica)
    print("\n📊 Creando colección analítica (OLAP)...")
    if "ventas_analiticas" not in db.list_collection_names():
        db.create_collection("ventas_analiticas")
        print("  ✅ Colección 'ventas_analiticas' creada")
    else:
        print("  ℹ️ Colección 'ventas_analiticas' ya existe")
    
    print("\n✅ Estructura de ventas creada exitosamente en Atlas!")
    print("🔍 Abre MongoDB Compass para ver las colecciones creadas.")
    
    client.close()

if __name__ == "__main__":
    crear_estructura_ventas()
