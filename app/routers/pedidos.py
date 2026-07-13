"""
routers/pedidos.py — Endpoints CRUD para la colección pedidos

Este router es el más complejo porque maneja referencias a clientes
y arreglos de ítems con producto_id embebido.
"""
from app.config.security import requerir_rol, obtener_usuario_actual
from fastapi import Depends
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.database.connection import coleccion_pedidos, coleccion_clientes, coleccion_productos
from app.schemas.pedido_schema import PedidoCreate, PedidoUpdate
from app.models.serializers import serializar_pedido, serializar_pedidos
from datetime import datetime

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"]
)

def validar_object_id(id: str) -> ObjectId:
    """Valida que el string sea un ObjectId válido de MongoDB."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=400,
            detail=f"El ID '{id}' no es un ObjectId válido de MongoDB"
        )
    return ObjectId(id)


@router.post("/", status_code=201)
def crear_pedido(
    pedido: PedidoCreate,
    usuario: dict = Depends(requerir_rol("admin", "ventas", "cliente"))
):
    if usuario["rol"] == "cliente":
        cliente_propio = coleccion_clientes.find_one({"email": usuario["email"]})
        if not cliente_propio:
            raise HTTPException(
                status_code=400,
                detail="No tienes un perfil de cliente asociado. Contacta a soporte."
            )
        cliente_oid = cliente_propio["_id"]
    else:
        cliente_oid = validar_object_id(pedido.cliente_id)
        if not coleccion_clientes.find_one({"_id": cliente_oid}):
            raise HTTPException(
                status_code=404,
                detail=f"Cliente con ID '{pedido.cliente_id}' no encontrado"
            )

    items_procesados = []
    total = 0.0

    for item in pedido.items:
        producto_oid = validar_object_id(item.producto_id)
        producto = coleccion_productos.find_one({"_id": producto_oid})

        if not producto:
            raise HTTPException(
                status_code=404,
                detail=f"Producto con ID '{item.producto_id}' no encontrado"
            )

        item_doc = {
            "producto_id": producto_oid,
            "nombre_producto": producto["nombre"],
            "cantidad": item.cantidad,
            "precio_unitario": item.precio_unitario or producto["precio"]
        }

        items_procesados.append(item_doc)
        total += item_doc["cantidad"] * item_doc["precio_unitario"]

    nuevo_pedido = {
        "cliente_id": cliente_oid,
        "fecha_pedido": datetime.utcnow(),
        "estado": "pendiente",
        "items": items_procesados,
        "total": round(total, 2),
        "direccion_envio": pedido.direccion_envio,
        "notas": pedido.notas
    }

    resultado = coleccion_pedidos.insert_one(nuevo_pedido)
    # Recuperar el documento insertado y devolverlo serializado
    pedido_insertado = coleccion_pedidos.find_one({"_id": resultado.inserted_id})
    return serializar_pedido(pedido_insertado)


@router.get("/")
def listar_pedidos(usuario: dict = Depends(obtener_usuario_actual)):
    if usuario["rol"] in ("admin", "ventas"):
        pedidos = coleccion_pedidos.find().sort("fecha_pedido", -1)
    elif usuario["rol"] == "cliente":
        cliente_propio = coleccion_clientes.find_one({"email": usuario["email"]})
        if not cliente_propio:
            return []
        pedidos = coleccion_pedidos.find({"cliente_id": cliente_propio["_id"]}).sort("fecha_pedido", -1)
    else:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return serializar_pedidos(pedidos)


@router.get("/{pedido_id}")
def obtener_pedido(pedido_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    oid = validar_object_id(pedido_id)
    pedido = coleccion_pedidos.find_one({"_id": oid})

    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID '{pedido_id}' no encontrado")

    if usuario["rol"] == "cliente":
        cliente_propio = coleccion_clientes.find_one({"email": usuario["email"]})
        if not cliente_propio or pedido["cliente_id"] != cliente_propio["_id"]:
            raise HTTPException(status_code=403, detail="No puedes ver pedidos de otro cliente")
    elif usuario["rol"] not in ("admin", "ventas"):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    return serializar_pedido(pedido)


@router.put("/{pedido_id}")
def actualizar_pedido(pedido_id: str, pedido: PedidoUpdate, usuario: dict = Depends(requerir_rol("admin", "ventas", "cliente"))):
    """
    Actualiza el estado o notas de un pedido existente.

    Método: PUT /pedidos/{pedido_id}
    Body: estado y/o notas

    Estados válidos: pendiente → confirmado → enviado → entregado → cancelado
    """
    oid = validar_object_id(pedido_id)

    # Validar que el estado sea uno de los valores permitidos
    estados_validos = ["pendiente", "confirmado", "enviado", "entregado", "cancelado"]
    if pedido.estado and pedido.estado not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Valores permitidos: {estados_validos}"
        )

    datos_actualizar = {
        k: v for k, v in pedido.model_dump(exclude_none=True).items()
    }

    if not datos_actualizar:
        raise HTTPException(
            status_code=400,
            detail="No se enviaron datos para actualizar"
        )

    resultado = coleccion_pedidos.update_one(
        {"_id": oid},
        {"$set": datos_actualizar}
    )

    if resultado.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Pedido con ID '{pedido_id}' no encontrado"
        )

    pedido_actualizado = coleccion_pedidos.find_one({"_id": oid})
    return {
        "mensaje": "Pedido actualizado correctamente",
        "pedido": serializar_pedido(pedido_actualizado)
    }

@router.put("/{pedido_id}/cancelar")
def cancelar_pedido(pedido_id: str, usuario: dict = Depends(requerir_rol("admin", "ventas", "cliente"))):
    """
    Cancela un pedido.
    - admin/ventas: pueden cancelar cualquier pedido, en cualquier estado.
    - cliente: solo puede cancelar SU PROPIO pedido, y solo si está en estado 'pendiente'.
    """
    oid = validar_object_id(pedido_id)
    pedido = coleccion_pedidos.find_one({"_id": oid})
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID '{pedido_id}' no encontrado")

    if usuario["rol"] == "cliente":
        cliente_propio = coleccion_clientes.find_one({"email": usuario["email"]})
        if not cliente_propio or pedido["cliente_id"] != cliente_propio["_id"]:
            raise HTTPException(status_code=403, detail="No puedes cancelar pedidos de otro cliente")
        if pedido["estado"] != "pendiente":
            raise HTTPException(status_code=400, detail="Solo se pueden cancelar pedidos en estado 'pendiente'")

    coleccion_pedidos.update_one({"_id": oid}, {"$set": {"estado": "cancelado"}})
    actualizado = coleccion_pedidos.find_one({"_id": oid})
    return serializar_pedido(actualizado)

@router.delete("/{pedido_id}", dependencies=[Depends(requerir_rol("admin"))])
def eliminar_pedido(pedido_id: str):
    """
    Elimina un pedido de la base de datos.

    Método: DELETE /pedidos/{pedido_id}
    Lanza: 404 si no existe, 400 si el ID es inválido
    """
    oid = validar_object_id(pedido_id)
    resultado = coleccion_pedidos.delete_one({"_id": oid})

    if resultado.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Pedido con ID '{pedido_id}' no encontrado"
        )

    return {"mensaje": f"Pedido '{pedido_id}' eliminado correctamente"}