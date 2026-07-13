"""
auth.py — Endpoints de autenticación

Maneja el registro y login de usuarios.
Genera tokens JWT que el frontend debe incluir en cada petición.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.database.connection import coleccion_usuarios, coleccion_clientes
from app.schemas.usuario_schema import LoginRequest, TokenResponse, UsuarioCreate
from app.config.security import (
    hashear_password,
    verificar_password,
    crear_token
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

ROLES_VALIDOS = ["admin", "ventas", "cliente", "visitante"]


@router.post("/login", response_model=TokenResponse)
def login(credenciales: LoginRequest):
    """
    Autentica un usuario y devuelve un token JWT.

    Método: POST /auth/login
    Body: email + password

    Retorna: token JWT + rol + nombre
    Lanza: 401 si las credenciales son incorrectas
    """
    # Buscar usuario por email
    usuario = coleccion_usuarios.find_one({"email": credenciales.email})

    if not usuario:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    # Verificar que el usuario esté activo
    if not usuario.get("activo", False):
        raise HTTPException(status_code=401, detail="Usuario desactivado. Contacte al administrador.")

    # Verificar la contraseña contra el hash almacenado
    if not verificar_password(credenciales.password, usuario["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    # Generar el token JWT con email y rol del usuario
    token = crear_token({
        "sub":    usuario["email"],
        "rol":    usuario["rol"],
        "nombre": usuario["nombre"]
    })

    return {
        "access_token": token,
        "token_type":   "bearer",
        "rol":          usuario["rol"],
        "nombre":       usuario["nombre"]
    }


@router.post("/register", status_code=201)
def registrar_cliente(usuario: UsuarioCreate):
    """
    Permite el auto-registro de nuevos usuarios con rol 'cliente'.
    El rol se fuerza a 'cliente' independiente de lo que envíe el body.

    Método: POST /auth/register
    Body: nombre, email, password
    """
    # Verificar email duplicado
    if coleccion_usuarios.find_one({"email": usuario.email}):
        raise HTTPException(status_code=400, detail=f"El email '{usuario.email}' ya está registrado")

    # Forzar rol cliente en auto-registro — seguridad importante
    nuevo_usuario = {
        "nombre":        usuario.nombre,
        "email":         usuario.email,
        "password_hash": hashear_password(usuario.password),
        "rol":           "cliente",  # Siempre cliente en auto-registro
        "activo":        True,
        "fecha_registro": datetime.utcnow()
    }

    coleccion_usuarios.insert_one(nuevo_usuario)
    if not coleccion_clientes.find_one({"email": usuario.email}):
        coleccion_clientes.insert_one({
            "nombre":         usuario.nombre,
            "email":          usuario.email,
            "telefono":       None,
            "activo":         True,
            "direccion":      None,
            "fecha_registro": datetime.utcnow()
        })

    return {"mensaje": "Usuario registrado correctamente. Ya puedes iniciar sesión."}
