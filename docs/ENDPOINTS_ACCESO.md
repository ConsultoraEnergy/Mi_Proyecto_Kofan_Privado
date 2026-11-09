# Nivel de acceso por endpoint (API v1)

> Fuente de verdad: las listas `PUBLIC`, `AUTHENTICATED` y `RECEPTIONIST_ALLOWED` de
> [backend/tests/test_authorization.py](../backend/tests/test_authorization.py). Esas pruebas recorren
> **todos** los endpoints del esquema OpenAPI y fallan si:
> - un endpoint no público responde sin token,
> - un cliente puede usar un endpoint del personal,
> - la recepción puede usar un endpoint reservado al administrador.
>
> Si agregas un endpoint, clasifícalo en esas listas y en esta tabla.

Los permisos se asignan por rol en [backend/app/core/permissions.py](../backend/app/core/permissions.py).

| Nivel | Quién |
|---|---|
| **Público** | Cualquiera, sin token |
| **Sesión** | Cualquier usuario autenticado y activo |
| **Recepción** | `receptionist` y `admin` (permiso indicado) |
| **Admin** | Solo `admin` |

| Método | Ruta (`/api/v1`) | Nivel | Permiso / notas |
|---|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` | Público | Login con mensaje genérico; refresh por cookie HttpOnly rotativa |
| POST | `/auth/verify-email`, `/auth/forgot-password`, `/auth/reset-password` | Público | Tokens de un solo uso |
| POST | `/auth/resend-verification` | Sesión | |
| GET/PATCH/DELETE | `/users/me` | Sesión | DELETE desactiva la cuenta y cierra sus sesiones |
| POST | `/users/me/password` | Sesión | Cierra las demás sesiones |
| GET | `/users`, `/users/{id}` | Recepción | `users:read` |
| POST | `/users` | Recepción | `users:create`; crear personal exige `users:manage_staff` (admin) |
| PATCH | `/users/{id}`, `/users/{id}/status` | Recepción | `users:update`; editar personal o cambiar roles exige `users:manage_staff` (admin) |
| GET | `/room-types`, `/rooms`, `/rooms/{id}` | Público | `include_inactive=true` exige `rooms:read_all` |
| GET | `/rooms/{id}/booked-dates`, `/rooms/{id}/quote`, `/availability` | Público | |
| POST/PATCH | `/room-types[/{id}]` | Admin | `rooms:write` |
| POST/PATCH/DELETE | `/rooms[/{id}]`, `/rooms/{id}/images` | Admin | `rooms:write` |
| POST | `/bookings` | Público | Sesión opcional; precio calculado en el servidor; comprobante obligatorio |
| GET | `/bookings/mine` | Sesión | |
| GET | `/bookings/{id}`, `/bookings/{id}/receipt` | Sesión | Solo el dueño o el personal (404 para los demás) |
| POST | `/bookings/{id}/receipt` | Sesión | Dueño o `bookings:update` |
| GET | `/bookings` | Recepción | `bookings:read_all` |
| POST | `/bookings/manual` | Recepción | `bookings:create_manual`; precio negociado exige `bookings:override_price` (admin) |
| PATCH | `/bookings/{id}` | Recepción | `bookings:update`; precio negociado exige `bookings:override_price` (admin) |
| POST | `/bookings/{id}/status` | Recepción | `bookings:change_status` |
| GET | `/folios/by-booking/{id}` | Recepción | `folios:read` |
| POST/DELETE | `/folios/{id}/charges[/{charge_id}]` | Recepción | `folios:write` |
| GET | `/dashboard` | Recepción | `dashboard:read` |
| GET | `/gallery`, `/settings` | Público | |
| POST/DELETE | `/gallery[/{id}]` | Admin | `gallery:write` |
| PUT/POST | `/settings`, `/settings/logo` | Admin | `settings:write` |
| GET | `/audit-logs` | Admin | `audit:read` |
| GET/POST | `/notifications`, `/notifications/read-all` | Sesión | Solo las propias |

**Archivos:** `/static/uploads` es público y solo contiene fotos re-codificadas. Los comprobantes de pago
viven en `PRIVATE_UPLOAD_DIR` (por defecto `backend/private_uploads/`), que no se sirve como estático.
