# Hotel Kawari

Sistema de reservas del hotel: sitio público, área del huésped y panel del personal (administración y recepción).

| Capa | Tecnología |
|---|---|
| API | Python 3.12 · FastAPI · PyMongo Async · Pydantic v2 · PyJWT · Argon2 (pwdlib) |
| Base de datos | MongoDB (Atlas en producción) |
| Frontend | Vue 3 · Vite · Pinia · Bootstrap 5 |
| Dependencias | `uv` (Python, `pyproject.toml` + `uv.lock`) · `npm` (frontend) |

- Arquitectura y backlog: [CLAUDE.md](CLAUDE.md)
- Contrato de la API: [docs/API_V1.md](docs/API_V1.md)
- Nivel de acceso por endpoint: [docs/ENDPOINTS_ACCESO.md](docs/ENDPOINTS_ACCESO.md)

## Arranque rápido (desarrollo)

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/) (`pip install uv`), Node 20.19+ y MongoDB (local o Atlas).

```sh
# 1. Backend
cp backend/.env.example backend/.env        # completa MONGO_URI y SECRET_KEY
uv sync                                     # crea .venv con dependencias exactas (uv.lock)
uv run python -m backend.scripts.seed --demo-rooms   # índices, ajustes, tipos de habitación y admin
uv run uvicorn backend.app.main:app --reload         # http://127.0.0.1:8000/docs

# 2. Frontend (otra terminal)
cd frontend
npm install
npm run dev                                 # http://localhost:5173 (proxy de /api y /static al backend)
```

El seed crea el administrador definido en `SEED_ADMIN_EMAIL`; si no defines `SEED_ADMIN_PASSWORD`,
imprime una contraseña aleatoria una sola vez.

En desarrollo los correos (verificación, recuperación de contraseña) se muestran en el log del backend
(`EMAIL_BACKEND=console`). Para enviarlos de verdad configura `EMAIL_BACKEND=smtp` y las variables `SMTP_*`.

## Pruebas

```sh
uv run pytest                 # backend: levanta un mongod temporal (o usa MONGO_TEST_URI)
uv run pytest --cov=backend/app
```

Las pruebas del backend usan un MongoDB real: buscan `mongod` en el PATH, en `MONGOD_PATH` o en
`C:\Program Files\MongoDB\Server\*\bin`. También puedes apuntar a un servidor existente con `MONGO_TEST_URI`.

## Estructura

```
backend/app/
├── core/        settings, seguridad, errores de dominio, permisos (RBAC), fechas
├── db/          cliente PyMongo Async, índices y validación $jsonSchema
├── api/v1/      routers HTTP (solo transporte)
├── modules/     auth, users, rooms, bookings, folios, cms, media, notifications, dashboard, audit
└── workers/     tareas programadas (vencimiento de pagos)
backend/scripts/ seed idempotente
backend/tests/   pruebas contra MongoDB real
frontend/src/
├── api/         una función por endpoint (única puerta al backend)
├── config/      variables de entorno y assetUrl()
├── stores/      auth (sesión en memoria + cookie HttpOnly), config del sitio, reserva
└── views/       público, auth, área del cliente, panel del personal
```

## Flujo de pago

No hay pasarela de pago: el huésped transfiere el anticipo (datos en *Configuración → Instrucciones de pago*),
sube el comprobante al reservar y el personal lo verifica en *Reservas → Por verificar*.
