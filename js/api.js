/*
 * api.js — Módulo central de comunicación con la API REST ComercioTech
 * Versión 2.0 — Incluye manejo de token JWT para autenticación RBAC
 */

const API_URL = window.API_URL || "";

/**
 * Obtiene el token JWT almacenado en sessionStorage.
 * Retorna null si no hay sesión activa.
 */
function obtenerToken() {
  return sessionStorage.getItem("token");
}

/**
 * Obtiene el rol del usuario actual desde sessionStorage.
 */
function obtenerRol() {
  return sessionStorage.getItem("rol");
}

/**
 * Obtiene el nombre del usuario actual desde sessionStorage.
 */
function obtenerNombre() {
  return sessionStorage.getItem("nombre");
}

/**
 * Cierra la sesión eliminando los datos del sessionStorage
 * y redirige al login.
 */
function cerrarSesion() {
  sessionStorage.removeItem("token");
  sessionStorage.removeItem("rol");
  sessionStorage.removeItem("nombre");
  window.location.href = "/pages/login.html";
}

/**
 * Verifica si hay sesión activa.
 * Si no hay token, redirige al login.
 */
function verificarSesion() {
  if (!obtenerToken()) {
    window.location.href = "../pages/login.html";
    return false;
  }
  return true;
}

/**
 * Construye los headers con el token JWT si existe.
 */
function construirHeaders(conJson = true) {
  const headers = {};
  if (conJson) headers["Content-Type"] = "application/json";

  const token = obtenerToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  return headers;
}

/**
 * Muestra una alerta flotante en la esquina superior derecha.
 */
function mostrarAlerta(mensaje, tipo = "success") {
  const anterior = document.querySelector(".alerta-flotante");
  if (anterior) anterior.remove();

  const alerta = document.createElement("div");
  alerta.className = `alert alert-${tipo} alerta-flotante shadow`;
  alerta.innerHTML = `
    <i class="bi bi-${tipo === "success" ? "check-circle" : "exclamation-triangle"} me-2"></i>
    ${mensaje}
  `;
  document.body.appendChild(alerta);
  setTimeout(() => alerta.remove(), 3000);
}

/**
 * Maneja errores de autenticación — redirige al login si el token expiró.
 */
function manejarErrorAuth(status) {
  if (status === 401) {
    sessionStorage.clear();
    mostrarAlerta("Sesión expirada. Redirigiendo al login...", "warning");
    setTimeout(() => window.location.href = "../pages/login.html", 2000);
    return true;
  }
  return false;
}

/**
 * Realiza una petición GET a la API con token JWT.
 */
async function apiGet(endpoint) {
  try {
    const respuesta = await fetch(`${API_URL}${endpoint}`, {
      headers: construirHeaders(false)
    });

    if (manejarErrorAuth(respuesta.status)) return null;

    if (!respuesta.ok) {
      const error = await respuesta.json();
      throw new Error(error.detail || "Error al obtener datos");
    }

    return await respuesta.json();

  } catch (error) {
    mostrarAlerta(`Error: ${error.message}`, "danger");
    throw error;
  }
}

/**
 * Realiza una petición POST a la API con token JWT.
 */
async function apiPost(endpoint, datos) {
  try {
    const respuesta = await fetch(`${API_URL}${endpoint}`, {
      method:  "POST",
      headers: construirHeaders(true),
      body:    JSON.stringify(datos)
    });

    if (manejarErrorAuth(respuesta.status)) return null;

    if (!respuesta.ok) {
      const error = await respuesta.json();
      throw new Error(error.detail || "Error al crear el registro");
    }

    return await respuesta.json();

  } catch (error) {
    mostrarAlerta(`Error: ${error.message}`, "danger");
    throw error;
  }
}

/**
 * Realiza una petición PUT a la API con token JWT.
 */
async function apiPut(endpoint, datos) {
  try {
    const respuesta = await fetch(`${API_URL}${endpoint}`, {
      method:  "PUT",
      headers: construirHeaders(true),
      body:    JSON.stringify(datos)
    });

    if (manejarErrorAuth(respuesta.status)) return null;

    if (!respuesta.ok) {
      const error = await respuesta.json();
      throw new Error(error.detail || "Error al actualizar el registro");
    }

    return await respuesta.json();

  } catch (error) {
    mostrarAlerta(`Error: ${error.message}`, "danger");
    throw error;
  }
}

/**
 * Realiza una petición DELETE a la API con token JWT.
 */
async function apiDelete(endpoint) {
  try {
    const respuesta = await fetch(`${API_URL}${endpoint}`, {
      method:  "DELETE",
      headers: construirHeaders(false)
    });

    if (manejarErrorAuth(respuesta.status)) return null;

    if (!respuesta.ok) {
      const error = await respuesta.json();
      throw new Error(error.detail || "Error al eliminar el registro");
    }

    return await respuesta.json();

  } catch (error) {
    mostrarAlerta(`Error: ${error.message}`, "danger");
    throw error;
  }
}

/**
 * Ajusta la navbar visible según el rol del usuario autenticado.
 * Debe llamarse en el DOMContentLoaded de cada página.
 */
function aplicarNavbarPorRol() {
  const rol = obtenerRol(); // null = visitante (sin sesión)

  const liClientes = document.querySelector('.navbar-nav [data-nav="clientes"]');
  if (liClientes) {
    liClientes.style.display = (rol === "admin" || rol === "ventas") ? "" : "none";
  }

  const liPedidos = document.querySelector('[data-nav="pedidos"]');
  const linkPedidos = document.getElementById("link-pedidos");
  if (liPedidos && linkPedidos) {
    if (rol === "admin" || rol === "ventas") {
      liPedidos.style.display = "";
      linkPedidos.href = esRaizIndex() ? "pages/pedidos.html" : "pedidos.html";
      linkPedidos.innerHTML = '<i class="bi bi-cart me-1"></i>Pedidos';
    } else if (rol === "cliente") {
      liPedidos.style.display = "";
      linkPedidos.href = esRaizIndex() ? "pages/mis-pedidos.html" : "mis-pedidos.html";
      linkPedidos.innerHTML = '<i class="bi bi-cart me-1"></i>Mis Pedidos';
    } else {
      liPedidos.style.display = "none"; // visitante
    }
  }

  // Tarjetas del home (index.html) — mismo criterio que el navbar
  const cardClientes = document.querySelector('div[data-nav="clientes"]');
  if (cardClientes) {
    cardClientes.style.display = (rol === "admin" || rol === "ventas") ? "" : "none";
  }

  const cardPedidosLink = document.getElementById("card-pedidos-link");
  const cardPedidosTitulo = document.getElementById("card-pedidos-titulo");
  const cardPedidosTexto = document.getElementById("card-pedidos-texto");
  if (cardPedidosLink) {
    if (rol === "cliente") {
      cardPedidosLink.href = "pages/mis-pedidos.html";
      cardPedidosLink.innerHTML = '<i class="bi bi-arrow-right-circle me-1"></i>Ir a Mis Pedidos';
      if (cardPedidosTitulo) cardPedidosTitulo.textContent = "Mis Pedidos";
      if (cardPedidosTexto) cardPedidosTexto.textContent = "Consulta el estado de tus pedidos y crea uno nuevo.";
    } else if (rol !== "admin" && rol !== "ventas") {
      cardPedidosLink.closest(".col-md-4").style.display = "none";
    }
  }
}

/** Detecta si el script corre desde index.html (raíz) o desde una página dentro de /pages */
function esRaizIndex() {
  return !window.location.pathname.includes("/pages/");
}

/**
 * Determina si el usuario actual puede gestionar productos.
 */
function puedeGestionarProductos() {
  const rol = obtenerRol();
  return rol === "admin" || rol === "ventas";
}

/**
 * Aplica los permisos de UI para la vista de productos.
 */
function aplicarPermisosUI() {
  aplicarNavbarPorRol();

  const btnNuevo = document.querySelector('[data-bs-target="#modalProducto"]');
  if (btnNuevo) {
    btnNuevo.style.display = puedeGestionarProductos() ? "" : "none";
  }
}