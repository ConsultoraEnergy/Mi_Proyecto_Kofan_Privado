# Nivel de acceso por endpoint

> Fuente de verdad: las listas `PUBLIC_ENDPOINTS` y `AUTHENTICATED_ENDPOINTS` de
> [testing/test_seguridad_fase0.py](../testing/test_seguridad_fase0.py).
> La prueba `test_todo_endpoint_no_publico_exige_autenticacion` recorre **todas** las rutas de la
> app y falla si alguna no listada como pública responde sin token; `test_endpoints_de_admin_rechazan_a_un_cliente`
> falla si un cliente puede usar un endpoint de administrador. Si agregas un endpoint público o de
> cliente, actualiza esas listas **y** esta tabla.

| Nivel | Significado |
|---|---|
| **Público** | Sin token. |
| **Autenticado** | Cualquier usuario con *access token* válido y cuenta activa (`is_active`). |
| **Admin** | Usuario autenticado con `role = admin`. Responde 401 sin token y 403 con otro rol. |

| Método | Ruta | Nivel | Notas |
|---|---|---|---|
| `POST` | `/auth/login` | Público | Mensaje de error genérico (no revela si el correo existe). |
| `POST` | `/register/` | Público | Contraseña obligatoria (≥ 8). Rol forzado a `client`. No vincula reservas por correo. |
| `GET` | `/users/me` | Autenticado | |
| `PATCH` | `/users/update-me` | Autenticado | |
| `PATCH` | `/users/delete-me` | Autenticado | Desactiva la cuenta: el token deja de funcionar. |
| `GET` | `/users/` | Admin | |
| `POST` | `/users/` | Admin | |
| `PATCH` | `/users/{user_id}` | Admin | No devuelve el hash de la contraseña. |
| `PATCH` | `/users/{user_id}/toggle-status` | Admin | Suspender = pierde acceso de inmediato. |
| `POST` | `/api/reservas/` | Autenticado | Precio calculado en el servidor. Comprobante obligatorio. |
| `POST` | `/api/reservas/invitado` | Público | Precio calculado en el servidor. Comprobante obligatorio. |
| `POST` | `/api/reservas/admin` | Admin | Reserva manual (JSON). Queda `confirmada`. `monto_total` opcional = precio negociado. |
| `GET` | `/api/reservas/{reserva_id}/comprobante` | Autenticado | Solo admin o dueño de la reserva (404 para los demás). |
| `GET` | `/api/reservas/mis-reservas` | Autenticado | |
| `GET` | `/api/reservas/admin/todas` | Admin | |
| `PATCH` | `/api/reservas/{reserva_id}/estado` | Admin | |
| `PUT` | `/api/reservas/{reserva_id}/detalles` | Admin | |
| `GET` | `/api/notificaciones/mis-avisos` | Autenticado | |
| `PATCH` | `/api/notificaciones/read-all` | Autenticado | |
| `GET` | `/rooms/public` | Público | |
| `GET` | `/rooms/public/{room_id}` | Público | |
| `GET` | `/rooms/` | Público | Incluye habitaciones inactivas. Revisar en Fase 1 si debe ser solo admin. |
| `GET` | `/rooms/{room_id}` | Público | |
| `GET` | `/rooms/{room_id}/booked-dates` | Público | Solo fechas, sin datos del huésped. |
| `POST` | `/rooms/` | Admin | |
| `PUT` | `/rooms/{room_id}` | Admin | |
| `DELETE` | `/rooms/{room_id}` | Admin | |
| `POST` | `/rooms/create-with-images` | Admin | Antes bastaba con estar autenticado (5.2). |
| `DELETE` | `/rooms/{room_id}/delete-image` | Admin | |
| `POST` | `/rooms/{room_id}/add-images` | Admin | |
| `GET` | `/rooms/logs/history` | Admin | |
| `GET` | `/config` | Público | |
| `PUT` | `/config` | Admin | |
| `POST` | `/config/logo` | Admin | |
| `GET` | `/gallery/` | Público | |
| `POST` | `/gallery/` | Admin | |
| `DELETE` | `/gallery/{image_id}` | Admin | |
| `GET` | `/invoices/by-booking/{booking_id}` | Admin | Antes era público (5.1). |
| `POST` | `/invoices/` | Admin | Antes era público (5.1). |
| `PUT` | `/invoices/{invoice_id}/extra-charges` | Admin | Antes era público (5.1). |
| `PUT` | `/invoices/sync-by-booking/{booking_id}` | Admin | Antes era público (5.1). |
| `PUT` | `/invoices/close-by-booking/{booking_id}` | Admin | Antes era público (5.1). |
| `GET` | `/dashboard` | Admin | |
| `GET` | `/reports/earnings` | Admin | Placeholder (lanza `KeyError`, ver 6.6). |
| `GET` | `/busqueda/disponibilidad` | Público | |

**Archivos estáticos:** `/static/uploads` y `/static/images` son públicos y solo contienen fotos
(re-codificadas). Los comprobantes de pago viven en `backend/private_uploads/` (o `PRIVATE_UPLOAD_DIR`),
que **no** se sirve como estático.
