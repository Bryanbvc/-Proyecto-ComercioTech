"""
connection.py — Conexión a MongoDB para el proyecto ComercioTech

Este módulo gestiona la conexión entre FastAPI y MongoDB usando PyMongo.
Utiliza variables de entorno para no exponer credenciales en el código.
"""

# ── Importaciones ─────────────────────────────────────────────────────────────

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

import os

# ── Cargar variables de entorno ───────────────────────────────────────────────

# Busca el archivo .env en la carpeta raíz del proyecto y carga las variables
load_dotenv()

# Leer cada variable desde el archivo .env
# Si la variable no existe, usa el valor predeterminado indicado después de la coma
MONGO_URI       = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME   = os.getenv("MONGO_DATABASE", "comerciotech_db")

# ── Crear la conexión a MongoDB ───────────────────────────────────────────────

try:
    # Crear el cliente de MongoDB con configuración de connection pool
    # maxPoolSize: máximo de conexiones simultáneas al pool (evita sobrecargar MongoDB)
    # serverSelectionTimeoutMS: tiempo máximo en ms para detectar que MongoDB no responde
    # connectTimeoutMS: tiempo máximo en ms para establecer la conexión inicial
    client = MongoClient(
        MONGO_URI,
        maxPoolSize=10,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )

    # Verificar que la conexión es real
    client.admin.command("ping")

    # Seleccionar la base de datos del proyecto
    # Si no existe, MongoDB la crea automáticamente al insertar el primer documento
    db = client[DATABASE_NAME]

    # ── Colecciones disponibles ───────────────────────────────────────────────

    coleccion_clientes  = db["clientes"]
    coleccion_productos = db["productos"]
    coleccion_pedidos   = db["pedidos"]
    # Colección de usuarios del sistema (agregada para RBAC)
    coleccion_usuarios  = db["usuarios"]

    # Mensaje de confirmación visible al iniciar el servidor
    print(f"✅ Conexión exitosa a MongoDB — Base de datos: {DATABASE_NAME}")

except ConnectionFailure:
    # Error de red: MongoDB existe pero no se puede alcanzar
    print("❌ Error: No se puede conectar a MongoDB. Verifica que el contenedor Docker esté corriendo.")
    raise

except ServerSelectionTimeoutError:
    # Timeout: MongoDB no respondió en el tiempo definido
    print("❌ Error: Tiempo de espera agotado. Verifica la URI de conexión en el archivo .env")
    raise

except Exception as e:
    # Cualquier otro error inesperado
    print(f"❌ Error inesperado al conectar a MongoDB: {e}")
    raise
