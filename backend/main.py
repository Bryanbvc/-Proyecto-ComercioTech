from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.productos import router as router_productos
from app.routers.clientes  import router as router_clientes
from app.routers.pedidos   import router as router_pedidos
# ── NUEVO ──────────────────────────────────────────────
from app.routers.auth      import router as router_auth
from app.routers.usuarios  import router as router_usuarios
# ───────────────────────────────────────────────────────

app = FastAPI(
    title="API REST — ComercioTech",
    description="API para gestión de clientes, productos y pedidos usando FastAPI y MongoDB",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router_productos)
app.include_router(router_clientes)
app.include_router(router_pedidos)
# ── NUEVO ──────────────────────────────────────────────
app.include_router(router_auth)
app.include_router(router_usuarios)
# ───────────────────────────────────────────────────────

@app.get("/", tags=["Inicio"])
def inicio():
    return {
        "mensaje":     "API ComercioTech v2.0 — RBAC implementado",
        "version":     "2.0.0",
        "docs":        "/docs",
        "colecciones": ["clientes", "productos", "pedidos", "usuarios"]
    }