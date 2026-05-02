import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Importaciones de tu aplicación
from backend.routers import admin, auth, earnings, register, users, bookings, rooms, config, gallery, invoices, dashboard, notifications, availability
from backend.services.task_service import cancelar_reservas_vencidas
from backend.core.config import UPLOAD_DIR
from backend.db.client import db

# 🟢 1. UNIFICAMOS EL LIFESPAN (Tareas automáticas + Índices BD)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # -- FASE DE INICIO (STARTUP) --
    print("Iniciando servicios del backend...")
    
    # A) Iniciar tareas en segundo plano
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cancelar_reservas_vencidas, 'interval', hours=24)
    scheduler.start()
    print("⏳ Motor de tareas automáticas iniciado.")

    # B) Crear índices de MongoDB
    print("Verificando y creando índices de la base de datos...")
    try:
        await db.bookings.create_index("habitacion_id")
        await db.bookings.create_index("cliente_id")
        await db.bookings.create_index("estado")
        await db.bookings.create_index([("fecha_entrada", -1)])
        print("✅ Índices listos y optimizados.")
    except Exception as e:
        print(f"❌ Error al crear índices: {e}")
    
    # -- AQUÍ FASTAPI SE QUEDA ESCUCHANDO PETICIONES --
    yield 
    
    # -- FASE DE APAGADO (SHUTDOWN) --
    print("Apagando el servidor. Conexiones cerradas.")
    scheduler.shutdown()
    print("🛑 Motor de tareas automáticas detenido.")


app = FastAPI(lifespan=lifespan)

# 🟢 2. PROTECCIÓN DE DIRECTORIOS ESTÁTICOS Y MONTAJE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = UPLOAD_DIR
IMAGES_DIR = os.path.join(STATIC_DIR, "images")

# Creamos las carpetas si no existen (evita que el servidor explote al arrancar)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Montamos las rutas para que el frontend las pueda ver
app.mount("/static/uploads", StaticFiles(directory=UPLOADS_DIR), name="static_uploads")
app.mount("/static/images", StaticFiles(directory=IMAGES_DIR), name="static_images")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 🟢 3. CONFIGURACIÓN CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)

# 🟢 4. REGISTRO DE RUTAS (ROUTERS)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(bookings.router)
app.include_router(register.router)
app.include_router(earnings.router)
app.include_router(rooms.router)
app.include_router(admin.router)
app.include_router(config.router)
app.include_router(gallery.router)
app.include_router(invoices.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(availability.router)