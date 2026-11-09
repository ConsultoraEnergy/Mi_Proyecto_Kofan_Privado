# Análisis de Arquitectura — Base Ecohotel Kofán → Hotel Kawari

> **Fecha:** 2026-11-09
> **Alcance:** revisión completa del repositorio actual (backend FastAPI, frontend Vue 3, pruebas, configuración y repositorio git) como punto de partida para **Hotel Kawari**.
> **Rol:** Arquitecto de Software Senior / Full-Stack.

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Stack tecnológico identificado](#2-stack-tecnológico-identificado)
3. [Arquitectura actual](#3-arquitectura-actual)
4. [Reglas y convenciones identificadas](#4-reglas-y-convenciones-identificadas)
5. [Hallazgos — Seguridad](#5-hallazgos--seguridad)
6. [Hallazgos — Lógica de negocio e integridad de datos](#6-hallazgos--lógica-de-negocio-e-integridad-de-datos)
7. [Hallazgos — Arquitectura y diseño](#7-hallazgos--arquitectura-y-diseño)
8. [Hallazgos — Escalabilidad y rendimiento](#8-hallazgos--escalabilidad-y-rendimiento)
9. [Hallazgos — Frontend](#9-hallazgos--frontend)
10. [Hallazgos — Calidad, DevOps y repositorio](#10-hallazgos--calidad-devops-y-repositorio)
11. [Riesgos legales / normativos (Colombia)](#11-riesgos-legales--normativos-colombia)
12. [Arquitectura objetivo propuesta para Hotel Kawari](#12-arquitectura-objetivo-propuesta-para-hotel-kawari)
13. [Lista de tareas (backlog priorizado)](#13-lista-de-tareas-backlog-priorizado)

---

## 1. Resumen ejecutivo

El proyecto Kofán es un sistema funcional de reservas hoteleras (sitio público + panel de cliente + panel administrativo) con una separación por capas razonable en el backend (`routers → services → db`) y un frontend Vue 3 moderno con rutas *lazy* y Pinia.

Sin embargo, **no está listo para usarse como base de producción tal como está**. Se identificaron:

| Severidad | Cantidad | Ejemplos clave |
|---|---|---|
| 🔴 Crítica | 8 | Facturas sin autenticación, cualquier cliente puede crear habitaciones, el precio de la reserva lo define el cliente, *refresh token* aceptado como *access token*, reservas ajenas "robables" al registrarse, comprobantes de pago públicos |
| 🟠 Alta | 10 | Doble reserva por condición de carrera, bot que cancela reservas pendientes legítimas, usuarios suspendidos siguen con acceso, `$lookup` a colección inexistente (`clients`), subida de archivos con extensión arbitraria |
| 🟡 Media | 15+ | URLs `localhost` *hardcodeadas*, zona horaria manual (-5h), scheduler en proceso, `print()` en vez de logging, componentes de 600-800 líneas |
| 🟢 Baja | varias | Código muerto, dependencias basura, comentarios duplicados, mezcla español/inglés |

**Recomendación principal:** mantener el stack (FastAPI + Vue 3 + MongoDB) porque el equipo ya lo domina, pero **antes de construir funcionalidades de Kawari** ejecutar la *Fase 0 (seguridad)* y la *Fase 1 (fundaciones)* del backlog de la sección 13. Además, aprovechar el arranque para convertir la base en una **plantilla parametrizable** (nombre del hotel, BD, marca, colores) en lugar de copiar y reemplazar "Kofán" a mano.

---

## 2. Stack tecnológico identificado

### Backend
| Componente | Tecnología | Versión | Observación |
|---|---|---|---|
| Lenguaje | Python | 3.12 | OK |
| Framework API | FastAPI | 0.129.0 (backend) / 0.135.3 (raíz) | ⚠️ Dos `requirements.txt` con versiones distintas |
| Servidor ASGI | Uvicorn | 0.40.0 | Sin configuración de *workers* documentada |
| Base de datos | MongoDB Atlas | — | BD `kofan_hospedaje_db` *hardcodeada* |
| Driver | Motor (async) | 3.7.1 | ⚠️ **Motor está deprecado** por MongoDB en favor de la API async nativa de PyMongo (`AsyncMongoClient`) |
| Validación | Pydantic v2 | 2.12.5 | Se usa a medias (muchos endpoints reciben `Form(...)` sueltos o `dict`) |
| Auth | python-jose (JWT HS256) + passlib/bcrypt | 3.5.0 / 1.7.4 / 4.0.1 | ⚠️ `python-jose` y `passlib` están sin mantenimiento; bcrypt fijado en 4.0.1 por incompatibilidad con passlib |
| Tareas programadas | APScheduler (AsyncIOScheduler) | sin versión fija | Corre dentro del proceso web |
| Archivos | Disco local `backend/static/uploads` servido con `StaticFiles` | — | `cloudinary` aparece en el `requirements.txt` raíz pero no se usa |
| Config | python-dotenv | — | `.env` cargado dos veces (config.py y client.py) |

### Frontend
| Componente | Tecnología | Versión |
|---|---|---|
| Framework | Vue 3 (Composition API, `<script setup>`) | 3.5 |
| Build | Vite | 7.3 |
| Estado | Pinia (stores tipo *setup*) | 3.0 |
| Router | Vue Router (history mode, *lazy loading*, guardias por `meta`) | 4.x |
| HTTP | Axios con interceptores (token + 401 → logout) | 1.13 |
| UI | Bootstrap 5.3 + Bootstrap Icons + FontAwesome 7 | — |
| Componentes | SweetAlert2, v-calendar, vuedraggable, html2pdf.js | — |
| Lenguaje | JavaScript (sin TypeScript), `jsconfig.json` con alias `@` | — |

### Pruebas
| Capa | Herramienta | Cobertura real |
|---|---|---|
| Backend | pytest + httpx + mongomock-motor | **5 pruebas** |
| Frontend unit | Vitest + @vue/test-utils + jsdom | **3 pruebas** |
| E2E | Playwright | **1 prueba** |

### Infraestructura (según `docs/IMPLEMENTACION_PRODUCCION...md`)
Frontend en Netlify/Vercel, backend Docker en VPS (DigitalOcean / Lightsail) con Nginx + Certbot, BD en MongoDB Atlas. **No existen** Dockerfile, docker-compose ni pipeline CI en el repositorio.

---

## 3. Arquitectura actual

```
┌──────────────────────── Frontend (Vue 3 + Vite) ────────────────────────┐
│  PublicLayout  /hospedaje (Home, About, Gallery)                         │
│  AuthLayout    /auth (Login, Register)                                   │
│  AppLayout     /app  (Perfil, Reservas, Notificaciones)  requiresAuth    │
│  AdminLayout   /admin (Dashboard, Rooms, Bookings, Users, Gallery, Config│
│  Pinia: auth, reserva, config, gallery    Axios: /api → proxy Vite       │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │  HTTP (Bearer JWT en localStorage)
┌──────────────────────────────▼───────────────────────────────────────────┐
│                     Backend FastAPI (monolito)                            │
│  routers/  auth, register, users, admin, rooms, bookings, availability,   │
│            invoices, gallery, config, dashboard, notifications, earnings  │
│  services/ lógica + acceso directo a Mongo (sin repositorios)            │
│  schemas/ + models/  (Pydantic y "entities" mezclados)                   │
│  StaticFiles: /static/uploads, /static/images  (disco local)             │
│  APScheduler: cancelar_reservas_vencidas (cada 24h)                      │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ Motor (async)
                      ┌────────▼────────┐
                      │  MongoDB Atlas  │  users, rooms, bookings, invoices,
                      │                 │  gallery, notifications, settings,
                      └─────────────────┘  room_logs
```

**Puntos positivos a conservar**
- Separación `routers / services / schemas` en backend.
- `lifespan` unificado para scheduler e índices.
- Rutas *lazy* y layouts por zona en el frontend; `manualChunks` en Vite.
- Motor de disponibilidad con intervalo semiabierto (`entrada < salida_nueva AND salida > entrada_nueva`) — correcto conceptualmente.
- Auditoría de habitaciones (`room_logs`) con diff de cambios.
- Concepto de reserva de invitado + vinculación posterior al registrarse (buena idea de producto, mala implementación — ver 5.5).

---

## 4. Reglas y convenciones identificadas

### 4.1 Reglas de negocio (implícitas en el código)
| # | Regla | Dónde |
|---|---|---|
| RN-01 | Estados de reserva: `pendiente → confirmada → ocupada → finalizada`, y `cancelada` | [booking_schema.py](../backend/schemas/booking_schema.py) |
| RN-02 | Una habitación no puede tener dos reservas activas (`pendiente`, `confirmada`, `ocupada`) que se solapen | [booking_service.py](../backend/services/booking_service.py) |
| RN-03 | El día de *check-out* queda libre para una nueva entrada (intervalo semiabierto) | `booking_service.py` + [reserva.js](../frontend/src/stores/reserva.js) |
| RN-04 | Total = precio/noche × noches; anticipo = 50 % del total | `reserva.js` (**solo en el frontend**) |
| RN-05 | Toda reserva web exige comprobante de pago adjunto | `reserva.js` (validación solo en frontend) |
| RN-06 | Las reservas `pendiente` se cancelan automáticamente si superan un tiempo límite (código: 2 minutos; job: cada 24 h) | [task_service.py](../backend/services/task_service.py) |
| RN-07 | Se permite reservar como invitado; al registrarse con el mismo correo, las reservas se vinculan a la cuenta | [user_service.py](../backend/services/user_service.py) |
| RN-08 | Si recepción crea un usuario sin contraseña, la contraseña es el número de documento | `user_service.py:9` |
| RN-09 | La búsqueda asigna la habitación **más barata** del tipo pedido con capacidad ≥ huéspedes | [availability_service.py](../backend/services/availability_service.py) |
| RN-10 | Tipos de habitación: *individual*, *familiar*, *cabaña* (detectados por regex) | `availability_service.py` |
| RN-11 | No se pueden agregar consumos a una factura `closed` | [invoices.py](../backend/routers/invoices.py) |
| RN-12 | Un admin no puede eliminarse a sí mismo | [admin.py](../backend/routers/admin.py) |
| RN-13 | Huéspedes = titular + acompañantes (para métricas) | [dashboard_service.py](../backend/services/dashboard_service.py) |
| RN-14 | Zona horaria del negocio: Colombia (UTC-5) | `dashboard_service.py`, `notifications_service.py` |

### 4.2 Convenciones técnicas
- **Roles:** `admin`, `recepcionista`, `client` (pero `recepcionista` **no tiene ningún permiso efectivo**: solo existe `required_admin`).
- **Auth:** OAuth2 *password flow*, JWT HS256, `sub` = `_id` del usuario, access 30 min / refresh 7 días.
- **Fechas:** se guardan como `datetime` UTC a medianoche.
- **Archivos:** nombre `uuid4().hex + extensión original`, URL relativa `/static/uploads/...` guardada en BD.
- **Prefijos de rutas inconsistentes:** `/api/reservas`, `/api/notificaciones` vs `/rooms`, `/users`, `/invoices`, `/busqueda`... El proxy de Vite quita `/api`, por lo que el frontend termina llamando `/api/api/reservas`.
- **Idioma:** mezcla español/inglés en nombres de colecciones, campos y endpoints (`habitacion_id` vs `room_number`, `cliente_email` vs `guest_email`).

---

## 5. Hallazgos — Seguridad

### 🔴 5.1 El router de facturas no tiene autenticación
[invoices.py:10](../backend/routers/invoices.py#L10) define `dependencies= [Depends(required_admin)]` como **variable suelta**, no dentro de `APIRouter(...)`. Resultado: **cualquier persona anónima** puede leer facturas (nombre, documento, correo, teléfono del huésped), crearlas, modificar totales y cerrarlas.
**Solución:** `APIRouter(prefix="/invoices", dependencies=[Depends(required_admin)])` + prueba automatizada que verifique 401 en todos los endpoints protegidos.

### 🔴 5.2 Cualquier cliente registrado puede crear habitaciones
[rooms.py:102](../backend/routers/rooms.py#L102) — `/rooms/create-with-images` usa `get_current_user` en vez de `required_admin`. Además, en [gallery.py:17](../backend/routers/gallery.py#L17) se mezcla `dependencies=[required_admin]` con `user=Depends(get_current_user)` (funciona, pero es frágil).

### 🔴 5.3 El precio de la reserva lo decide el cliente
[bookings.py:21](../backend/routers/bookings.py#L21) y `:67` reciben `monto_total` desde el formulario. Un usuario puede reservar una cabaña por $1. El cálculo (RN-04) existe **solo en el frontend**.
**Solución:** calcular `monto_total`, `noches` y `anticipo` en el servicio a partir de `room.price` (y en el futuro, de tarifas por temporada).

### 🔴 5.4 El *refresh token* sirve como *access token* (sesiones de 7 días)
[security.py](../backend/core/security.py) firma access y refresh con el mismo secreto y **sin claim `type`**. [auth.py (deps)](../backend/dependencies/auth.py) acepta cualquier JWT válido → el refresh token de 7 días funciona como access token. Además **no existe endpoint `/auth/refresh`** y el frontend no guarda el refresh token: el diseño está a medio camino.

### 🔴 5.5 Robo de reservas al registrarse (vinculación por correo sin verificar)
[register.py](../backend/routers/register.py) llama `link_guest_bookings_to_user(email)` inmediatamente después de registrar, **sin verificar que el correo pertenezca al usuario**. Cualquiera que se registre con el correo de otra persona obtiene sus reservas (fechas, montos, comprobantes). Agravante: el filtro usa regex sin escapar ([user_service.py:86](../backend/services/user_service.py#L86)), así que `.` coincide con cualquier carácter.
**Solución:** verificación de correo (token por email) antes de vincular; comparar por igualdad exacta sobre un campo `email_normalizado`.

### 🔴 5.6 Comprobantes de pago públicos
Los comprobantes se guardan en `static/uploads`, montado públicamente sin autenticación. Son datos financieros/personales accesibles por URL. Hoy la URL es aleatoria (uuid), pero queda expuesta en respuestas, logs y el panel.
**Solución:** almacenamiento privado (bucket S3/R2/GCS o carpeta no servida) + endpoint autenticado o URLs firmadas con expiración.

### 🔴 5.7 Secreto JWT por defecto y credenciales impresas
- [config.py:10](../backend/core/config.py#L10): `SECRET_KEY` cae a `"mysecretkey"` si falta → cualquiera puede forjar tokens de admin.
- La versión comprometida de `db/client.py` **imprime `MONGO_URI` con contraseña** en consola (el cambio sin commit lo corrige). Si esos logs se compartieron o el servidor estuvo desplegado, **rotar credenciales de Atlas**.
**Solución:** `pydantic-settings` con campos obligatorios; fallar al arrancar si falta un secreto.

### 🔴 5.8 Hash de contraseña filtrado en respuesta del admin
[admin.py](../backend/routers/admin.py) `PATCH /admin/users/{id}` devuelve el documento actualizado **sin quitar `password`** (el router `users.py` sí lo hace). Además existen **dos routers duplicados** para la misma gestión de usuarios (`/admin/users` y `/users`).

### 🟠 5.9 Usuarios suspendidos conservan acceso
`get_current_user` no valida `is_active`, y `login` tampoco. "Suspender" o "eliminar mi cuenta" no tiene efecto real.

### 🟠 5.10 Contraseña por defecto = número de documento
[user_service.py:9](../backend/services/user_service.py#L9). Además el registro **público** acepta `password` opcional → una cuenta pública puede quedar con el documento como contraseña. El documento es un dato semipúblico (aparece en facturas).
**Solución:** contraseña obligatoria en registro público; en recepción, enviar enlace de "establecer contraseña" de un solo uso.

### 🟠 5.11 Subida de archivos insegura
- La extensión se toma del nombre original ([media_service.py:16](../backend/services/media_service.py#L16)) y el `content_type` lo declara el cliente → se puede subir `x.html` o `x.svg` declarado como `image/png` y servirlo desde el dominio del backend (XSS almacenado).
- Sin límite de tamaño (DoS de disco).
- `save_image` (síncrono) se ejecuta directamente en el *event loop* en `bookings.py`.
- Tres implementaciones distintas de guardado de archivos (`media_service`, `gallery_service`, `rooms`).
**Solución:** un único `StorageService`; validar firma mágica (Pillow/`filetype`), lista blanca de extensiones derivada del tipo detectado, límite de tamaño, re-codificar imágenes (elimina EXIF/payloads).

### 🟠 5.12 Enumeración de usuarios y sin *rate limiting*
El login responde "Correo no encontrado" vs "Contraseña incorrecta" y registra el correo con `print`. No hay límite de intentos en `/auth/login`, `/register` ni `/api/reservas/invitado` (spam de reservas y archivos).

### 🟡 5.13 Otros
- Token en `localStorage` (vulnerable a XSS). Preferir cookie `HttpOnly; Secure; SameSite` para el refresh token.
- CORS solo con `localhost` *hardcodeado* en [main.py:65](../backend/main.py#L65).
- Regex sin escapar en búsqueda de habitaciones por nombre (`room_service.py:100`) → riesgo de ReDoS.
- `ObjectId(room_id)` sin validar en varios endpoints → 500 en vez de 400/404.
- Errores internos devueltos al cliente (`detail=f"Error...: {str(e)}"`).
- No hay cabeceras de seguridad (CSP, HSTS, X-Content-Type-Options).

---

## 6. Hallazgos — Lógica de negocio e integridad de datos

### 🟠 6.1 Doble reserva por condición de carrera
`create_booking_service` hace "buscar choque → insertar" en dos operaciones separadas. Dos peticiones simultáneas para la misma habitación/fechas pasan ambas la validación.
**Solución recomendada:** colección `room_nights` con índice único `(room_id, fecha)`; al reservar se insertan todas las noches dentro de una **transacción** (Atlas soporta transacciones en replica set). Si alguna falla por duplicado → 409. Alternativa: bloqueo optimista por habitación con un documento de versión.

### 🟠 6.2 El bot de cancelación destruye reservas legítimas
[task_service.py:13](../backend/services/task_service.py#L13) cancela toda reserva `pendiente` con más de **2 minutos**, y el job corre **cada 24 h** ([main.py:22](../backend/main.py#L22)). Como toda reserva web nace `pendiente` y espera revisión del comprobante por el admin, **cada día se cancelan todas las reservas no revisadas**, sin notificar al cliente. Valores de prueba quedaron en producción.
**Solución:** plazo configurable (p. ej. 24-48 h), job frecuente (cada 5-15 min), estado separado `pendiente_pago` vs `pendiente_verificacion`, y notificación al cliente.

### 🟠 6.3 `$lookup` a una colección que ya no existe
`booking_service.py:233` y `dashboard_service.py:78` hacen `$lookup` a `clients`, pero los usuarios se migraron a `users`. El nombre del cliente nunca se resuelve desde la cuenta (se usa el fallback del snapshot).

### 🟠 6.4 Edición de reservas sin validar disponibilidad
`PUT /api/reservas/{id}/detalles` permite al admin cambiar fechas sin comprobar solapamientos ni recalcular el monto. Tampoco valida transiciones de estado (se puede pasar de `cancelada` a `ocupada`, o de `finalizada` a `pendiente`).
**Solución:** máquina de estados explícita con transiciones permitidas y auditoría.

### 🟠 6.5 Disponibilidad modelada con una bandera estática
`rooms.is_available` es un booleano manual que mezcla "habitación habilitada" con "ocupada ahora". La búsqueda y `/rooms/public` filtran por esa bandera, mientras el dashboard calcula ocupación por reservas → **métricas inconsistentes** (`get_all_bookings_service` reporta una ocupación y `dashboard` otra).
**Solución:** `active` (habilitada para venta) + `estado_operativo` (limpieza/mantenimiento); la ocupación siempre se **deriva** de las reservas.

### 🟡 6.6 Otros problemas de datos
- Facturas: `booking_id` guardado como `string` mientras las reservas usan `ObjectId`; totales calculados por el cliente en `sync-by-booking`; sin numeración consecutiva; `consumos_extras` viven duplicados en `bookings` y en `invoices`.
- `pendientes_por_aprobar` cuenta solo los pendientes **de la página actual**.
- Búsqueda por tipo con regex "caba|fami|indiv" en vez de un catálogo de tipos (`room_types`).
- Datos con tipos inconsistentes (`capacity` como texto, `active` como `"true"`), compensados con `int()` / `in [True,"true","True"]` en el código: falta validación de esquema en BD.
- Reserva autenticada fija `tipo_documento="CC"` y `cliente_documento="0"` en vez de usar los datos del perfil.
- Comprobante en PDF: el frontend lo acepta, pero el backend solo admite `jpeg/png/webp` → error confuso al usuario.
- Índices faltantes: `users.email` (único), `users.number_document` (único), `notifications.user_id+created_at`, `invoices.booking_id` (único), `bookings(habitacion_id, estado, fecha_entrada, fecha_salida)` compuesto.
- `/reports/earnings` lanza `KeyError` (`user['username']` no existe en el documento).

---

## 7. Hallazgos — Arquitectura y diseño

| # | Severidad | Hallazgo | Propuesta |
|---|---|---|---|
| 7.1 | 🟠 | **Marca y BD *hardcodeadas*** ("Kofán" en mensajes, `kofan_hospedaje_db`, colores, textos). Para Kawari habría que buscar/reemplazar en decenas de archivos. | Config centralizada (`HOTEL_NAME`, `DB_NAME`, `TIMEZONE`, `CURRENCY`, `DEPOSIT_PERCENT`...) + `settings` en BD para textos/branding. Convertir la base en plantilla reutilizable. |
| 7.2 | 🟠 | Servicios lanzan `HTTPException` y routers acceden a `db` directamente (`rooms.py`, `invoices.py` completos sin servicio). Capas acopladas. | `routers` (HTTP) → `services` (dominio, excepciones propias) → `repositories` (Mongo). *Exception handlers* globales que traduzcan errores de dominio a HTTP. |
| 7.3 | 🟡 | Configuración dispersa: `.env` se carga en `config.py` y en `client.py`; constantes en código. | `pydantic-settings` (`Settings` única, inyectada). |
| 7.4 | 🟡 | `schemas/` y `models/` mezclan responsabilidades (Pydantic de entrada en `models/`, serializadores en `schemas/`, "entities" a mano). | `schemas/` = DTOs Pydantic de entrada/salida con `response_model`; `domain/` = entidades; eliminar serializadores manuales. Evaluar **Beanie** u ODM ligero. |
| 7.5 | 🟡 | Endpoints de creación reciben 10+ `Form(...)` sueltos y construyen el schema a mano. | Un modelo Pydantic + `Annotated[..., Form()]` (FastAPI ≥0.113 soporta modelos de formulario) o separar subida de archivo del JSON. |
| 7.6 | 🟡 | Prefijos y nombres de rutas inconsistentes (`/api/reservas`, `/rooms`, `/busqueda`, `/reports`), sin versionado. | `/api/v1/<recurso>` en inglés o español, pero **uno solo**. |
| 7.7 | 🟡 | Roles: solo existe `required_admin`; `recepcionista` no sirve. | RBAC por permisos (`require_permission("bookings:update")`) con mapa rol→permisos. |
| 7.8 | 🟡 | Zona horaria con `timedelta(hours=5)` y `datetime.utcnow()` (deprecado) mezclado con `datetime.now(timezone.utc)`. Backend formatea fechas para la UI. | Guardar UTC, devolver ISO-8601, formatear en el frontend con `Intl` / `zoneinfo("America/Bogota")`. |
| 7.9 | 🟡 | Notificaciones acopladas dentro de `update_booking_status_service`. | Eventos de dominio (`BookingConfirmed`) + manejadores (panel, email, WhatsApp). |
| 7.10 | 🟢 | Código muerto/duplicado: `test_atlas.py`, `doc_backend.py`, `doc_frontend.py`, bloques comentados, comentarios repetidos, router `admin.py` duplicando `users.py`, `earnings.py` placeholder. | Limpieza. |

---

## 8. Hallazgos — Escalabilidad y rendimiento

| # | Severidad | Hallazgo | Impacto | Propuesta |
|---|---|---|---|---|
| 8.1 | 🟠 | **APScheduler dentro del proceso web.** Con `uvicorn --workers 4` o varias réplicas, el job se ejecuta N veces. | Duplicación de efectos; imposible escalar horizontalmente. | Proceso *worker* separado (ARQ / Celery / Dramatiq con Redis) o cron externo + *lock* distribuido. |
| 8.2 | 🟠 | **Archivos en disco local** del servidor (145 MB ya en el repo). | No escala a varias instancias; se pierde con contenedores efímeros; sin CDN. | Object storage (Cloudflare R2 / S3 / Cloudinary) + CDN; generar miniaturas/WebP. |
| 8.3 | 🟡 | Disponibilidad: trae **todas** las reservas solapadas y **todas** las habitaciones candidatas a Python para filtrar. | O(n) en memoria por búsqueda. | Filtrar capacidad/estado/precio en la consulta Mongo, `sort({price:1}).limit(1)`; índice compuesto. |
| 8.4 | 🟡 | `count_documents` + agregación separados en cada listado; `/rooms/public` limitado a 100 sin paginar; `booked-dates` hasta 1000 sin rango de fechas. | Latencia creciente. | `$facet` para conteo+página; filtrar `booked-dates` por ventana (p. ej. próximos 12 meses). |
| 8.5 | 🟡 | Dashboard recalcula todo en cada carga. | Carga en BD con muchos admins. | Caché corta (Redis, 60 s) o vistas materializadas (`$merge`) nocturnas. |
| 8.6 | 🟡 | Paginación *skip/limit* sin tope (`limit` arbitrario del cliente). | Consultas costosas / DoS. | `limit ≤ 100`; paginación por cursor en listados grandes. |
| 8.7 | 🟢 | Sin compresión GZip, sin cabeceras de caché para estáticos. | Mayor ancho de banda. | `GZipMiddleware` / Nginx; `Cache-Control` inmutable para assets con hash. |
| 8.8 | 🟢 | Frontend: imágenes de 21 MB en `src/img` empaquetadas por Vite; todos los íconos FA registrados globalmente. | Bundle pesado, LCP alto. | Optimizar a WebP/AVIF, `loading="lazy"`, `srcset`; mover fotos de contenido a storage/CMS. |

---

## 9. Hallazgos — Frontend

| # | Severidad | Hallazgo | Propuesta |
|---|---|---|---|
| 9.1 | 🟠 | URLs del backend *hardcodeadas* (`http://127.0.0.1:8000` en `RoomsManager.vue:8`, `BookingsManager.vue:549`) y **dos variables distintas** (`VITE_API_URL` y `VITE_BACKEND_URL`) con fallbacks diferentes en 7 archivos. En producción las imágenes y comprobantes apuntarán a localhost. | Un único módulo `config/env.js` + helper `assetUrl(path)`. |
| 9.2 | 🟠 | El 401 hace logout inmediato (no hay *refresh*); el rol se lee de `localStorage` (`userData`) y la guardia de admin confía en él. | Interceptor con *refresh* y cola de reintentos; obtener `/users/me` al iniciar la app; la seguridad real queda en el backend. |
| 9.3 | 🟡 | Componentes gigantes: `BookingsManager.vue` (823 líneas), `AboutUs.vue` (744), `RoomsManager.vue` (678), `Home.vue` (599). Lógica, llamadas HTTP y presentación mezcladas. | Extraer *composables* (`useBookings`, `usePagination`), componentes de tabla/filtros, y servicios API por recurso (ya existe la carpeta `services/`, pero se usa poco). |
| 9.4 | 🟡 | Login duplica la lógica del store (`Login.vue:211` escribe `localStorage` directamente). | Solo `authStore.login()` toca el almacenamiento. |
| 9.5 | 🟡 | Sin ESLint/Prettier, sin TypeScript, `package.json` con dependencias basura (`"from"`, `"git"`), nombre `vue-project`. | ESLint + Prettier + (opcional) migración gradual a TS con `vue-tsc`. |
| 9.6 | 🟡 | Contenido institucional (misión, visión, textos de AboutUs, fotos) *hardcodeado* en componentes. | Contenido gestionable desde `settings`/CMS para que Kawari no requiera tocar código. |
| 9.7 | 🟢 | Accesibilidad y SEO: SPA sin meta-tags por ruta, sin `sitemap`, sin datos estructurados `Hotel`. Para un hotel, el SEO es canal de venta. | `@unhead/vue` para meta por ruta; considerar SSR/SSG (Nuxt) para páginas públicas a mediano plazo. |
| 9.8 | 🟢 | `v-html` en `RoomCalendarModal.vue:308` (hoy con datos propios, sin riesgo, pero mala práctica). | Reemplazar por plantilla. |

---

## 10. Hallazgos — Calidad, DevOps y repositorio

| # | Severidad | Hallazgo | Propuesta |
|---|---|---|---|
| 10.1 | 🟠 | **Cobertura de pruebas casi nula** (5 + 3 + 1). Ninguna prueba cubre autorización, doble reserva ni cálculo de precios. | Suite mínima por dominio (ver backlog), *fixtures* con `mongomock-motor` o Mongo real en contenedor (testcontainers). |
| 10.2 | 🟠 | Dos `requirements.txt` divergentes; el de la raíz está en **UTF-16** y con versiones distintas; el de backend incluye `windows-curses` (rompe instalación en Linux/Docker) y dependencias de test (`mongomock`, `coverage`) en producción; varias sin versión fija. | Un solo gestor: `pyproject.toml` con **uv** (o Poetry), grupos `dev`/`test`, *lockfile*. |
| 10.3 | 🟠 | **145 MB de imágenes subidas versionadas en git** (`backend/static/images`, `uploads`), además de `.coverage` y `test-results/`. | Sacar del repo (`.gitignore`), mover a storage; para Kawari empezar con historial limpio. |
| 10.4 | 🟡 | Sin Dockerfile, docker-compose ni CI. | `Dockerfile` multi-stage para API y web, `docker-compose.yml` (api, web, mongo, redis), GitHub Actions: lint + tests + build. |
| 10.5 | 🟡 | `print()` como logging (con emojis), sin niveles ni correlación; `except: pass` silencioso. | `logging` estructurado (JSON), *request-id* middleware, Sentry para errores. |
| 10.6 | 🟡 | Sin endpoint de salud. | `/health` (liveness) y `/ready` (ping a Mongo). |
| 10.7 | 🟡 | Sin migraciones/semillas de BD (índices creados al arrancar, sin *seed* de admin ni tipos de habitación). | Script `seed` idempotente + migraciones (p. ej. `mongodb-migrations` o scripts versionados). |
| 10.8 | 🟢 | README del frontend desactualizado (no menciona backend), README de testing con rutas de otra máquina (`L:\SENA\...`). | README raíz único con *quick start* (`docker compose up`). |

---

## 11. Riesgos legales / normativos (Colombia)

> No es asesoría legal; son puntos a validar con el hotel/contador.

1. **Habeas Data (Ley 1581 de 2012):** se almacenan documentos de identidad del titular y acompañantes, teléfonos y comprobantes bancarios. Se requiere política de tratamiento de datos, **consentimiento explícito** en registro y reserva, mecanismo de consulta/supresión y control de acceso a esos datos (hoy expuestos — ver 5.1 y 5.6).
2. **Facturación electrónica (DIAN):** el módulo `invoices` genera un "folio" interno, **no una factura electrónica válida**. Renombrarlo a *cuenta/folio de huésped* o integrarse con un proveedor tecnológico autorizado.
3. **Registro hotelero (TRA / reporte a Migración para extranjeros):** el sistema ya recoge datos de huéspedes; es una oportunidad de producto para Kawari (exportar/reportar), y un motivo más para validar la calidad del dato.

---

## 12. Arquitectura objetivo propuesta para Hotel Kawari

Se propone un **monolito modular** (no microservicios: el tamaño del negocio no lo justifica) con fronteras claras, listo para escalar horizontalmente.

```
                    ┌───────────── CDN (Cloudflare) ─────────────┐
                    │  Frontend Vue 3 (estático)  +  imágenes    │
                    └───────────────┬────────────────────────────┘
                                    │ HTTPS  /api/v1
                         ┌──────────▼──────────┐
                         │  Nginx / proxy      │  rate limit, gzip, headers
                         └──────────┬──────────┘
              ┌─────────────────────┼─────────────────────┐
     ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
     │ API FastAPI #1  │   │ API FastAPI #N  │   │ Worker (ARQ)    │
     │ (stateless)     │   │ (stateless)     │   │ expiraciones,   │
     └────────┬────────┘   └────────┬────────┘   │ emails, reportes│
              └──────────┬──────────┘            └────────┬────────┘
                ┌────────▼────────┐  ┌───────────┐        │
                │ MongoDB Atlas   │  │  Redis    │◄───────┘
                │ (replica set,   │  │ cola/caché│
                │  transacciones) │  │ rate-limit│
                └─────────────────┘  └───────────┘
                ┌─────────────────────────────────┐
                │ Object Storage (R2/S3)          │
                │  /public  → fotos (CDN)         │
                │  /private → comprobantes (URL   │
                │             firmada)            │
                └─────────────────────────────────┘
```

### Estructura de backend sugerida
```
backend/app/
├── core/          settings.py (pydantic-settings), security.py, logging.py, errors.py
├── api/v1/        routers por módulo (solo HTTP, response_model obligatorio)
├── modules/
│   ├── auth/      service, schemas (login, refresh, verify-email, reset)
│   ├── users/     service, repository, schemas
│   ├── rooms/     room_types, rooms, rates (tarifas por temporada)
│   ├── bookings/  service, state_machine.py, pricing.py, availability.py, repository
│   ├── folios/    (ex-invoices) cargos, pagos, cierre
│   ├── media/     storage.py (interfaz) + s3.py / local.py
│   ├── cms/       settings del sitio, galería, textos
│   └── notifications/ eventos → canales (panel, email, WhatsApp)
├── workers/       tareas ARQ (expirar reservas, recordatorios)
└── tests/         unit/, integration/, e2e/
```

### Decisiones clave
| Decisión | Elección | Motivo |
|---|---|---|
| Driver Mongo | PyMongo Async (`AsyncMongoClient`) o Beanie sobre él | Motor está deprecado |
| JWT | PyJWT + claim `type` + rotación de refresh en cookie HttpOnly | Seguridad y mantenimiento |
| Hash | `pwdlib` con Argon2 (o `bcrypt` directo) | passlib sin mantenimiento |
| Anti doble-reserva | `room_nights` con índice único + transacción | Garantía a nivel de BD |
| Precios | Calculados 100 % en backend (`pricing.py`) | Integridad |
| Tareas | Worker separado (ARQ + Redis) | Escalado horizontal |
| Archivos | Object storage, privado para comprobantes | Escala + privacidad |
| Config multi-hotel | Settings por entorno + `settings` en BD | Reutilizar la base para futuros hoteles |
| Dependencias | `uv` + `pyproject.toml`; `npm` con lockfile | Builds reproducibles |

---

## 13. Lista de tareas (backlog priorizado)

Tamaño estimado: **S** ≤ ½ día · **M** 1-2 días · **L** 3-5 días.

### Fase 0 — Bloqueantes de seguridad (antes de cualquier funcionalidad nueva)
> ✅ Implementada el 2026-11-09 — pruebas en `testing/test_seguridad_fase0.py`, accesos en `docs/ENDPOINTS_ACCESO.md`. Pendiente: migrar comprobantes antiguos (`python -m backend.scripts.migrar_comprobantes_privados --aplicar`) y rotar credenciales.

- [x] **S** Proteger el router de facturas con `required_admin` dentro de `APIRouter(...)` (5.1).
- [x] **S** Cambiar `/rooms/create-with-images` a `required_admin`; revisar **todos** los endpoints y documentar su nivel de acceso (5.2).
- [x] **M** Calcular `monto_total`, noches y anticipo en el backend; ignorar el valor del cliente (5.3).
- [x] **S** Agregar claim `type` a los JWT y rechazar refresh tokens en `get_current_user` (5.4).
- [x] **S** Validar `is_active` en login y en `get_current_user` (5.9).
- [x] **S** Eliminar el valor por defecto de `SECRET_KEY`; fallar al arrancar si falta (5.7).
- [ ] **S** ⚠️ *Manual:* rotar `SECRET_KEY` y credenciales de Atlas (5.7).
- [x] **S** Quitar `password` de la respuesta de `PATCH /admin/users/{id}` y eliminar el router duplicado (5.8).
- [x] **M** Desactivar la vinculación automática de reservas por correo hasta tener verificación de email; usar igualdad exacta, no regex (5.5).
- [x] **M** Mover comprobantes a almacenamiento privado con acceso autenticado (5.6).
- [x] **M** Endurecer subida de archivos: validación por firma, extensión derivada, límite de tamaño, servicio único (5.11).
- [x] **S** Mensaje de login genérico; quitar `print` de correos (5.12).
- [x] **S** Corregir el bot de cancelación: plazo configurable realista y job frecuente (6.2).
- [x] **S** Sacar `backend/static/uploads`, `static/images`, `.coverage`, `test-results/` del control de versiones.

### Fase 1 — Fundaciones de la base Kawari
- [ ] **M** `pydantic-settings`: un único `Settings` (Mongo URI, DB name, secretos, CORS, nombre del hotel, zona horaria, moneda, % anticipo, plazo de expiración).
- [ ] **M** Eliminar toda referencia *hardcodeada* a "Kofán" (backend, frontend, textos, BD) y llevarla a configuración/`settings` en BD.
- [ ] **M** Unificar dependencias Python en `pyproject.toml` (uv), separar `dev/test`, quitar `windows-curses`, fijar versiones.
- [ ] **M** Migrar Motor → PyMongo Async; `python-jose` → PyJWT; `passlib` → `pwdlib[argon2]`.
- [ ] **L** Reestructurar backend en módulos (`routers → services → repositories`), errores de dominio + *exception handlers*, `response_model` en todos los endpoints.
- [ ] **M** Unificar prefijos bajo `/api/v1`, nombres consistentes (un idioma) y quitar el doble `/api/api`.
- [ ] **M** Esquema de datos revisado: catálogo `room_types`, `active` vs estado operativo, referencias siempre `ObjectId`, eliminar `$lookup` a `clients` (6.3, 6.5).
- [ ] **M** Índices únicos y compuestos (users.email, users.number_document, invoices.booking_id, bookings compuesto, notifications) + validación `$jsonSchema` en colecciones críticas.
- [ ] **L** Anti doble-reserva con `room_nights` + transacciones; responder 409 en conflicto (6.1).
- [ ] **M** Máquina de estados de reserva con transiciones válidas y registro de auditoría (6.4).
- [ ] **M** Auth completa: `/auth/refresh` con rotación, refresh en cookie HttpOnly, logout que invalida, verificación de email, recuperación de contraseña, contraseña obligatoria en registro público (5.4, 5.10).
- [ ] **M** RBAC por permisos con rol `recepcionista` funcional (7.7).
- [ ] **S** Fechas: UTC en BD, ISO en API, `zoneinfo` para lógica de negocio; quitar `timedelta(hours=5)` y `utcnow()` (7.8).
- [ ] **S** Frontend: módulo único de configuración de entorno + helper `assetUrl`; eliminar URLs `localhost` (9.1).
- [ ] **M** Frontend: interceptor con refresh token y carga de `/users/me` al iniciar (9.2).
- [ ] **S** Limpiar `package.json` (`from`, `git`), renombrar proyecto, unificar `package.json` raíz/frontend.
- [ ] **S** Script `seed` idempotente (admin inicial, tipos de habitación, settings por defecto).

### Fase 2 — Calidad y automatización
- [ ] **M** Pruebas de autorización: cada endpoint protegido devuelve 401/403 sin credenciales/rol adecuado.
- [ ] **M** Pruebas de dominio: precios, disponibilidad, solapamiento (incluida concurrencia), transiciones de estado, expiración.
- [ ] **M** Pruebas de frontend para stores (`auth`, `reserva`) y E2E del flujo de reserva completo (invitado y autenticado) y del flujo admin (aprobar → check-in → check-out).
- [ ] **S** Linters: Ruff + mypy (backend), ESLint + Prettier (frontend); `pre-commit`.
- [ ] **M** `Dockerfile` (api, web) + `docker-compose.yml` (api, web, mongo, redis) para desarrollo local con un comando.
- [ ] **M** GitHub Actions: lint, tests con cobertura mínima (≥70 % en `modules/bookings` y `auth`), build del frontend.
- [ ] **S** Logging estructurado + *request-id*; reemplazar todos los `print`; integrar Sentry.
- [ ] **S** Endpoints `/health` y `/ready`.
- [ ] **M** Refactorizar `BookingsManager.vue`, `RoomsManager.vue`, `Home.vue`, `AboutUs.vue` en componentes + composables; usar la capa `services/` para todas las llamadas HTTP.

### Fase 3 — Producción y escalabilidad
- [ ] **M** Object storage (R2/S3) con bucket público (fotos vía CDN) y privado (comprobantes con URL firmada); generación de miniaturas WebP.
- [ ] **M** Worker separado (ARQ + Redis) para expiración de reservas, emails y reportes; eliminar APScheduler del proceso web (8.1).
- [ ] **S** Rate limiting (login, registro, reservas de invitado) y CAPTCHA en formularios públicos.
- [ ] **S** Cabeceras de seguridad (CSP, HSTS, X-Content-Type-Options), CORS por entorno, GZip.
- [ ] **M** Optimizar consultas de disponibilidad y listados (filtros en Mongo, `$facet`, límites máximos, `booked-dates` por ventana) (8.3-8.6).
- [ ] **S** Caché del dashboard (Redis 60 s) o agregaciones materializadas.
- [ ] **S** Optimizar imágenes del frontend (WebP/AVIF, lazy loading, `srcset`).
- [ ] **S** Backups y alertas en Atlas; documentar procedimiento de restauración.

### Fase 4 — Producto (oportunidades para Kawari)
- [ ] **L** Pasarela de pago local (p. ej. Wompi / Mercado Pago / PSE) para reemplazar la carga manual de comprobantes; webhooks → confirmación automática.
- [ ] **M** Tarifas por temporada, fines de semana y estancia mínima (`rates`).
- [ ] **M** Notificaciones por correo/WhatsApp (confirmación, recordatorio de check-in, expiración).
- [ ] **M** Contenido del sitio (textos, misión/visión, galería) 100 % editable desde el panel.
- [ ] **M** SEO: meta por ruta, sitemap, datos estructurados `Hotel`; evaluar SSR/SSG para páginas públicas.
- [ ] **M** Cumplimiento: política de datos y consentimiento (Ley 1581), renombrar facturas a folios o integrar facturación electrónica, exportación de registro de huéspedes.
- [ ] **S** i18n (español/inglés) para turistas extranjeros.

---

### Orden recomendado de ejecución
1. Crear el repositorio de **Hotel Kawari** con historial limpio (sin imágenes subidas ni artefactos).
2. Ejecutar **Fase 0** completa con pruebas que la respalden.
3. Ejecutar **Fase 1** — al terminarla, la base queda parametrizada y reutilizable.
4. **Fase 2** en paralelo al desarrollo de funcionalidades nuevas (cada PR con pruebas y CI verde).
5. **Fase 3** antes del lanzamiento público.
6. **Fase 4** según prioridades del negocio.
