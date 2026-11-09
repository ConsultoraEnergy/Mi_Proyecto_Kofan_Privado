import apiClient from "@/api/apiClient";

// --- Folios (cuenta del huésped; se abre en el check-in y se cierra en el check-out) ---
export const getFolioByBooking = (bookingId) =>
  apiClient.get(`/folios/by-booking/${bookingId}`).then((r) => r.data);
export const addFolioCharge = (folioId, description, amount) =>
  apiClient.post(`/folios/${folioId}/charges`, { description, amount }).then((r) => r.data);
export const removeFolioCharge = (folioId, chargeId) =>
  apiClient.delete(`/folios/${folioId}/charges/${chargeId}`).then((r) => r.data);

// --- Dashboard ---
export const getDashboard = () => apiClient.get("/dashboard").then((r) => r.data);

// --- Notificaciones del usuario: [{ id, title, message, theme, icon, read, created_at }] ---
export const listNotifications = () => apiClient.get("/notifications").then((r) => r.data);
export const markAllNotificationsRead = () => apiClient.post("/notifications/read-all").then((r) => r.data);

// --- Auditoría: { items: [{ entity, entity_id, entity_label, action, actor, changes, created_at }], total } ---
export const listAuditLogs = (params = {}) => apiClient.get("/audit-logs", { params }).then((r) => r.data);
