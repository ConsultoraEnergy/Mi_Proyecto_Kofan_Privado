import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

vi.mock("@/api/auth", () => ({
  login: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}));

import * as authApi from "@/api/auth";
import apiClient, { configureAuth } from "@/api/apiClient";
import { useAuthStore } from "@/stores/auth";

const staff = { id: "1", role: "receptionist", permissions: ["bookings:read_all"], full_name: "Recepción" };

describe("store de auth", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("restaura la sesión desde la cookie y nunca usa localStorage", async () => {
    localStorage.setItem("token", "viejo");
    localStorage.setItem("userData", JSON.stringify({ role: "admin" }));
    authApi.refresh.mockResolvedValue({ access_token: "nuevo", user: staff });

    const auth = useAuthStore();
    await auth.init();

    expect(auth.isLogged).toBe(true);
    expect(auth.isStaff).toBe(true);
    expect(auth.isAdmin).toBe(false);
    expect(auth.can("bookings:read_all")).toBe(true);
    expect(auth.can("rooms:write")).toBe(false);
    expect(localStorage.getItem("token")).toBeNull(); // se limpian restos de la versión anterior
    expect(localStorage.getItem("userData")).toBeNull();
  });

  it("init se ejecuta una sola vez y tolera no tener sesión", async () => {
    authApi.refresh.mockRejectedValue(new Error("401"));
    const auth = useAuthStore();
    await Promise.all([auth.init(), auth.init()]);
    expect(authApi.refresh).toHaveBeenCalledTimes(1);
    expect(auth.isLogged).toBe(false);
    expect(auth.initialized).toBe(true);
  });

  it("logout limpia la sesión aunque falle la petición", async () => {
    authApi.login.mockResolvedValue({ access_token: "t", user: staff });
    authApi.logout.mockRejectedValue(new Error("sin red"));
    const auth = useAuthStore();
    await auth.login("a@b.com", "x");
    await expect(auth.logout()).rejects.toThrow();
    expect(auth.isLogged).toBe(false);
  });
});

describe("apiClient", () => {
  it("ante un 401 renueva la sesión una sola vez y reintenta las peticiones en cola", async () => {
    let token = "expirado";
    const refreshSession = vi.fn(async () => {
      token = "renovado";
      return token;
    });
    configureAuth({ getAccessToken: () => token, refreshSession, onSessionExpired: vi.fn() });

    const seen = [];
    const adapter = async (config) => {
      seen.push(config.headers.Authorization);
      if (config.headers.Authorization === "Bearer expirado") {
        const error = new Error("401");
        error.config = config;
        error.response = { status: 401, data: {} };
        throw error;
      }
      return { data: { ok: true }, status: 200, statusText: "OK", headers: {}, config };
    };

    const [a, b] = await Promise.all([
      apiClient.get("/users/me", { adapter }),
      apiClient.get("/bookings/mine", { adapter }),
    ]);

    expect(a.data.ok && b.data.ok).toBe(true);
    expect(refreshSession).toHaveBeenCalledTimes(1);
    expect(seen.filter((h) => h === "Bearer renovado")).toHaveLength(2);
  });

  it("si la renovación falla, notifica la expiración de la sesión", async () => {
    const onSessionExpired = vi.fn();
    configureAuth({ getAccessToken: () => "x", refreshSession: async () => null, onSessionExpired });
    const adapter = async (config) => {
      const error = new Error("401");
      error.config = config;
      error.response = { status: 401, data: {} };
      throw error;
    };
    await expect(apiClient.get("/users/me", { adapter })).rejects.toThrow();
    expect(onSessionExpired).toHaveBeenCalledTimes(1);
  });
});
