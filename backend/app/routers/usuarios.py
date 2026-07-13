"""
usuarios.py — CRUD de usuarios (solo accesible por administradores)
"""

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime

from app.database.connection import coleccion_usuarios, coleccion_clientes
from app.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.config.security import hashear_password, requerir_rol

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

ROLES_VALIDOS = ["admin", "ventas", "cliente", "visitante"]


def serializar_usuario(u) -> dict:
    """Serializa un usuario — NUNCA incluye password_hash."""
    return {
        "id":             str(u["_id"]),
        "nombre":         u.get("nombre"),
        "email":          u.get("email"),
        "rol":            u.get("rol"),
        "activo":         u.get("activo"),
        "fecha_registro": u.get("fecha_registro")
    }


@router.get("/", dependencies=[Depends(requerir_rol("admin"))])
def listar_usuarios():
    """Lista todos los usuarios. Solo admin."""
    usuarios = coleccion_usuarios.find({}, {"password_hash": 0})
    return [serializar_usuario(u) for u in usuarios]


@router.post("/", status_code=201, dependencies=[Depends(requerir_rol("admin"))])
def crear_usuario(usuario: UsuarioCreate):
    """Crea un usuario con cualquier rol. Solo admin."""
    if usuario.rol not in ROLES_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Valores permitidos: {ROLES_VALIDOS}")

    if coleccion_usuarios.find_one({"email": usuario.email}):
        raise HTTPException(status_code=400, detail=f"El email '{usuario.email}' ya está registrado")

    nuevo = {
        "nombre":         usuario.nombre,
        "email":          usuario.email,
        "password_hash":  hashear_password(usuario.password),
        "rol":            usuario.rol,
        "activo":         usuario.activo,
        "fecha_registro": datetime.utcnow()
    }

    resultado = coleccion_usuarios.insert_one(nuevo)

    # Si el admin crea un usuario con rol cliente, generar también su ficha comercial
    if usuario.rol == "cliente" and not coleccion_clientes.find_one({"email": usuario.email}):
        coleccion_clientes.insert_one({
            "nombre": usuario.nombre, "email": usuario.email,
            "telefono": None, "activo": True, "direccion": None,
            "fecha_registro": datetime.utcnow()
        })

    creado    = coleccion_usuarios.find_one({"_id": resultado.inserted_id})
    return {"mensaje": "Usuario creado correctamente", "usuario": serializar_usuario(creado)}


@router.put("/{usuario_id}", dependencies=[Depends(requerir_rol("admin"))])
def actualizar_usuario(usuario_id: str, usuario: UsuarioUpdate):
    """Actualiza datos de un usuario. Solo admin."""
    if not ObjectId.is_valid(usuario_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    datos = {k: v for k, v in usuario.model_dump(exclude_none=True).items()}

    # Si se actualiza el password, hashearlo antes de guardar
    if "password" in datos:
        datos["password_hash"] = hashear_password(datos.pop("password"))

    if not datos:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    resultado = coleccion_usuarios.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": datos}
    )

    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    actualizado = coleccion_usuarios.find_one({"_id": ObjectId(usuario_id)})
    return {"mensaje": "Usuario actualizado", "usuario": serializar_usuario(actualizado)}


@router.delete("/{usuario_id}", dependencies=[Depends(requerir_rol("admin"))])
def eliminar_usuario(usuario_id: str):
    """Elimina un usuario. Solo admin."""
    if not ObjectId.is_valid(usuario_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    resultado = coleccion_usuarios.delete_one({"_id": ObjectId(usuario_id)})

    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"mensaje": "Usuario eliminado correctamente"}