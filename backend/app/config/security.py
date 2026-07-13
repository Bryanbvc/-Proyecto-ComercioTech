"""
security.py — Configuración de seguridad JWT y hashing de contraseñas

Este módulo centraliza:
- Hashing y verificación de contraseñas con bcrypt
- Generación y validación de tokens JWT
- Dependencias de FastAPI para proteger endpoints por rol
"""

from datetime import datetime, timedelta
from typing import Optional

# jose maneja la creación y verificación de tokens JWT
from jose import JWTError, jwt

# passlib maneja el hashing seguro de contraseñas
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
# Dependencias de FastAPI para inyección en endpoints
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Leer variables de entorno
from dotenv import load_dotenv
import os

load_dotenv()

# ── Configuración JWT ─────────────────────────────────────────────────────────
JWT_SECRET          = os.getenv("JWT_SECRET", "clave-secreta-por-defecto")
JWT_ALGORITHM       = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES  = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

# ── Configuración de hashing ──────────────────────────────────────────────────
# bcrypt es el algoritmo recomendado para contraseñas — es lento por diseño
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAuth2 scheme ─────────────────────────────────────────────────────────────
# Indica a FastAPI que el token se envía en el header Authorization: Bearer <token>
# tokenUrl es la ruta donde el cliente obtiene el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Esquema opcional — no lanza error si no hay token (para rutas públicas)
oauth2_scheme_opcional = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)

# ── Roles definidos ───────────────────────────────────────────────────────────
ROLES = {
    "admin":    4,  # Nivel más alto — acceso total
    "ventas":   3,  # Gestión comercial
    "cliente":  2,  # Solo sus propios datos
    "visitante":1   # Solo lectura pública
}


# ── Funciones de contraseña ───────────────────────────────────────────────────

def hashear_password(password: str) -> str:
    """
    Convierte una contraseña en texto plano a hash bcrypt.

    Parámetros:
        password: contraseña en texto plano

    Retorna:
        string con el hash bcrypt (seguro para almacenar en BD)
    """
    return pwd_context.hash(password)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password_plano, password_hash)
    except (UnknownHashError, ValueError):
        # El hash almacenado no tiene formato bcrypt válido
        # (dato corrupto o insertado fuera del flujo normal de la app)
        return False


# ── Funciones JWT ─────────────────────────────────────────────────────────────

def crear_token(datos: dict) -> str:
    """
    Genera un token JWT firmado con los datos del usuario.

    Parámetros:
        datos: diccionario con información a incluir en el token
               (normalmente: sub=email, rol=rol del usuario)

    Retorna:
        string con el token JWT firmado
    """
    payload = datos.copy()

    # Calcular la fecha de expiración
    expiracion = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload.update({"exp": expiracion})

    # Firmar el token con la clave secreta
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decodificar_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT.

    Parámetros:
        token: string del token JWT recibido en el header

    Retorna:
        diccionario con el payload del token

    Lanza:
        HTTPException 401 si el token es inválido o expiró
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ── Dependencias de FastAPI ───────────────────────────────────────────────────

async def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependencia que extrae el usuario actual desde el token JWT.
    Se usa en endpoints que requieren autenticación obligatoria.

    Retorna:
        dict con email, rol y nombre del usuario autenticado

    Lanza:
        HTTPException 401 si no hay token o es inválido
    """
    payload = decodificar_token(token)

    email = payload.get("sub")
    rol   = payload.get("rol")

    if not email or not rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no contiene información de usuario válida"
        )

    return {"email": email, "rol": rol, "nombre": payload.get("nombre", "")}


async def obtener_usuario_opcional(
    token: Optional[str] = Depends(oauth2_scheme_opcional)
) -> Optional[dict]:
    """
    Dependencia para rutas públicas que también admiten autenticados.
    No lanza error si no hay token — retorna None para visitantes.
    """
    if not token:
        return None
    try:
        return await obtener_usuario_actual(token)
    except HTTPException:
        return None


def requerir_rol(*roles_permitidos: str):
    """
    Fábrica de dependencias que restringe el acceso por rol.

    Uso en un endpoint:
        @router.post("/")
        def crear(usuario = Depends(requerir_rol("admin", "ventas"))):

    Parámetros:
        roles_permitidos: roles que pueden acceder al endpoint

    Retorna:
        función dependencia que valida el rol del usuario
    """
    async def verificar(
        usuario: dict = Depends(obtener_usuario_actual)
    ) -> dict:
        if usuario["rol"] not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {list(roles_permitidos)}"
            )
        return usuario
    return verificar