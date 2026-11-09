/**
 * Configuración de entorno del frontend (9.1). ÚNICO lugar que lee import.meta.env.
 *
 * VITE_API_URL: origen del backend (p. ej. https://api.kawari.com). Vacío = mismo origen
 * (en desarrollo, Vite hace de proxy de /api y /static hacia el backend).
 */
const rawOrigin = (import.meta.env.VITE_API_URL || "").trim().replace(/\/+$/, "");

export const API_ORIGIN = rawOrigin;
export const API_BASE_URL = `${rawOrigin}/api/v1`;
export const HOTEL_TIMEZONE = import.meta.env.VITE_HOTEL_TIMEZONE || "America/Bogota";
export const DEFAULT_CURRENCY = import.meta.env.VITE_CURRENCY || "COP";

/**
 * URL absoluta de un archivo servido por el backend (fotos, logo).
 * Acepta rutas relativas ("/static/uploads/x.webp") o URLs completas.
 */
export function assetUrl(path) {
  if (!path) return "";
  if (/^(https?:|data:|blob:)/i.test(path)) return path;
  return `${API_ORIGIN}${path.startsWith("/") ? "" : "/"}${path}`;
}
