/**
 * Cliente HTTP único (9.2).
 *
 * - El access token vive SOLO en memoria (store de auth), nunca en localStorage.
 * - El refresh token es una cookie HttpOnly que el navegador envía a /api/v1/auth/*.
 * - Ante un 401, intenta renovar la sesión UNA vez y reintenta la petición; las peticiones que
 *   fallan mientras se renueva esperan en cola y se reintentan con el nuevo token.
 */
import axios from "axios";
import { API_BASE_URL } from "@/config/env";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

// Se inyectan desde el store de auth (evita una dependencia circular).
let getAccessToken = () => null;
let refreshSession = async () => null;
let onSessionExpired = () => {};

export function configureAuth(handlers) {
  getAccessToken = handlers.getAccessToken;
  refreshSession = handlers.refreshSession;
  onSessionExpired = handlers.onSessionExpired;
}

const NO_REFRESH_URLS = ["/auth/login", "/auth/refresh", "/auth/logout", "/auth/register"];

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const skip = !original || original._retried || NO_REFRESH_URLS.some((u) => original.url?.startsWith(u));

    if (status !== 401 || skip) {
      return Promise.reject(error);
    }

    original._retried = true;
    try {
      // Una sola renovación en curso; las demás peticiones la esperan.
      refreshPromise = refreshPromise || refreshSession();
      const token = await refreshPromise;
      if (!token) throw error;
      original.headers.Authorization = `Bearer ${token}`;
      return apiClient(original);
    } catch (refreshError) {
      onSessionExpired();
      return Promise.reject(error);
    } finally {
      refreshPromise = null;
    }
  },
);

/** Mensaje legible de un error del backend ({detail: string} o errores de validación 422). */
export function errorMessage(error, fallback = "Ocurrió un error inesperado. Intenta de nuevo.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0];
    const field = first.loc?.[first.loc.length - 1];
    return field ? `Revisa el campo "${field}": ${first.msg}` : first.msg;
  }
  if (!error?.response) return "No hay conexión con el servidor.";
  return fallback;
}

export default apiClient;
