/*
 * pedidos.js — Lógica CRUD para la pantalla de Pedidos
 */
// Verificar sesión al cargar — redirige al login si no hay token
// Solo admin/ventas gestionan el listado completo de pedidos
document.addEventListener("DOMContentLoaded", () => {
  if (!verificarSesion()) return;
  const rolesPermitidos = ["admin", "ventas"];
  if (!rolesPermitidos.includes(obtenerRol())) {
    window.location.href = "../index.html";
    return;
  }
  aplicarNavbarPorRol();
  cargarPedidos(); // bug corregido: llamaba a cargarClientes() por error
});

let modoEdicion    = false;
let productosCache = [];  // Cache de productos para el selector de items
let contadorItems  = 0;   // Contador para IDs únicos de cada fila de item

/**
 * Carga y muestra todos los pedidos en la tabla.
 */
async function cargarPedidos() {
  const tbody = document.getElementById("tabla-body");

  try {
    const pedidos = await apiGet("/pedidos/");

    if (pedidos.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center text-muted py-4">
            <i class="bi bi-inbox fs-3 d-block mb-2"></i>
            No hay pedidos registrados
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = pedidos.map(p => `
      <tr>
        <td><small class="text-muted font-monospace">${p.id.slice(-8)}</small></td>
        <td>${p.cliente_id.slice(-8)}</td>
        <td>${new Date(p.fecha_pedido).toLocaleDateString("es-CL")}</td>
        <td><span class="badge bg-secondary">${p.items.length} item(s)</span></td>
        <td class="fw-semibold">$${Number(p.total).toLocaleString("es-CL")}</td>
        <td>
          <span class="badge badge-${p.estado}">
            ${p.estado.charAt(0).toUpperCase() + p.estado.slice(1)}
          </span>
        </td>
        <td class="text-center">
          <button
            class="btn btn-outline-warning btn-accion me-1"
            onclick='prepararEdicion(${JSON.stringify(p)})'
            title="Cambiar estado"
          >
            <i class="bi bi-pencil"></i>
          </button>
          <button
            class="btn btn-outline-danger btn-accion"
            onclick="eliminarPedido('${p.id}')"
            title="Eliminar"
          >
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `).join("");

  } catch {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-danger py-4">
          <i class="bi bi-wifi-off fs-3 d-block mb-2"></i>
          No se pudo conectar con la API.
        </td>
      </tr>`;
  }
}

/**
 * Prepara el modal para crear un nuevo pedido.
 * Carga los selectores de clientes y productos.
 */
async function prepararFormulario() {
  modoEdicion   = false;
  contadorItems = 0;

  document.getElementById("modal-titulo").innerHTML =
    '<i class="bi bi-cart-plus me-2"></i>Nuevo Pedido';
  document.getElementById("pedido-id").value     = "";
  document.getElementById("pedido-notas").value  = "";
  document.getElementById("items-container").innerHTML = "";
  document.getElementById("total-pedido").textContent = "$0";
  document.getElementById("seccion-estado").style.display = "none";

  // Cargar clientes en el selector
  await cargarSelectorClientes();

  // Cargar productos en cache
  productosCache = await apiGet("/productos/");

  // Agregar primer item vacío
  agregarItem();
}

/**
 * Carga los clientes activos en el select del modal.
 */
async function cargarSelectorClientes() {
  const select = document.getElementById("pedido-cliente");
  select.innerHTML = '<option value="">Selecciona un cliente</option>';

  try {
    const clientes = await apiGet("/clientes/");
    clientes
      .filter(c => c.activo)
      .forEach(c => {
        select.innerHTML += `<option value="${c.id}">${c.nombre} — ${c.email}</option>`;
      });
  } catch {
    select.innerHTML = '<option value="">Error al cargar clientes</option>';
  }
}

/**
 * Agrega una fila de item al formulario del pedido.
 */
function agregarItem() {
  const container = document.getElementById("items-container");
  const idx       = contadorItems++;

  // Construir opciones del selector de productos
  const opcionesProductos = productosCache
    .filter(p => p.activo && p.stock > 0)
    .map(p => `<option value="${p.id}" data-precio="${p.precio}">${p.nombre} — $${Number(p.precio).toLocaleString("es-CL")}</option>`)
    .join("");

  // Crear fila del item
  const fila = document.createElement("div");
  fila.className = "row g-2 mb-2 align-items-end";
  fila.id        = `item-${idx}`;
  fila.innerHTML = `
    <div class="col-md-6">
      <label class="form-label form-label-sm">Producto</label>
      <select class="form-select form-select-sm" id="item-producto-${idx}"
        onchange="actualizarTotal()">
        <option value="">Selecciona un producto</option>
        ${opcionesProductos}
      </select>
    </div>
    <div class="col-md-3">
      <label class="form-label form-label-sm">Cantidad</label>
      <input type="number" class="form-control form-control-sm"
        id="item-cantidad-${idx}" value="1" min="1"
        onchange="actualizarTotal()" />
    </div>
    <div class="col-md-2">
      <label class="form-label form-label-sm">Subtotal</label>
      <input type="text" class="form-control form-control-sm bg-light"
        id="item-subtotal-${idx}" readonly placeholder="$0" />
    </div>
    <div class="col-md-1">
      <button type="button" class="btn btn-outline-danger btn-sm w-100"
        onclick="eliminarItem('item-${idx}')">
        <i class="bi bi-x"></i>
      </button>
    </div>
  `;

  container.appendChild(fila);
}

/**
 * Elimina una fila de item del formulario.
 * @param {string} itemId - ID del elemento a eliminar
 */
function eliminarItem(itemId) {
  const elemento = document.getElementById(itemId);
  if (elemento) {
    elemento.remove();
    actualizarTotal();
  }
}

/**
 * Recalcula el total del pedido sumando precio × cantidad de cada item.
 */
function actualizarTotal() {
  let total = 0;

  // Recorrer todos los items del contenedor
  document.querySelectorAll("[id^='item-producto-']").forEach(select => {
    const idx      = select.id.split("-")[2];
    const cantidad = parseInt(document.getElementById(`item-cantidad-${idx}`)?.value) || 0;
    const precio   = parseFloat(select.selectedOptions[0]?.dataset.precio) || 0;
    const subtotal = precio * cantidad;

    // Actualizar subtotal de la fila
    const subtotalEl = document.getElementById(`item-subtotal-${idx}`);
    if (subtotalEl) subtotalEl.value = `$${subtotal.toLocaleString("es-CL")}`;

    total += subtotal;
  });

  document.getElementById("total-pedido").textContent =
    `$${total.toLocaleString("es-CL")}`;
}

/**
 * Prepara el modal para editar el estado de un pedido existente.
 * @param {object} pedido - Datos del pedido seleccionado
 */
function prepararEdicion(pedido) {
  modoEdicion = true;
  document.getElementById("modal-titulo").innerHTML =
    '<i class="bi bi-pencil me-2"></i>Actualizar Estado';

  document.getElementById("pedido-id").value    = pedido.id;
  document.getElementById("pedido-notas").value = pedido.notas || "";

  // Mostrar selector de estado solo en edición
  document.getElementById("seccion-estado").style.display = "block";
  document.getElementById("pedido-estado").value = pedido.estado;

  // Ocultar selector de cliente e items en edición
  document.getElementById("pedido-cliente").closest(".mb-3").style.display = "none";
  document.getElementById("items-container").innerHTML = `
    <div class="alert alert-info">
      <i class="bi bi-info-circle me-2"></i>
      Pedido con ${pedido.items.length} item(s) — Total: $${Number(pedido.total).toLocaleString("es-CL")}
    </div>`;

  new bootstrap.Modal(document.getElementById("modalPedido")).show();
}

/**
 * Guarda el pedido: POST si es nuevo, PUT si es actualización de estado.
 */
async function guardarPedido() {
  const id = document.getElementById("pedido-id").value;

  try {
    if (modoEdicion) {
      // Solo actualizar estado y notas
      const estado = document.getElementById("pedido-estado").value;
      const notas  = document.getElementById("pedido-notas").value.trim();

      await apiPut(`/pedidos/${id}`, { estado, notas });
      mostrarAlerta("Estado del pedido actualizado correctamente.", "success");

    } else {
      // Crear nuevo pedido
      const clienteId = document.getElementById("pedido-cliente").value;
      const notas     = document.getElementById("pedido-notas").value.trim();

      if (!clienteId) {
        mostrarAlerta("Selecciona un cliente para el pedido.", "warning");
        return;
      }

      // Recopilar items del formulario
      const items = [];
      document.querySelectorAll("[id^='item-producto-']").forEach(select => {
        const idx        = select.id.split("-")[2];
        const productoId = select.value;
        const cantidad   = parseInt(document.getElementById(`item-cantidad-${idx}`)?.value) || 0;
        const precio     = parseFloat(select.selectedOptions[0]?.dataset.precio) || 0;

        if (productoId && cantidad > 0) {
          items.push({
            producto_id:     productoId,
            cantidad:        cantidad,
            precio_unitario: precio
          });
        }
      });

      if (items.length === 0) {
        mostrarAlerta("Agrega al menos un producto al pedido.", "warning");
        return;
      }

      await apiPost("/pedidos/", { cliente_id: clienteId, items, notas });
      mostrarAlerta("Pedido creado correctamente.", "success");
    }

    bootstrap.Modal.getInstance(document.getElementById("modalPedido")).hide();
    cargarPedidos();

  } catch {
    // Error manejado por api.js
  }
}

/**
 * Elimina un pedido después de confirmación.
 * @param {string} id - ID del pedido a eliminar
 */
async function eliminarPedido(id) {
  if (!confirm(`¿Eliminar este pedido?\nEsta acción no se puede deshacer.`)) return;

  try {
    await apiDelete(`/pedidos/${id}`);
    mostrarAlerta("Pedido eliminado correctamente.", "success");
    cargarPedidos();
  } catch {
    // Error manejado por api.js
  }
}

