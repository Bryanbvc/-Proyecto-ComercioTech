"""
settings.py — Configuración central del proyecto ComercioTech

Centraliza la lectura de todas las variables de entorno del archivo .env
y las expone como constantes para usar en cualquier parte del proyecto.
"""

from dotenv import load_dotenv
import os

# Cargar el archivo .env desde la raíz del proyecto
load_dotenv()

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URI      = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "comerciotech_db")

# ── FastAPI ───────────────────────────────────────────────────────────────────
API_HOST   = os.getenv("API_HOST", "0.0.0.0")
API_PORT   = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"