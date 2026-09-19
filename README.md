# Arquitectura de Datos con MongoDB Atlas - Sistema de Ventas (OLTP / OLAP) :)

Proyecto de implementación completa de una arquitectura de datos transaccional y analítica en la nube utilizando **MongoDB Atlas**, **Python**, y **PyMongo**.

---

## 🛠️ Tecnologías y Librerías

- **Motor de Base de Datos:** MongoDB Atlas (Cluster distribuido Replica Set $\ge 3$ nodos).
- **Lenguaje:** Python 3.x
- **Librerías:**
  - `pymongo` & `dnspython`: Conectividad y operaciones sobre MongoDB.
  - `python-dotenv`: Carga segura de variables de entorno (`.env`).
  - `faker`: Generación sintética masiva de datos adaptada a Colombia (`es_CO`).

---

## 📁 Estructura del Proyecto

```text
├── .env                              # Variables de entorno y URI de conexión a Atlas
├── conexion.py                       # Prueba de conectividad con ping administrativo
├── INFORME_PARCIAL_BD.md             # Informe técnico y justificaciones arquitectónicas
├── scripts/
│   ├── crear_estructura.py           # Creación de colecciones OLTP, índices y semillas
│   ├── generar_datos_masivos.py      # Ingesta por lotes (5.000 clientes, 1.000 productos, 50.000 ventas)
│   ├── transformar_oltp_a_olap.py    # Pipeline ETL de agregación nativo hacia modelo estrella
│   └── benchmarking.py               # Estrategia de índices compuestos y medición de latencias
```

---

## 🚀 Guía de Ejecución

### 1. Instalación de dependencias
```bash
pip install pymongo dnspython python-dotenv faker
```

### 2. Configuración de variables de entorno
Crear un archivo `.env` en la raíz del proyecto con la URI del cluster:
```env
MONGO_URI="mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/?appName=Reto"
```

### 3. Fase 1: Verificación de conexión
```bash
python conexion.py
```

### 4. Fase 2: Creación de estructura OLTP y OLAP
```bash
python scripts/crear_estructura.py
```

### 5. Fase 3: Generación masiva de datos (Batch Insert)
```bash
python scripts/generar_datos_masivos.py
```

### 6. Fase 4: Transformación ETL (OLTP ➔ OLAP)
```bash
python scripts/transformar_oltp_a_olap.py
```

### 7. Fase 5: Indexación compuesta y Benchmarking
```bash
python scripts/benchmarking.py
```

:)