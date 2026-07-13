/*
 * productos.js — Lógica CRUD para la pantalla de Productos
 *
 * Maneja: listar, crear, editar y eliminar productos
 */
// Verificar sesión al cargar — redirige al login si no hay token
document.addEventListener("DOMContentLoaded", () => {
  cargarProductos(); // el catálogo es público — no forzar sesión
  aplicarPermisosUI();
});

// Variable global para saber si estamos editando o creando
let modoEdicion = false;

/**
 * Carga y muestra todos los productos en la tabla al iniciar la página.
 */
async function cargarProductos() {
  const tbody = document.getElementById("tabla-body");

  try {
    // Llamada GET a la API
    const productos = await apiGet("/productos/");

    // Si no hay productos, mostrar mensaje
    if (productos.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted py-4">
            <i class="bi bi-inbox fs-3 d-block mb-2"></i>
            No hay productos registrados
          </td>
        </tr>`;
      return;
    }

    // Generar una fila HTML por cada producto
    tbody.innerHTML = productos.map(p => `
      <tr>
        <td class="fw-semibold">${p.nombre}</td>
        <td><span class="badge bg-secondary">${p.categoria}</span></td>
        <td>$${Number(p.precio).toLocaleString("es-CL")}</td>
        <td>
          <span class="badge ${p.stock > 0 ? "bg-success" : "bg-danger"}">
            ${p.stock} uds.
          </span>
        </td>
        <td>
          <span class="badge ${p.activo ? "bg-success" : "bg-secondary"}">
            ${p.activo ? "Activo" : "Inactivo"}
          </span>
        </td>
        <td class="text-center">
          ${puedeGestionarProductos() ? `
          <button class="btn btn-outline-primary btn-accion me-1" onclick='prepararEdicion(${JSON.stringify(p)})' title="Editar">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-outline-danger btn-accion" onclick="eliminarProducto('${p.id}', '${p.nombre}')" title="Eliminar">
            <i class="bi bi-trash"></i>
          </button>
          ` : `<span class="text-muted small">—</span>`}
        </td>
      </tr>
    `).join("");

  } catch {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-danger py-4">
          <i class="bi bi-wifi-off fs-3 d-block mb-2"></i>
          No se pudo conectar con la API. Verifica que el servidor esté corriendo.
        </td>
      </tr>`;
  }
}

/**
 * Prepara el modal para CREAR un nuevo producto.
 * Limpia todos los campos del formulario.
 */
function prepararFormulario() {
  modoEdicion = false;
  document.getElementById("modal-titulo").innerHTML =
    '<i class="bi bi-plus-circle me-2"></i>Nuevo Producto';
  document.getElementById("producto-id").value          = "";
  document.getElementById("producto-nombre").value      = "";
  document.getElementById("producto-descripcion").value = "";
  document.getElementById("producto-precio").value      = "";
  document.getElementById("producto-stock").value       = "";
  document.getElementById("producto-categoria").value   = "";
  document.getElementById("producto-activo").checked    = true;
}

/**
 * Prepara el modal para EDITAR un producto existente.
 * Rellena el formulario con los datos actuales del producto.
 *
 * @param {object} producto - Objeto producto con todos sus campos
 */
function prepararEdicion(producto) {
  modoEdicion = true;
  document.getElementById("modal-titulo").innerHTML =
    '<i class="bi bi-pencil me-2"></i>Editar Producto';

  // Rellenar cada campo con los datos del producto seleccionado
  document.getElementById("producto-id").value          = producto.id;
  document.getElementById("producto-nombre").value      = producto.nombre;
  document.getElementById("producto-descripcion").value = producto.descripcion || "";
  document.getElementById("producto-precio").value      = producto.precio;
  document.getElementById("producto-stock").value       = producto.stock;
  document.getElementById("producto-categoria").value   = producto.categoria;
  document.getElementById("producto-activo").checked    = producto.activo;

  // Abrir el modal programáticamente
  new bootstrap.Modal(document.getElementById("modalProducto")).show();
}

/**
 * Guarda el producto: crea uno nuevo (POST) o actualiza uno existente (PUT).
 * Valida los campos obligatorios antes de enviar.
 */
async function guardarProducto() {
  // Leer valores del formulario
  const nombre      = document.getElementById("producto-nombre").value.trim();
  const descripcion = document.getElementById("producto-descripcion").value.trim();
  const precio      = parseFloat(document.getElementById("producto-precio").value);
  const stock       = parseInt(document.getElementById("producto-stock").value);
  const categoria   = document.getElementById("producto-categoria").value;
  const activo      = document.getElementById("producto-activo").checked;
  const id          = document.getElementById("producto-id").value;

  // Validación del lado del cliente
  if (!nombre || !categoria || isNaN(precio) || isNaN(stock)) {
    mostrarAlerta("Por favor completa todos los campos obligatorios.", "warning");
    return;
  }

  if (precio <= 0) {
    mostrarAlerta("El precio debe ser mayor a 0.", "warning");
    return;
  }

  // Construir el objeto a enviar
  const datos = { nombre, descripcion, precio, stock, categoria, activo };

  try {
    if (modoEdicion) {
      // PUT — actualizar producto existente
      await apiPut(`/productos/${id}`, datos);
      mostrarAlerta("Producto actualizado correctamente.", "success");
    } else {
      // POST — crear nuevo producto
      await apiPost("/productos/", datos);
      mostrarAlerta("Producto creado correctamente.", "success");
    }

    // Cerrar modal y recargar la tabla
    bootstrap.Modal.getInstance(document.getElementById("modalProducto")).hide();
    cargarProductos();

  } catch {
    // El error ya fue mostrado por api.js
  }
}

/**
 * Elimina un producto después de confirmación del usuario.
 *
 * @param {string} id     - ID del producto a eliminar
 * @param {string} nombre - Nombre para mostrar en el mensaje de confirmación
 */
async function eliminarProducto(id, nombre) {
  // Pedir confirmación antes de borrar
  if (!confirm(`¿Estás seguro de eliminar el producto "${nombre}"?\nEsta acción no se puede deshacer.`)) {
    return;
  }

  try {
    await apiDelete(`/productos/${id}`);
    mostrarAlerta(`Producto "${nombre}" eliminado correctamente.`, "success");
    cargarProductos();
  } catch {
    // Error ya manejado por api.js
  }
}

// Cargar productos automáticamente cuando la página termina de cargar
document.addEventListener("DOMContentLoaded", cargarProductos);

