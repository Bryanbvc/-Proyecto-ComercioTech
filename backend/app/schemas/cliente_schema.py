"""
cliente_schema.py — Esquemas de validación para la colección clientes
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class DireccionSchema(BaseModel):
    """
    Subdocumento embebido que representa la dirección del cliente.
    Se usa dentro de ClienteCreate y ClienteResponse.
    """
    calle:          Optional[str] = Field(None, max_length=200)
    ciudad:         Optional[str] = Field(None, max_length=100)
    region:         Optional[str] = Field(None, max_length=100)
    codigo_postal:  Optional[str] = Field(None, max_length=20)
    pais:           Optional[str] = Field(None, max_length=100)


class ClienteCreate(BaseModel):
    """Esquema para CREAR un cliente (POST)."""

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre completo del cliente"
    )

    # EmailStr valida automáticamente que el formato del email sea correcto
    email: str = Field(
        ...,
        description="Email único del cliente"
    )

    telefono: Optional[str] = Field(
        None,
        max_length=20,
        description="Teléfono de contacto"
    )

    activo: bool = Field(
        default=True,
        description="Estado del cliente"
    )

    # El subdocumento dirección es opcional al crear
    direccion: Optional[DireccionSchema] = Field(
        None,
        description="Dirección de envío del cliente"
    )


class ClienteUpdate(BaseModel):
    """Esquema para ACTUALIZAR un cliente (PUT). Todos los campos opcionales."""

    nombre:    Optional[str]             = Field(None, min_length=2, max_length=100)
    email:     Optional[str]             = Field(None)
    telefono:  Optional[str]             = Field(None, max_length=20)
    activo:    Optional[bool]            = Field(None)
    direccion: Optional[DireccionSchema] = Field(None)


class ClienteResponse(BaseModel):
    """Esquema de respuesta al cliente."""

    id:               str
    nombre:           str
    email:            str
    telefono:         Optional[str]
    activo:           bool
    fecha_registro:   Optional[datetime]
    direccion:        Optional[DireccionSchema]