import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import pymongo
from dotenv import load_dotenv
import time
import json

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

def ejecutar_benchmark():
    print("🚀 Iniciando Benchmarking de Consultas Analíticas...\n")
    client = pymongo.MongoClient(MONGO_URI)
    db = client["ventas_db"]
    coleccion = db["ventas_analiticas"]
    
    # 1. Crear índices compuestos
    print("🔧 Fase 1: Aplicando estrategia de indexación...")
    coleccion.create_index([("anio", 1), ("mes", 1), ("dia", 1)], name="idx_fecha")
    coleccion.create_index([("producto.categoria", 1), ("total_venta", -1)], name="idx_categoria_venta")
    coleccion.create_index([("cliente.segmento", 1), ("cliente.ciudad", 1)], name="idx_segmento_ciudad")
    coleccion.create_index([("estado", 1), ("cliente.segmento", 1), ("cliente.ciudad", 1)], name="idx_estado_segmento_ciudad")
    print("✅ Índices creados exitosamente.\n")
    
    # 2. Consultas analíticas
    consultas = [
        {
            "nombre": "1. Ventas totales mensuales",
            "pipeline": [
                {"$group": {"_id": {"anio": "$anio", "mes": "$mes"}, "ingresos_totales": {"$sum": "$total_venta"}, "transacciones": {"$sum": 1}}},
                {"$sort": {"_id.anio": 1, "_id.mes": 1}}
            ]
        },
        {
            "nombre": "2. Top 5 Productos por Categoría",
            "pipeline": [
                {"$group": {"_id": {"categoria": "$producto.categoria", "producto": "$producto.nombre"}, "ingresos": {"$sum": "$total_venta"}, "unidades": {"$sum": "$cantidad"}}},
                {"$sort": {"_id.categoria": 1, "ingresos": -1}},
                {"$group": {"_id": "$_id.categoria", "todos_productos": {"$push": {"producto": "$_id.producto", "ingresos": "$ingresos"}}}},
                {"$project": {"categoria": "$_id", "top_productos": {"$slice": ["$todos_productos", 5]}, "_id": 0}}
            ]
        },
        {
            "nombre": "3. Rendimiento por Segmento y Ciudad",
            "pipeline": [
                {"$match": {"estado": "Completada"}},
                {"$group": {"_id": {"segmento": "$cliente.segmento", "ciudad": "$cliente.ciudad"}, "ingresos": {"$sum": "$total_venta"}, "ganancia_estimada": {"$sum": "$ganancia_estimada"}}},
                {"$sort": {"ingresos": -1}}
            ]
        },
        {
            "nombre": "4. Ticket Promedio por Método de Pago",
            "pipeline": [
                {"$match": {"estado": "Completada"}},
                {"$group": {"_id": "$metodo_pago", "ticket_promedio": {"$avg": "$total_venta"}, "total_transacciones": {"$sum": 1}, "ingresos_totales": {"$sum": "$total_venta"}}},
                {"$sort": {"ingresos_totales": -1}}
            ]
        },
        {
            "nombre": "5. Ventas por Día de la Semana",
            "pipeline": [
                {"$addFields": {"dia_semana": {"$dayOfWeek": "$fecha_venta"}}},
                {"$group": {"_id": "$dia_semana", "ingresos": {"$sum": "$total_venta"}, "ventas_count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
        }
    ]
    
    print("⚙️ Fase 2: Ejecutando consultas...\n")
    print("-" * 70)
    
    tiempos_totales = []
    
    for consulta in consultas:
        print(f"▶️ {consulta['nombre']}")
        
        inicio = time.perf_counter()
        resultados = list(coleccion.aggregate(consulta['pipeline'], allowDiskUse=True))
        fin = time.perf_counter()
        
        tiempo_ms = (fin - inicio) * 1000
        tiempos_totales.append(tiempo_ms)
        
        print(f"   ⏱️ Latencia: {tiempo_ms:.2f} ms | 📊 Filas: {len(resultados)}")
        
        if len(resultados) > 0:
            resultado_limpio = json.loads(json.dumps(resultados[0], default=str))
            print(f"   💡 Muestra: {resultado_limpio}")
        print("-" * 70)
    
    # 3. Resumen
    promedio_latencia = sum(tiempos_totales) / len(tiempos_totales)
    
    print("\n" + "="*70)
    print("📊 RESUMEN DE BENCHMARKING")
    print("="*70)
    print(f"📈 Consultas ejecutadas: {len(consultas)}")
    print(f"⏱️  Latencia promedio: {promedio_latencia:.2f} ms")
    print(f"🚀 Latencia máxima: {max(tiempos_totales):.2f} ms")
    print(f"💾 Registros procesados: {coleccion.count_documents({})}")
    print("="*70)
    
    client.close()

if __name__ == "__main__":
    ejecutar_benchmark()
