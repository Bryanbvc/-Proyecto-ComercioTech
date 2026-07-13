"""
routers/clientes.py — Endpoints CRUD para la colección clientes
"""
from app.config.security import requerir_rol
from fastapi import Depends
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.database.connection import coleccion_clientes
from app.schemas.cliente_schema import ClienteCreate, ClienteUpdate
from app.models.serializers import serializar_cliente, serializar_clientes
from datetime import datetime

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

def validar_object_id(id: str) -> ObjectId:
    """Valida que el string sea un ObjectId válido de MongoDB."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=400,
            detail=f"El ID '{id}' no es un ObjectId válido de MongoDB"
        )
    return ObjectId(id)


@router.post("/", status_code=201, dependencies=[Depends(requerir_rol("admin", "ventas"))])
def crear_cliente(cliente: ClienteCreate):
    """
    Crea un nuevo cliente en la base de datos.

    Método: POST /clientes/
    Body: nombre, email, telefono (opcional), direccion (opcional)
    Retorna: cliente creado con ID asignado
    Lanza: 400 si el email ya existe en la base de datos
    """
    # Verificar que el email no esté duplicado antes de insertar
    # El índice único en MongoDB también lo bloquea, pero este mensaje es más claro
    if coleccion_clientes.find_one({"email": cliente.email}):
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un cliente con el email '{cliente.email}'"
        )

    nuevo_cliente = cliente.model_dump()

    # Convertir el subdocumento DireccionSchema a dict si existe
    if nuevo_cliente.get("direccion"):
        nuevo_cliente["direccion"] = dict(nuevo_cliente["direccion"])

    # Registrar la fecha de alta automáticamente
    nuevo_cliente["fecha_registro"] = datetime.utcnow()

    resultado = coleccion_clientes.insert_one(nuevo_cliente)
    cliente_creado = coleccion_clientes.find_one({"_id": resultado.inserted_id})

    return {
        "mensaje": "Cliente creado correctamente",
        "cliente": serializar_cliente(cliente_creado)
    }


@router.get("/", dependencies=[Depends(requerir_rol("admin", "ventas"))])
def listar_clientes():
    """
    Retorna todos los clientes registrados.

    Método: GET /clientes/
    Retorna: lista de todos los clientes
    """
    clientes = coleccion_clientes.find()
    return serializar_clientes(clientes)


@router.get("/{cliente_id}", dependencies=[Depends(requerir_rol("admin", "ventas"))])
def obtener_cliente(cliente_id: str):
    """
    Retorna un cliente específico por su ID.

    Método: GET /clientes/{cliente_id}
    Lanza: 404 si no existe, 400 si el ID es inválido
    """
    oid = validar_object_id(cliente_id)
    cliente = coleccion_clientes.find_one({"_id": oid})

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente con ID '{cliente_id}' no encontrado"
        )

    return serializar_cliente(cliente)


@router.put("/{cliente_id}", dependencies=[Depends(requerir_rol("admin", "ventas"))])
def actualizar_cliente(cliente_id: str, cliente: ClienteUpdate):
    """
    Actualiza parcialmente un cliente existente.

    Método: PUT /clientes/{cliente_id}
    Body: solo los campos que se desean modificar
    """
    oid = validar_object_id(cliente_id)

    datos_actualizar = {
        k: v for k, v in cliente.model_dump(exclude_none=True).items()
    }

    if not datos_actualizar:
        raise HTTPException(
            status_code=400,
            detail="No se enviaron datos para actualizar"
        )

    resultado = coleccion_clientes.update_one(
        {"_id": oid},
        {"$set": datos_actualizar}
    )

    if resultado.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente con ID '{cliente_id}' no encontrado"
        )

    cliente_actualizado = coleccion_clientes.find_one({"_id": oid})
    return {
        "mensaje": "Cliente actualizado correctamente",
        "cliente": serializar_cliente(cliente_actualizado)
    }


@router.delete("/{cliente_id}", dependencies=[Depends(requerir_rol("admin"))])
def eliminar_cliente(cliente_id: str):
    """
    Elimina un cliente de la base de datos.

    Método: DELETE /clientes/{cliente_id}
    Lanza: 404 si no existe, 400 si el ID es inválido
    """
    oid = validar_object_id(cliente_id)
    resultado = coleccion_clientes.delete_one({"_id": oid})

    if resultado.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente con ID '{cliente_id}' no encontrado"
        )

    return {"mensaje": f"Cliente '{cliente_id}' eliminado correctamente"}