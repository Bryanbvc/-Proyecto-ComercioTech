/*
 * mis-pedidos.js — Autoservicio de pedidos para el rol "cliente"
 * Reutiliza los mismos endpoints /pedidos/ y /productos/, que ya
 * filtran/asocian automáticamente por el usuario autenticado.
 */
document.addEventListener("DOMContentLoaded", cargarMisPedidos);

let productosCache = [];
let contadorItems = 0;

async function cargarMisPedidos() {
  const tbody = document.getElementById("tabla-body");
  try {
    const pedidos = await apiGet("/pedidos/");

    if (pedidos.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="6" class="text-center text-muted py-4">
          <i class="bi bi-inbox fs-3 d-block mb-2"></i>Aún no tienes pedidos
        </td></tr>`;
      return;
    }

    tbody.innerHTML = pedidos.map(p => `
      <tr>
        <td><small class="text-muted font-monospace">${p.id.slice(-8)}</small></td>
        <td>${new Date(p.fecha_pedido).toLocaleDateString("es-CL")}</td>
        <td><span class="badge bg-secondary">${p.items.length} item(s)</span></td>
        <td class="fw-semibold">$${Number(p.total).toLocaleString("es-CL")}</td>
        <td><span class="badge badge-${p.estado}">${p.estado.charAt(0).toUpperCase() + p.estado.slice(1)}</span></td>
        <td class="text-center">
          ${p.estado === "pendiente"
            ? `<button class="btn btn-outline-danger btn-accion" onclick="cancelarMiPedido('${p.id}')" title="Cancelar">
                 <i class="bi bi-x-circle"></i>
               </button>`
            : `<span class="text-muted small">—</span>`}
        </td>
      </tr>
    `).join("");

  } catch {
    tbody.innerHTML = `
      <tr><td colspan="6" class="text-center text-danger py-4">
        <i class="bi bi-wifi-off fs-3 d-block mb-2"></i>No se pudo conectar con la API.
      </td></tr>`;
  }
}

async function prepararFormulario() {
  contadorItems = 0;
  document.getElementById("items-container").innerHTML = "";
  document.getElementById("total-pedido").textContent = "$0";
  document.getElementById("pedido-notas").value = "";
  productosCache = await apiGet("/productos/");
  agregarItem();
}

function agregarItem() {
  const container = document.getElementById("items-container");
  const idx = contadorItems++;

  const opcionesProductos = productosCache
    .filter(p => p.activo && p.stock > 0)
    .map(p => `<option value="${p.id}" data-precio="${p.precio}">${p.nombre} — $${Number(p.precio).toLocaleString("es-CL")}</option>`)
    .join("");

  const fila = document.createElement("div");
  fila.className = "row g-2 mb-2 align-items-end";
  fila.id = `item-${idx}`;
  fila.innerHTML = `
    <div class="col-md-6">
      <label class="form-label form-label-sm">Producto</label>
      <select class="form-select form-select-sm" id="item-producto-${idx}" onchange="actualizarTotal()">
        <option value="">Selecciona un producto</option>
        ${opcionesProductos}
      </select>
    </div>
    <div class="col-md-3">
      <label class="form-label form-label-sm">Cantidad</label>
      <input type="number" class="form-control form-control-sm" id="item-cantidad-${idx}" value="1" min="1" onchange="actualizarTotal()" />
    </div>
    <div class="col-md-2">
      <label class="form-label form-label-sm">Subtotal</label>
      <input type="text" class="form-control form-control-sm bg-light" id="item-subtotal-${idx}" readonly placeholder="$0" />
    </div>
    <div class="col-md-1">
      <button type="button" class="btn btn-outline-danger btn-sm w-100" onclick="eliminarItem('item-${idx}')">
        <i class="bi bi-x"></i>
      </button>
    </div>
  `;
  container.appendChild(fila);
}

function eliminarItem(itemId) {
  const el = document.getElementById(itemId);
  if (el) { el.remove(); actualizarTotal(); }
}

function actualizarTotal() {
  let total = 0;
  document.querySelectorAll("[id^='item-producto-']").forEach(select => {
    const idx = select.id.split("-")[2];
    const cantidad = parseInt(document.getElementById(`item-cantidad-${idx}`)?.value) || 0;
    const precio = parseFloat(select.selectedOptions[0]?.dataset.precio) || 0;
    const subtotal = precio * cantidad;
    const subtotalEl = document.getElementById(`item-subtotal-${idx}`);
    if (subtotalEl) subtotalEl.value = `$${subtotal.toLocaleString("es-CL")}`;
    total += subtotal;
  });
  document.getElementById("total-pedido").textContent = `$${total.toLocaleString("es-CL")}`;
}

async function guardarPedido() {
  const notas = document.getElementById("pedido-notas").value.trim();
  const items = [];

  document.querySelectorAll("[id^='item-producto-']").forEach(select => {
    const idx = select.id.split("-")[2];
    const productoId = select.value;
    const cantidad = parseInt(document.getElementById(`item-cantidad-${idx}`)?.value) || 0;
    const precio = parseFloat(select.selectedOptions[0]?.dataset.precio) || 0;
    if (productoId && cantidad > 0) {
      items.push({ producto_id: productoId, cantidad, precio_unitario: precio });
    }
  });

  if (items.length === 0) {
    mostrarAlerta("Agrega al menos un producto al pedido.", "warning");
    return;
  }

  try {
    await apiPost("/pedidos/", { items, notas });
    mostrarAlerta("Pedido creado correctamente.", "success");
    bootstrap.Modal.getInstance(document.getElementById("modalPedido")).hide();
    cargarMisPedidos();
  } catch {
    // Error manejado por api.js
  }
}

async function cancelarMiPedido(id) {
  if (!confirm("¿Cancelar este pedido? Esta acción no se puede deshacer.")) return;
  try {
    await apiPut(`/pedidos/${id}/cancelar`, {});
    mostrarAlerta("Pedido cancelado correctamente.", "success");
    cargarMisPedidos();
  } catch {
    // Error manejado por api.js
  }
}
