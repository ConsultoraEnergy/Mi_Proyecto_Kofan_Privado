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

## Arranque rápido con Docker (un comando)

Requisitos: Docker con Compose v2.24+.

```sh
docker compose up --build                                       # http://localhost:8080
docker compose run --rm api python -m backend.scripts.seed --demo-rooms   # en otra terminal, la primera vez
```

Levanta MongoDB local (nunca Atlas), la API y el frontend servido por Nginx, que hace de proxy de `/api`
y `/static/uploads` (mismo origen, como exige la cookie de sesión). Los datos persisten en volúmenes;
`docker compose down -v` los borra.

## Arranque rápido (sin Docker)

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
cd frontend && npm test       # frontend: Vitest
```

Las pruebas del backend usan un MongoDB real: buscan `mongod` en el PATH, en `MONGOD_PATH` o en
`C:\Program Files\MongoDB\Server\*\bin`. También puedes apuntar a un servidor existente con `MONGO_TEST_URI`.

## Calidad de código

| Capa | Herramientas | Comandos |
|---|---|---|
| Backend | Ruff (lint + formato), mypy | `uv run ruff check .` · `uv run ruff format .` · `uv run mypy` |
| Frontend | ESLint (plugin Vue), Prettier | `npm run lint` · `npm run format` (dentro de `frontend/`) |

Hooks de pre-commit (Ruff, mypy, ESLint, Prettier, bloqueo de `.env` y de archivos grandes):

```sh
uv run pre-commit install           # una vez por clon (requiere uv en el PATH y npm ci en frontend/)
uv run pre-commit run --all-files   # revisión completa manual
```

El CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) ejecuta lo mismo en cada push y PR, además de
las pruebas con cobertura mínima (70 % en `auth` y `bookings`, 85 % total), el build del frontend y la
construcción y arranque de las imágenes Docker.

## Observabilidad

- `GET /health`: liveness (el proceso responde). `GET /ready`: readiness (MongoDB responde; 503 si no).
- Cada respuesta lleva `X-Request-ID` (se respeta el entrante si es válido). El mismo id aparece en todos
  los logs de la petición y en las respuestas 500 (`request_id`), para cruzar un reporte del usuario con el log.
- Logs: texto legible en desarrollo y JSON de una línea en producción (`LOG_FORMAT`, `LOG_LEVEL`).
- Sentry: se activa al definir `SENTRY_DSN`. No envía datos personales (`send_default_pii=False`).

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
