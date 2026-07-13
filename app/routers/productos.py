"""
routers/productos.py — Endpoints CRUD para la colección productos

Define las rutas HTTP que permiten crear, leer, actualizar y eliminar productos.
Cada función maneja una operación específica sobre MongoDB.
"""
from app.config.security import requerir_rol, obtener_usuario_opcional
from fastapi import Depends
# HTTPException lanza errores HTTP con código y mensaje personalizados
from fastapi import APIRouter, HTTPException
from bson import ObjectId

# Importar las colecciones desde el módulo de conexión
from app.database.connection import coleccion_productos

# Importar los esquemas de validación Pydantic
from app.schemas.producto_schema import ProductoCreate, ProductoUpdate

# Importar los serializadores para convertir ObjectId a string
from app.models.serializers import serializar_producto, serializar_productos

# datetime para registrar la fecha de creación
from datetime import datetime

# ── Configuración del router ──────────────────────────────────────────────────
router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)

# ── HELPERS ───────────────────────────────────────────────────────────────────

def validar_object_id(id: str) -> ObjectId:
    """
    Valida que el string recibido sea un ObjectId válido de MongoDB.

    Parámetros:
        id: string que representa el ObjectId

    Retorna:
        ObjectId válido

    Lanza:
        HTTPException 400 si el ID no tiene el formato correcto
    """
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=400,
            detail=f"El ID '{id}' no es un ObjectId válido de MongoDB"
        )
    return ObjectId(id)


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@router.post("/", status_code=201, dependencies=[Depends(requerir_rol("admin", "ventas"))])
def crear_producto(producto: ProductoCreate):
    """
    Crea un nuevo producto en la base de datos.

    Método: POST
    URL: /productos/
    Body: JSON con nombre, precio, stock, categoria (descripcion y activo opcionales)

    Retorna: documento del producto creado con su ID asignado por MongoDB
    """
    # Convertir el esquema Pydantic a diccionario Python
    nuevo_producto = producto.model_dump()

    # Agregar la fecha de creación automáticamente
    nuevo_producto["fecha_creacion"] = datetime.utcnow()

    # Insertar en MongoDB — retorna un objeto con el _id generado
    resultado = coleccion_productos.insert_one(nuevo_producto)

    # Recuperar el documento completo recién insertado para devolverlo
    producto_creado = coleccion_productos.find_one({"_id": resultado.inserted_id})

    return {
        "mensaje": "Producto creado correctamente",
        "producto": serializar_producto(producto_creado)
    }


@router.get("/")
def listar_productos():
    """
    Retorna todos los productos de la base de datos.

    Método: GET
    URL: /productos/

    Retorna: lista de todos los productos
    """
    # find() sin filtros retorna todos los documentos de la colección
    productos = coleccion_productos.find()
    return serializar_productos(productos)


@router.get("/{producto_id}")
def obtener_producto(producto_id: str):
    """
    Retorna un producto específico por su ID.

    Método: GET
    URL: /productos/{producto_id}

    Parámetros:
        producto_id: ID del producto en formato ObjectId string

    Retorna: documento del producto encontrado
    Lanza: 404 si el producto no existe, 400 si el ID es inválido
    """
    # Validar que el ID tenga formato correcto antes de consultar
    oid = validar_object_id(producto_id)

    producto = coleccion_productos.find_one({"_id": oid})

    if not producto:
        raise HTTPException(
            status_code=404,
            detail=f"Producto con ID '{producto_id}' no encontrado"
        )

    return serializar_producto(producto)


@router.put("/{producto_id}", dependencies=[Depends(requerir_rol("admin", "ventas"))])
def actualizar_producto(producto_id: str, producto: ProductoUpdate):
    """
    Actualiza parcialmente un producto existente.

    Método: PUT
    URL: /productos/{producto_id}
    Body: JSON con los campos a actualizar (solo los que cambien)

    Parámetros:
        producto_id: ID del producto a actualizar

    Retorna: documento del producto actualizado
    Lanza: 400 si el ID es inválido o no hay datos, 404 si no existe
    """
    oid = validar_object_id(producto_id)

    # Filtrar solo los campos que fueron enviados (excluir los None)
    # exclude_none=True evita sobreescribir campos con None
    datos_actualizar = {
        k: v for k, v in producto.model_dump(exclude_none=True).items()
    }

    # Verificar que se envió al menos un campo para actualizar
    if not datos_actualizar:
        raise HTTPException(
            status_code=400,
            detail="No se enviaron datos para actualizar"
        )

    # $set actualiza solo los campos indicados, sin tocar los demás
    resultado = coleccion_productos.update_one(
        {"_id": oid},
        {"$set": datos_actualizar}
    )

    # matched_count=0 significa que no encontró el documento
    if resultado.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Producto con ID '{producto_id}' no encontrado"
        )

    # Retornar el documento actualizado
    producto_actualizado = coleccion_productos.find_one({"_id": oid})
    return {
        "mensaje": "Producto actualizado correctamente",
        "producto": serializar_producto(producto_actualizado)
    }


@router.delete("/{producto_id}", dependencies=[Depends(requerir_rol("admin"))])
def eliminar_producto(producto_id: str):
    """
    Elimina un producto de la base de datos.

    Método: DELETE
    URL: /productos/{producto_id}

    Parámetros:
        producto_id: ID del producto a eliminar

    Retorna: mensaje de confirmación
    Lanza: 404 si el producto no existe, 400 si el ID es inválido
    """
    oid = validar_object_id(producto_id)

    resultado = coleccion_productos.delete_one({"_id": oid})

    # deleted_count=0 significa que no encontró el documento
    if resultado.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Producto con ID '{producto_id}' no encontrado"
        )

    return {"mensaje": f"Producto '{producto_id}' eliminado correctamente"}