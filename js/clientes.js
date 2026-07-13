/*
 * clientes.js — Lógica CRUD para la pantalla de Clientes
  * Versión 2.0 — Incluye manejo de token JWT para autenticación RBAC
 */
// Verificar sesión al cargar — redirige al login si no hay token
document.addEventListener("DOMContentLoaded", () => {
  if (!verificarSesion()) return;
  const rolesPermitidos = ["admin", "ventas"];
  if (!rolesPermitidos.includes(obtenerRol())) {
    window.location.href = "../index.html";
    return;
  }
  aplicarNavbarPorRol();
  cargarClientes();
});

let modoEdicion = false;

/**
 * Carga y muestra todos los clientes en la tabla.
 */
async function cargarClientes() {
  const tbody = document.getElementById("tabla-body");

  try {
    const clientes = await apiGet("/clientes/");

    if (clientes.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-muted py-4">
            <i class="bi bi-inbox fs-3 d-block mb-2"></i>
            No hay clientes registrados
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = clientes.map(c => `
      <tr>
        <td class="fw-semibold">${c.nombre}</td>
        <td>${c.email}</td>
        <td class="col-ocultar-movil">${c.telefono || "—"}</td>
        <td class="col-ocultar-movil">${c.direccion?.ciudad || "—"}</td>
        <td>
          <span class="badge ${c.activo ? "bg-success" : "bg-secondary"}">
            ${c.activo ? "Activo" : "Inactivo"}
          </span>
        </td>
        <td class="text-center">
          <button
            class="btn btn-outline-primary btn-accion me-1"
            onclick='prepararEdicion(${JSON.stringify(c)})'
            title="Editar"
          >
            <i class="bi bi-pencil"></i>
          </button>
          <button
            class="btn btn-outline-danger btn-accion"
            onclick="eliminarCliente('${c.id}', '${c.nombre}')"
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
        <td colspan="6" class="text-center text-danger py-4">
          <i class="bi bi-wifi-off fs-3 d-block mb-2"></i>
          No se pudo conectar con la API.
        </td>
      </tr>`;
  }
}

/**
 * Prepara el modal para crear un nuevo cliente.
 */
function prepararFormulario() {
  modoEdicion = false;
  document.getElementById("modal-titulo").innerHTML =
    '<i class="bi bi-person-plus me-2"></i>Nuevo Cliente';

  // Limpiar todos los campos
  ["cliente-id","cliente-nombre","cliente-email","cliente-telefono",
   "cliente-calle","cliente-cp","cliente-ciudad","cliente-region"].forEach(id => {
    document.getElementById(id).value = "";
  });
  document.getElementById("cliente-pais").value  = "Chile";
  document.getElementById("cliente-activo").checked = true;
}

/**
 * Prepara el modal para editar un cliente existente.
 * @param {object} cliente - Datos del cliente seleccionado
 */
function prepararEdicion(cliente) {
  modoEdicion = true;
  document.getElementById("modal-titulo").innerHTML =
    '<i class="bi bi-pencil me-2"></i>Editar Cliente';

  document.getElementById("cliente-id").value       = cliente.id;
  document.getElementById("cliente-nombre").value   = cliente.nombre;
  document.getElementById("cliente-email").value    = cliente.email;
  document.getElementById("cliente-telefono").value = cliente.telefono || "";
  document.getElementById("cliente-activo").checked = cliente.activo;

  // Rellenar dirección si existe
  const dir = cliente.direccion || {};
  document.getElementById("cliente-calle").value  = dir.calle  || "";
  document.getElementById("cliente-ciudad").value = dir.ciudad || "";
  document.getElementById("cliente-region").value = dir.region || "";
  document.getElementById("cliente-cp").value     = dir.codigo_postal || "";
  document.getElementById("cliente-pais").value   = dir.pais   || "Chile";

  new bootstrap.Modal(document.getElementById("modalCliente")).show();
}

/**
 * Guarda el cliente: POST si es nuevo, PUT si es edición.
 */
async function guardarCliente() {
  const nombre   = document.getElementById("cliente-nombre").value.trim();
  const email    = document.getElementById("cliente-email").value.trim();
  const telefono = document.getElementById("cliente-telefono").value.trim();
  const activo   = document.getElementById("cliente-activo").checked;
  const id       = document.getElementById("cliente-id").value;

  // Validación básica
  if (!nombre || !email) {
    mostrarAlerta("Nombre y email son obligatorios.", "warning");
    return;
  }

  // Validar formato de email
  const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!regexEmail.test(email)) {
    mostrarAlerta("El formato del email no es válido.", "warning");
    return;
  }

  // Construir subdocumento dirección
  const direccion = {
    calle:         document.getElementById("cliente-calle").value.trim(),
    ciudad:        document.getElementById("cliente-ciudad").value.trim(),
    region:        document.getElementById("cliente-region").value.trim(),
    codigo_postal: document.getElementById("cliente-cp").value.trim(),
    pais:          document.getElementById("cliente-pais").value.trim()
  };

  const datos = { nombre, email, telefono, activo, direccion };

  try {
    if (modoEdicion) {
      await apiPut(`/clientes/${id}`, datos);
      mostrarAlerta("Cliente actualizado correctamente.", "success");
    } else {
      await apiPost("/clientes/", datos);
      mostrarAlerta("Cliente creado correctamente.", "success");
    }

    bootstrap.Modal.getInstance(document.getElementById("modalCliente")).hide();
    cargarClientes();

  } catch {
    // Error manejado por api.js
  }
}

/**
 * Elimina un cliente después de confirmación.
 * @param {string} id     - ID del cliente
 * @param {string} nombre - Nombre para el mensaje de confirmación
 */
async function eliminarCliente(id, nombre) {
  if (!confirm(`¿Eliminar al cliente "${nombre}"?\nEsta acción no se puede deshacer.`)) return;

  try {
    await apiDelete(`/clientes/${id}`);
    mostrarAlerta(`Cliente "${nombre}" eliminado correctamente.`, "success");
    cargarClientes();
  } catch {
    // Error manejado por api.js
  }
}

// Cargar clientes al iniciar la página
document.addEventListener("DOMContentLoaded", cargarClientes);