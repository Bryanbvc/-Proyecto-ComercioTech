"""
serializers.py — Funciones para convertir documentos MongoDB a diccionarios JSON

MongoDB usa ObjectId para los _id, que no es serializable a JSON directamente.
Estas funciones convierten cada documento a un diccionario compatible con JSON.
"""


def serializar_cliente(cliente) -> dict:
    """
    Convierte un documento de la colección clientes a diccionario JSON.

    Parámetros:
        cliente: documento MongoDB (tipo dict con ObjectId)

    Retorna:
        dict con todos los campos del cliente, con _id convertido a string
    """
    return {
        "id":             str(cliente["_id"]),
        "nombre":         cliente.get("nombre"),
        "email":          cliente.get("email"),
        "telefono":       cliente.get("telefono"),
        "activo":         cliente.get("activo"),
        "fecha_registro": cliente.get("fecha_registro"),
        # .get() retorna None si el campo no existe, evitando KeyError
        "direccion":      cliente.get("direccion")
    }


def serializar_clientes(clientes) -> list:
    """
    Convierte una lista de documentos clientes a lista de diccionarios.

    Parámetros:
        clientes: cursor de MongoDB con múltiples documentos

    Retorna:
        list de dicts serializados
    """
    return [serializar_cliente(c) for c in clientes]


def serializar_producto(producto) -> dict:
    """Convierte un documento de la colección productos a diccionario JSON."""
    return {
        "id":             str(producto["_id"]),
        "nombre":         producto.get("nombre"),
        "descripcion":    producto.get("descripcion"),
        "precio":         producto.get("precio"),
        "stock":          producto.get("stock"),
        "categoria":      producto.get("categoria"),
        "activo":         producto.get("activo"),
        "fecha_creacion": producto.get("fecha_creacion")
    }


def serializar_productos(productos) -> list:
    """Convierte una lista de documentos productos a lista de diccionarios."""
    return [serializar_producto(p) for p in productos]


def serializar_item(item) -> dict:
    """
    Convierte un ítem embebido dentro de un pedido.
    El producto_id también es ObjectId y necesita conversión.
    """
    return {
        "producto_id":     str(item.get("producto_id", "")),
        "nombre_producto": item.get("nombre_producto"),
        "cantidad":        item.get("cantidad"),
        "precio_unitario": item.get("precio_unitario")
    }


def serializar_pedido(pedido) -> dict:
    """Convierte un documento de la colección pedidos a diccionario JSON."""
    return {
        "id":              str(pedido["_id"]),
        "cliente_id":      str(pedido.get("cliente_id", "")),
        "fecha_pedido":    pedido.get("fecha_pedido"),
        "estado":          pedido.get("estado"),
        # Serializa cada ítem del arreglo embebido
        "items":           [serializar_item(i) for i in pedido.get("items", [])],
        "total":           pedido.get("total"),
        "direccion_envio": pedido.get("direccion_envio"),
        "notas":           pedido.get("notas")
    }


def serializar_pedidos(pedidos) -> list:
    """Convierte una lista de documentos pedidos a lista de diccionarios."""
    return [serializar_pedido(p) for p in pedidos]