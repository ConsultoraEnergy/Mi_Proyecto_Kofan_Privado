import apiClient from "@/api/apiClient";

// --- Tipos de habitación: [{ id, code, name, description, is_active, sort_order }] ---
export const listRoomTypes = (includeInactive = false) =>
  apiClient
    .get("/room-types", { params: includeInactive ? { include_inactive: true } : {} })
    .then((r) => r.data);
export const createRoomType = (payload) => apiClient.post("/room-types", payload).then((r) => r.data);
export const updateRoomType = (id, payload) =>
  apiClient.patch(`/room-types/${id}`, payload).then((r) => r.data);

// --- Habitaciones ---
/** params: { room_type, q, include_inactive, page, limit } -> { items, total, page, limit } */
export const listRooms = (params = {}) => apiClient.get("/rooms", { params }).then((r) => r.data);
export const getRoom = (id) => apiClient.get(`/rooms/${id}`).then((r) => r.data);
export const createRoom = (payload) => apiClient.post("/rooms", payload).then((r) => r.data);
export const updateRoom = (id, payload) => apiClient.patch(`/rooms/${id}`, payload).then((r) => r.data);
export const deleteRoom = (id) => apiClient.delete(`/rooms/${id}`);

export function addRoomImages(id, files) {
  const form = new FormData();
  [...files].forEach((file) => form.append("files", file));
  return apiClient.post(`/rooms/${id}/images`, form).then((r) => r.data);
}
export const removeRoomImage = (id, url) =>
  apiClient.delete(`/rooms/${id}/images`, { params: { url } }).then((r) => r.data);

// --- Públicos ---
/** [{ check_in, check_out }]. El día de salida queda libre (intervalo semiabierto). */
export const getBookedDates = (id) => apiClient.get(`/rooms/${id}/booked-dates`).then((r) => r.data);

/** Precio calculado por el servidor: { nights, price_per_night, total_amount, deposit_percent, deposit_amount, currency } */
export const getQuote = (id, checkIn, checkOut) =>
  apiClient
    .get(`/rooms/${id}/quote`, { params: { check_in: checkIn, check_out: checkOut } })
    .then((r) => r.data);

/** { room, quote } o error 404 (code "no_availability") si no hay habitación libre. */
export const findAvailability = ({ roomType, checkIn, checkOut, guests }) =>
  apiClient
    .get("/availability", { params: { room_type: roomType, check_in: checkIn, check_out: checkOut, guests } })
    .then((r) => r.data);
