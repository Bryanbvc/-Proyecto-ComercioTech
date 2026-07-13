"""
pedido_schema.py — Esquemas de validación para la colección pedidos
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ItemPedidoSchema(BaseModel):
    """
    Subdocumento embebido que representa un ítem dentro de un pedido.
    Incluye snapshot del precio para preservar el precio histórico.
    """

    # ID del producto como string — lo convertimos a ObjectId en el router
    producto_id:     str   = Field(..., description="ID del producto")
    nombre_producto: Optional[str] = Field(None, description="Nombre del producto al momento del pedido")
    cantidad:        int   = Field(..., ge=1, description="Cantidad ordenada — mínimo 1")
    precio_unitario: float = Field(..., gt=0, description="Precio unitario al momento del pedido")


class PedidoCreate(BaseModel):
    """Esquema para CREAR un pedido (POST)."""

    # ID del cliente como string — lo convertimos a ObjectId en el router
    cliente_id: Optional[str] = Field(
        None,
        description="ID del cliente. Obligatorio para admin/ventas; se ignora y se autocompleta si el rol es 'cliente'."
    )

    # Lista de ítems — debe tener al menos uno
    items: List[ItemPedidoSchema] = Field(
        ...,
        min_length=1,
        description="Lista de productos del pedido"
    )

    direccion_envio: Optional[dict] = Field(
        None,
        description="Dirección de envío del pedido"
    )

    notas: Optional[str] = Field(
        None,
        max_length=500,
        description="Instrucciones especiales del pedido"
    )


class PedidoUpdate(BaseModel):
    """Esquema para ACTUALIZAR un pedido (PUT)."""

    estado: Optional[str] = Field(
        None,
        description="Estado: pendiente, confirmado, enviado, entregado, cancelado"
    )
    notas: Optional[str] = Field(None, max_length=500)


class PedidoResponse(BaseModel):
    """Esquema de respuesta para pedidos."""

    id:              str
    cliente_id:      str
    fecha_pedido:    datetime
    estado:          str
    items:           List[ItemPedidoSchema]
    total:           float
    direccion_envio: Optional[dict]
    notas:           Optional[str]