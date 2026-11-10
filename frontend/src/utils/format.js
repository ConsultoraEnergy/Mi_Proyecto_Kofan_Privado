/**
 * Formato de fechas y moneda (7.8): la API envía ISO-8601 y aquí se presenta en la zona horaria
 * del hotel. Ningún componente debe sumar/restar horas a mano.
 */
import { DEFAULT_CURRENCY, HOTEL_TIMEZONE } from "@/config/env";

export function formatMoney(value, currency = DEFAULT_CURRENCY) {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency, maximumFractionDigits: 0 }).format(
    Number(value || 0),
  );
}

/** Fecha de calendario "2026-11-20" -> "20 nov 2026" (sin conversión de zona). */
export function formatDate(isoDate, options = { day: "2-digit", month: "short", year: "numeric" }) {
  if (!isoDate) return "";
  const [y, m, d] = String(isoDate).slice(0, 10).split("-").map(Number);
  return new Intl.DateTimeFormat("es-CO", { ...options, timeZone: "UTC" }).format(Date.UTC(y, m - 1, d));
}

/** Instante ISO ("2026-11-09T21:15:00Z") -> fecha y hora en la zona del hotel. */
export function formatDateTime(isoInstant) {
  if (!isoInstant) return "";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: HOTEL_TIMEZONE,
  }).format(new Date(isoInstant));
}

/** Date local (p. ej. de v-calendar) -> "YYYY-MM-DD" sin desfase de zona horaria. */
export function toIsoDate(date) {
  if (!date) return null;
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** "YYYY-MM-DD" -> Date local a medianoche (para calendarios). */
export function fromIsoDate(isoDate) {
  const [y, m, d] = String(isoDate).slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Noches entre dos fechas ISO (solo para mostrar; el precio real lo calcula el servidor). */
export function nightsBetween(checkIn, checkOut) {
  if (!checkIn || !checkOut) return 0;
  return Math.max(0, Math.round((fromIsoDate(checkOut) - fromIsoDate(checkIn)) / 86_400_000));
}
