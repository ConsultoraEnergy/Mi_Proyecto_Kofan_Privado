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

// Fotos subidas por el backend: <base>/<uuid de 32 hex>.<ext>. Su miniatura es <base>/thumbs/<uuid>.webp
const STORED_IMAGE_RE = /^(.*\/)([0-9a-f]{32})\.(jpg|png|webp)$/i;

/**
 * Miniatura WebP de una foto subida (para tarjetas y cuadrículas). Las demás URL se devuelven
 * tal cual. Úsala junto con `fallbackToFullImage` en @error, por si la miniatura no existe.
 */
export function thumbUrl(path) {
  const full = assetUrl(path);
  const match = full.match(STORED_IMAGE_RE);
  return match ? `${match[1]}thumbs/${match[2]}.webp` : full;
}

/**
 * Manejador de @error para <img :src="thumbUrl(x)">: cambia a la foto original una sola vez.
 * Devuelve false si ya estaba mostrando la original, para encadenar otro manejador con `||`.
 */
export function fallbackToFullImage(event, path) {
  const img = event?.target;
  const full = assetUrl(path);
  if (!img || !full) return false;
  const absolute = new URL(full, window.location.href).href;
  if (img.src === absolute) return false;
  img.src = absolute;
  return true;
}
