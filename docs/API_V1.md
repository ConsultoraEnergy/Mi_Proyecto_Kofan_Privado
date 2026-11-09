# API v1 de Hotel Kawari

Base: `/api/v1`. Documentación interactiva (solo fuera de producción): `/docs`.
Todos los errores responden `{"detail": "<mensaje en español>", "code": "<código>"}`; los errores de
validación de FastAPI (422) responden `{"detail": [{loc, msg, ...}]}`.

Fechas de calendario (`check_in`, `check_out`) = `"YYYY-MM-DD"`. Instantes (`created_at`...) = ISO-8601 UTC.
Montos = número en la moneda del hotel (COP por defecto). El precio de las reservas **siempre** lo calcula el servidor.

## Autenticación

- `POST /auth/login` (form `username`, `password`) → `{access_token, token_type, expires_in, user}` y cookie
  HttpOnly `kawari_refresh` (path `/api/v1/auth`). El access token dura 15 min y se guarda **solo en memoria**.
- `POST /auth/refresh` (usa la cookie) → mismo cuerpo que login; rota la cookie. 401 si la sesión no es válida.
- `POST /auth/logout` → 204; invalida la sesión y borra la cookie.
- Peticiones autenticadas: cabecera `Authorization: Bearer <access_token>`.

`user` (UserOut): `{id, email, email_verified, full_name, person_type, document_type, document_number, phone,
country, city, role: "admin"|"receptionist"|"client", is_active, permissions: string[], created_at}`.

## Endpoints

| Método | Ruta | Acceso | Cuerpo / parámetros → respuesta |
|---|---|---|---|
| POST | /auth/register | Público | `{email, password(≥8), full_name, person_type? ("natural"\|"legal"), document_type, document_number, phone?, country?, city?, accept_privacy_policy: true}` → UserOut (envía correo de verificación) |
| POST | /auth/verify-email | Público | `{token}` → `{message, linked_bookings}` |
| POST | /auth/resend-verification | Sesión | → 202 |
| POST | /auth/forgot-password | Público | `{email}` → 202 (misma respuesta exista o no el correo) |
| POST | /auth/reset-password | Público | `{token, password}` → `{message}`; sirve también para "definir contraseña" de cuentas creadas por recepción |
| GET/PATCH/DELETE | /users/me | Sesión | PATCH `{full_name?, phone?, country?, city?}`; DELETE desactiva la cuenta |
| POST | /users/me/password | Sesión | `{current_password, new_password}` → 204 |
| GET | /users | users:read | `?q&role&page&limit` → `{items: UserOut[], total, page, limit}` |
| POST | /users | users:create | `{email, full_name, role?, person_type?, document_type?, document_number?, phone?, country?, city?}` → UserOut. El usuario recibe un enlace para definir su contraseña |
| GET/PATCH | /users/{id} | users:read / users:update | PATCH `{full_name?, phone?, country?, city?, person_type?, document_type?, document_number?, role?}` |
| PATCH | /users/{id}/status | users:update | `{is_active}` |
| GET | /room-types | Público | `?include_inactive` (personal) → `[{id, code, name, description, is_active, sort_order}]` |
| POST/PATCH | /room-types[/{id}] | rooms:write | `{code, name, description?, is_active?, sort_order?}` |
| GET | /availability | Público | `?room_type=<code>&check_in&check_out&guests` → `{room: RoomOut, quote: QuoteOut}`; 404 `no_availability` |
| GET | /rooms | Público | `?room_type&q&include_inactive(personal)&page&limit` → `{items: RoomOut[], total, page, limit}` |
| POST | /rooms | rooms:write | JSON `{number, name, room_type_id, description?, price_per_night, capacity, bedrooms?, beds?, amenities[]?, is_active?, operational_status?}` → RoomOut. Las fotos se suben después |
| GET/PATCH/DELETE | /rooms/{id} | Público / rooms:write | PATCH acepta los mismos campos (todos opcionales) + `main_image`. DELETE → 409 si tiene reservas (desactivar en su lugar) |
| POST | /rooms/{id}/images | rooms:write | multipart `files[]` → RoomOut |
| DELETE | /rooms/{id}/images | rooms:write | `?url=` → RoomOut |
| GET | /rooms/{id}/booked-dates | Público | → `[{check_in, check_out}]` (el día de salida queda libre) |
| GET | /rooms/{id}/quote | Público | `?check_in&check_out` → QuoteOut |
| POST | /bookings | Público (sesión opcional) | multipart: `room_id, check_in, check_out, full_name, email, phone, document_type?, document_number?, notes?, accept_privacy_policy=true, receipt(file)` → BookingOut (estado `pending_verification`) |
| POST | /bookings/manual | bookings:create_manual | `{room_id, check_in, check_out, guest: {full_name, email, phone?, document_type?, document_number?}, companions?, notes?, total_amount?}` → BookingDetailOut (estado `confirmed`). `total_amount` requiere bookings:override_price (solo admin) |
| GET | /bookings | bookings:read_all | `?status=a,b&q&page&limit` → `{items: BookingDetailOut[], total, page, limit, summary: {pending_verification, pending_payment}}` |
| GET | /bookings/mine | Sesión | → BookingOut[] |
| GET | /bookings/{id} | Dueño o personal | → BookingOut / BookingDetailOut |
| PATCH | /bookings/{id} | bookings:update | `{check_in?, check_out?, guest?, companions?, notes?, total_amount?}`; valida disponibilidad (409) y recalcula el precio |
| POST | /bookings/{id}/status | bookings:change_status | `{status, reason?}`; `reason` obligatorio al cancelar o rechazar comprobante. 409 `invalid_transition` |
| GET | /bookings/{id}/receipt | Dueño o bookings:view_receipts | Archivo del comprobante (privado) |
| POST | /bookings/{id}/receipt | Dueño o bookings:update | multipart `receipt` → BookingOut (pasa a `pending_verification`) |
| GET | /folios/by-booking/{booking_id} | folios:read | → FolioOut (404 si aún no hubo check-in) |
| POST | /folios/{id}/charges | folios:write | `{description, amount}` → FolioOut |
| DELETE | /folios/{id}/charges/{charge_id} | folios:write | → FolioOut |
| GET | /gallery | Público | `?category` → `[{id, url, title, category, created_at}]` |
| POST | /gallery | gallery:write | multipart `file, category, title` |
| DELETE | /gallery/{id} | gallery:write | 204 |
| GET | /settings | Público | → SiteSettings (+ `logo_url`, `deposit_percent`) |
| PUT | /settings | settings:write | SiteSettings completo |
| POST | /settings/logo | settings:write | multipart `file` |
| GET | /dashboard | dashboard:read | → `{today, stats: {month_revenue, confirmed_bookings, pending_verification, in_house_guests, arrivals_today, departures_today, occupancy_percent, occupied_rooms, sellable_rooms}, popular_rooms: [{room_id, name, bookings}], recent_activity: [{booking_id, code, guest_name, room_name, status, total_amount, at}]}` |
| GET | /notifications | Sesión | → `[{id, title, message, theme, icon, read, created_at}]` |
| POST | /notifications/read-all | Sesión | → `{updated}` |
| GET | /audit-logs | audit:read | `?entity=room|booking|user|...&entity_id&page&limit` → `{items: [{id, entity, entity_id, entity_label, action, actor, changes: [{field, old, new}], created_at}], total, page, limit}` |

## Modelos

**RoomOut**: `{id, number, name, room_type: {id, code, name, ...} | null, description, price_per_night, capacity,
bedrooms, beds, amenities[], images[], main_image, is_active, operational_status: "available"|"cleaning"|"maintenance"|"out_of_service", created_at, updated_at}`.
Las imágenes son rutas relativas (`/static/uploads/...`): usar `assetUrl()` del frontend.

**QuoteOut**: `{room_id, check_in, check_out, nights, price_per_night, total_amount, deposit_percent, deposit_amount, currency}`.

**BookingOut**: `{id, code, room: {id, number, name}, user_id, guest: {full_name, email, phone, document_type, document_number},
companions: [{full_name, document_type, document_number, relationship}], check_in, check_out, nights, price_per_night,
calculated_amount, total_amount, deposit_percent, deposit_amount, status, payment_due_at, has_receipt, receipt_url,
notes, status_reason, source: "web"|"manual", created_at, updated_at}`.
**BookingDetailOut** (personal) añade `created_by` y `status_history: [{from_status, to_status, at, by, reason}]`.

**FolioOut**: `{id, number, booking_id, booking_code, guest_name, guest_email, guest_document, guest_phone, room_number,
room_name, check_in, check_out, nights, room_subtotal, charges: [{id, description, amount, created_at, created_by}],
total_amount, status: "open"|"closed", opened_at, closed_at}`.

**SiteSettings**: `{hotel_name, tagline, contact_email, phone, whatsapp_number, address, city, country, check_in_time,
check_out_time, currency, tax_percentage, social_facebook, social_instagram, social_tiktok, payment_instructions,
about_description, mission, vision}`.

## Estados de reserva

```
pending_verification ──aprobar──▶ confirmed ──check-in──▶ checked_in ──check-out──▶ checked_out
   │  ▲  (rechazar comprobante, con motivo)        │
   ▼  │  (nuevo comprobante)                       │
pending_payment ── vence el plazo (48 h) ──▶ cancelled ◀── (con motivo)
```

- El check-in abre el folio; el check-out lo cierra. Cancelar libera las fechas.
- Las reservas con comprobante por verificar **nunca** se cancelan automáticamente.
