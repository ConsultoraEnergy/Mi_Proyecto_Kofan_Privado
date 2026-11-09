import apiClient from "@/api/apiClient";

// --- Autoservicio ---
export const getMe = () => apiClient.get("/users/me").then((r) => r.data);
export const updateMe = (payload) => apiClient.patch("/users/me", payload).then((r) => r.data);
export const changePassword = (currentPassword, newPassword) =>
  apiClient.post("/users/me/password", { current_password: currentPassword, new_password: newPassword });
export const deactivateMe = () => apiClient.delete("/users/me");

// --- Personal (admin / recepción) ---
/** params: { q, role, page, limit } -> { items, total, page, limit } */
export const listUsers = (params = {}) => apiClient.get("/users", { params }).then((r) => r.data);
export const getUser = (id) => apiClient.get(`/users/${id}`).then((r) => r.data);
/** El usuario creado recibe un correo para definir su contraseña (no hay contraseña por defecto). */
export const createUser = (payload) => apiClient.post("/users", payload).then((r) => r.data);
export const updateUser = (id, payload) => apiClient.patch(`/users/${id}`, payload).then((r) => r.data);
export const setUserStatus = (id, isActive) =>
  apiClient.patch(`/users/${id}/status`, { is_active: isActive }).then((r) => r.data);
