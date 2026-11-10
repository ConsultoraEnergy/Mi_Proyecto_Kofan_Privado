/** Estados de reserva del backend y su presentación en español. */
export const BOOKING_STATUS = Object.freeze({
  PENDING_PAYMENT: "pending_payment",
  PENDING_VERIFICATION: "pending_verification",
  CONFIRMED: "confirmed",
  CHECKED_IN: "checked_in",
  CHECKED_OUT: "checked_out",
  CANCELLED: "cancelled",
});

export const BOOKING_STATUS_META = Object.freeze({
  pending_payment: { label: "Pendiente de pago", badge: "bg-warning text-dark", icon: "fa-solid fa-clock" },
  pending_verification: {
    label: "Pago por verificar",
    badge: "bg-info text-dark",
    icon: "fa-solid fa-receipt",
  },
  confirmed: { label: "Confirmada", badge: "bg-success", icon: "fa-solid fa-circle-check" },
  checked_in: { label: "Huésped en el hotel", badge: "bg-primary", icon: "fa-solid fa-door-open" },
  checked_out: { label: "Finalizada", badge: "bg-secondary", icon: "fa-solid fa-check" },
  cancelled: { label: "Cancelada", badge: "bg-danger", icon: "fa-solid fa-ban" },
});

/** Transiciones permitidas (espejo de backend/app/modules/bookings/state_machine.py). */
export const BOOKING_TRANSITIONS = Object.freeze({
  pending_payment: ["pending_verification", "confirmed", "cancelled"],
  pending_verification: ["confirmed", "pending_payment", "cancelled"],
  confirmed: ["checked_in", "cancelled"],
  checked_in: ["checked_out"],
  checked_out: [],
  cancelled: [],
});

/** Transiciones que exigen motivo (cancelar y rechazar comprobante). */
export const requiresReason = (from, to) =>
  to === BOOKING_STATUS.CANCELLED ||
  (from === BOOKING_STATUS.PENDING_VERIFICATION && to === BOOKING_STATUS.PENDING_PAYMENT);

export const statusLabel = (status) => BOOKING_STATUS_META[status]?.label || status;
export const canTransition = (from, to) => (BOOKING_TRANSITIONS[from] || []).includes(to);

export const DOCUMENT_TYPES = [
  { value: "CC", label: "Cédula de ciudadanía" },
  { value: "CE", label: "Cédula de extranjería" },
  { value: "PASSPORT", label: "Pasaporte" },
  { value: "NIT", label: "NIT" },
  { value: "TI", label: "Tarjeta de identidad" },
];

export const ROLE_LABELS = Object.freeze({
  admin: "Administrador",
  receptionist: "Recepción",
  client: "Cliente",
});

/** Permisos del backend (backend/app/core/permissions.py) usados para mostrar/ocultar la UI. */
export const PERMISSIONS = Object.freeze({
  USERS_READ: "users:read",
  USERS_CREATE: "users:create",
  USERS_UPDATE: "users:update",
  USERS_MANAGE_STAFF: "users:manage_staff",
  ROOMS_READ_ALL: "rooms:read_all",
  ROOMS_WRITE: "rooms:write",
  BOOKINGS_READ_ALL: "bookings:read_all",
  BOOKINGS_CREATE_MANUAL: "bookings:create_manual",
  BOOKINGS_UPDATE: "bookings:update",
  BOOKINGS_CHANGE_STATUS: "bookings:change_status",
  BOOKINGS_OVERRIDE_PRICE: "bookings:override_price",
  BOOKINGS_VIEW_RECEIPTS: "bookings:view_receipts",
  FOLIOS_READ: "folios:read",
  FOLIOS_WRITE: "folios:write",
  GALLERY_WRITE: "gallery:write",
  SETTINGS_WRITE: "settings:write",
  DASHBOARD_READ: "dashboard:read",
  AUDIT_READ: "audit:read",
});
