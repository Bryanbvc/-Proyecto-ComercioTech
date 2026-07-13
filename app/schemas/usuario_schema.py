"""
usuario_schema.py — Esquemas de validación para la colección usuarios
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UsuarioCreate(BaseModel):
    """Esquema para CREAR un usuario (solo admin puede usar este endpoint)."""

    nombre: str = Field(..., min_length=2, max_length=100)
    email:  str = Field(..., description="Email único del usuario")
    password: str = Field(..., min_length=6, description="Contraseña en texto plano — se hashea antes de guardar")
    rol: str = Field(
        default="cliente",
        description="Rol del usuario: admin | ventas | cliente | visitante"
    )
    activo: bool = Field(default=True)


class UsuarioUpdate(BaseModel):
    """Esquema para ACTUALIZAR un usuario."""

    nombre:   Optional[str]  = Field(None, min_length=2, max_length=100)
    email:    Optional[str]  = Field(None)
    password: Optional[str]  = Field(None, min_length=6)
    rol:      Optional[str]  = Field(None)
    activo:   Optional[bool] = Field(None)


class UsuarioResponse(BaseModel):
    """Esquema de respuesta — NUNCA incluye el password_hash."""

    id:             str
    nombre:         str
    email:          str
    rol:            str
    activo:         bool
    fecha_registro: Optional[datetime]


class LoginRequest(BaseModel):
    """Esquema para el endpoint de login."""

    email:    str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña en texto plano")


class TokenResponse(BaseModel):
    """Esquema de respuesta del login — devuelve el token JWT."""

    access_token: str
    token_type:   str = "bearer"
    rol:          str
    nombre:       str