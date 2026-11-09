import apiClient from "@/api/apiClient";

/**
 * Reserva web (invitado o con sesión). El precio lo calcula el servidor.
 * data: { room_id, check_in, check_out, full_name, email, phone, document_type?, document_number?,
 *         notes?, accept_privacy_policy }
 * receipt: File (JPEG, PNG, WebP o PDF)
 */
export function createWebBooking(data, receipt) {
  const form = new FormData();
  Object.entries(data).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") form.append(key, value);
  });
  form.append("receipt", receipt);
  return apiClient.post("/bookings", form).then((r) => r.data);
}

/** Reserva registrada por el personal (queda confirmada).
 * payload: { room_id, check_in, check_out, guest: {full_name, email, phone?, document_type?, document_number?},
 *            companions?, notes?, total_amount? (solo admin: precio negociado) } */
export const createManualBooking = (payload) => apiClient.post("/bookings/manual", payload).then((r) => r.data);

/** params: { status: "a,b", q, page, limit } -> { items, total, page, limit, summary } */
export const listBookings = (params = {}) => apiClient.get("/bookings", { params }).then((r) => r.data);
export const myBookings = () => apiClient.get("/bookings/mine").then((r) => r.data);
export const getBooking = (id) => apiClient.get(`/bookings/${id}`).then((r) => r.data);
/** payload: { check_in?, check_out?, guest?, companions?, notes?, total_amount? } */
export const updateBooking = (id, payload) => apiClient.patch(`/bookings/${id}`, payload).then((r) => r.data);
export const changeBookingStatus = (id, status, reason = null) =>
  apiClient.post(`/bookings/${id}/status`, { status, reason }).then((r) => r.data);

export function uploadReceipt(id, file) {
  const form = new FormData();
  form.append("receipt", file);
  return apiClient.post(`/bookings/${id}/receipt`, form).then((r) => r.data);
}

/**
 * Abre el comprobante privado en una pestaña nueva. `receiptUrl` es el campo receipt_url de la
 * reserva: se descarga con el token (no es un enlace público) y se muestra como archivo local.
 * Llamar directamente desde el manejador del clic para que el navegador no bloquee la pestaña.
 */
export async function openReceipt(receiptUrl) {
  const win = window.open("", "_blank");
  try {
    const { data } = await apiClient.get(receiptUrl, { responseType: "blob" });
    const objectUrl = URL.createObjectURL(data);
    if (win) win.location.href = objectUrl;
    else window.open(objectUrl, "_blank");
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  } catch (error) {
    win?.close();
    throw error;
  }
}
