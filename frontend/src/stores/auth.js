/**
 * Sesión del usuario.
 *
 * Al cargar la app se llama a `init()`: si el navegador tiene la cookie de sesión (HttpOnly),
 * se obtiene un access token nuevo y el perfil real desde el backend. El rol y los permisos
 * NUNCA se leen de localStorage (9.2): la seguridad real la aplica el backend.
 */
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { configureAuth } from "@/api/apiClient";
import * as authApi from "@/api/auth";

const STAFF_ROLES = ["admin", "receptionist"];
const LEGACY_KEYS = ["token", "token_type", "refresh_token", "userData"];

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const accessToken = ref(null);
  const initialized = ref(false);
  let initPromise = null;

  const isLogged = computed(() => !!accessToken.value && !!user.value);
  const role = computed(() => user.value?.role || null);
  const isAdmin = computed(() => role.value === "admin");
  const isStaff = computed(() => STAFF_ROLES.includes(role.value));
  const permissions = computed(() => new Set(user.value?.permissions || []));

  function can(permission) {
    return permissions.value.has(permission);
  }

  function setSession({ access_token, user: profile }) {
    accessToken.value = access_token;
    user.value = profile;
  }

  function clear() {
    accessToken.value = null;
    user.value = null;
  }

  async function refresh() {
    try {
      setSession(await authApi.refresh());
      return accessToken.value;
    } catch {
      clear();
      return null;
    }
  }

  /** Restaura la sesión al cargar la app (una sola vez). */
  function init() {
    if (!initPromise) {
      LEGACY_KEYS.forEach((k) => localStorage.removeItem(k)); // restos de la versión anterior
      initPromise = refresh().finally(() => {
        initialized.value = true;
      });
    }
    return initPromise;
  }

  async function login(email, password) {
    setSession(await authApi.login(email, password));
    return user.value;
  }

  async function logout() {
    try {
      await authApi.logout();
    } finally {
      clear();
    }
  }

  function updateUser(profile) {
    user.value = { ...user.value, ...profile };
  }

  /** Ruta de inicio según el rol. */
  function homeRoute() {
    return isStaff.value ? { name: "admin-dashboard" } : { name: "account-profile" };
  }

  return {
    user,
    accessToken,
    initialized,
    isLogged,
    role,
    isAdmin,
    isStaff,
    permissions,
    can,
    init,
    login,
    logout,
    refresh,
    clear,
    updateUser,
    homeRoute,
  };
});

/** Conecta el store con el cliente HTTP (se llama una vez al iniciar la app). */
export function wireAuthToApiClient(store, router) {
  configureAuth({
    getAccessToken: () => store.accessToken,
    refreshSession: () => store.refresh(),
    onSessionExpired: () => {
      store.clear();
      const current = router.currentRoute.value;
      if (current.matched.some((r) => r.meta.requiresAuth)) {
        router.push({ name: "login", query: { redirect: current.fullPath } });
      }
    },
  });
}
