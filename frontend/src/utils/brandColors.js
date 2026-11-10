/**
 * Colores de marca definidos como variables CSS en styles/global.css (--k-*). SweetAlert2 necesita
 * el valor literal, así que se leen del documento; el respaldo aplica en pruebas o si falta la variable.
 */
export function brandColor(token, fallback) {
  if (typeof window === "undefined") return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback;
}

export const brandColors = () => ({
  apple: brandColor("--k-apple", "#8BCF5B"),
  forest: brandColor("--k-forest", "#0f3b2a"),
  danger: brandColor("--k-danger", "#e74c3c"),
});
