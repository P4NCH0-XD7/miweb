import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import pymongo
from dotenv import load_dotenv
import time

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def transformar_datos():
    print("🔄 Iniciando transformación de datos OLTP a OLAP (Modelo Estrella)...\n")
    client = pymongo.MongoClient(MONGO_URI)
    db = client["ventas_db"]
    inicio = time.time()
    
    pipeline = [
        # 1. Unir con clientes (LEFT JOIN)
        {
            "$lookup": {
                "from": "clientes",
                "localField": "cliente_id",
                "foreignField": "_id",
                "as": "info_cliente"
            }
        },
        {"$unwind": "$info_cliente"},
        
        # 2. Descomponer items de la venta
        {"$unwind": "$items"},
        
        # 3. Unir con productos
        {
            "$lookup": {
                "from": "productos",
                "localField": "items.producto_id",
                "foreignField": "_id",
                "as": "info_producto"
            }
        },
        {"$unwind": "$info_producto"},
        
        # 4. Proyectar al Modelo Dimensional
        {
            "$project": {
                "_id": 0,
                "fecha_venta": 1,
                "anio": {"$year": "$fecha_venta"},
                "mes": {"$month": "$fecha_venta"},
                "dia": {"$dayOfMonth": "$fecha_venta"},
                
                "cliente": {
                    "id": "$info_cliente._id",
                    "nombre": "$info_cliente.nombre",
                    "ciudad": "$info_cliente.direccion.ciudad",
                    "segmento": {
                        "$cond": [
                            {"$gte": ["$total", 5000000]},
                            "Premium",
                            {
                                "$cond": [
                                    {"$gte": ["$total", 1000000]},
                                    "Frecuente",
                                    "Regular"
                                ]
                            }
                        ]
                    }
                },
                
                "producto": {
                    "id": "$info_producto._id",
                    "nombre": "$info_producto.nombre",
                    "categoria": "$info_producto.categoria",
                    "marca": "$info_producto.proveedor"
                },
                
                "cantidad": "$items.cantidad",
                "precio_unitario": "$items.precio_unitario",
                "total_venta": "$items.subtotal",
                "ganancia_estimada": {"$multiply": ["$items.subtotal", 0.15]},
                
                "numero_factura": 1,
                "metodo_pago": 1,
                "estado": 1
            }
        },
        
        # 5. Guardar en colección OLAP
        {
            "$merge": {
                "into": "ventas_analiticas",
                "on": "_id",
                "whenNotMatched": "insert"
            }
        }
    ]
    
    print("⚙️ Ejecutando Aggregation Pipeline...")
    resultado = list(db.ventas.aggregate(pipeline, allowDiskUse=True))
    
    tiempo_total = time.time() - inicio
    total_analitico = db.ventas_analiticas.count_documents({})
    
    print("="*60)
    print("🎉 ¡TRANSFORMACIÓN OLTP A OLAP COMPLETADA!")
    print(f"⏱️  Tiempo de procesamiento: {tiempo_total:.2f} segundos")
    print(f"📊 Registros analíticos generados: {total_analitico}")
    print("="*60)
    
    client.close()

if __name__ == "__main__":
    transformar_datos()
