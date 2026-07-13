"""
producto_schema.py — Esquemas de validación para la colección productos

Define las reglas que deben cumplir los datos antes de ser procesados por la API.
Pydantic valida automáticamente cada campo al recibir una petición HTTP.
"""

# BaseModel es la clase base de Pydantic para definir esquemas de datos
from pydantic import BaseModel, Field

# Optional permite que un campo pueda ser None (usado en actualizaciones parciales)
# datetime para manejar fechas
from typing import Optional
from datetime import datetime


class ProductoCreate(BaseModel):
    """
    Esquema para CREAR un producto (método POST).
    Todos los campos son obligatorios excepto descripcion.
    """

    # Field define restricciones adicionales sobre el campo
    # ... significa que el campo es obligatorio (no tiene valor por defecto)
    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre del producto"
    )

    descripcion: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción detallada del producto"
    )

    # gt=0 significa "greater than 0" — el precio debe ser mayor que cero
    precio: float = Field(
        ...,
        gt=0,
        description="Precio en pesos chilenos — debe ser mayor a 0"
    )

    # ge=0 significa "greater than or equal to 0" — el stock puede ser cero
    stock: int = Field(
        ...,
        ge=0,
        description="Unidades disponibles en inventario"
    )

    categoria: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Categoría del producto"
    )

    # Campo con valor por defecto True — todo producto nuevo está activo
    activo: bool = Field(
        default=True,
        description="Si el producto está disponible para la venta"
    )


class ProductoUpdate(BaseModel):
    """
    Esquema para ACTUALIZAR un producto (método PUT).
    Todos los campos son opcionales — solo se actualizan los que se envíen.
    """

    nombre:      Optional[str]   = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str]   = Field(None, max_length=500)
    precio:      Optional[float] = Field(None, gt=0)
    stock:       Optional[int]   = Field(None, ge=0)
    categoria:   Optional[str]   = Field(None, min_length=2, max_length=50)
    activo:      Optional[bool]  = Field(None)


class ProductoResponse(BaseModel):
    """
    Esquema para la RESPUESTA de la API (lo que el cliente recibe).
    Incluye el id como string (MongoDB usa ObjectId internamente).
    """

    id:           str
    nombre:       str
    descripcion:  Optional[str]
    precio:       float
    stock:        int
    categoria:    str
    activo:       bool
    fecha_creacion: Optional[datetime]