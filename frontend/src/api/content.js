import apiClient from "@/api/apiClient";

// --- Ajustes del sitio (marca, contacto, instrucciones de pago, textos institucionales) ---
export const getSiteSettings = () => apiClient.get("/settings").then((r) => r.data);
export const updateSiteSettings = (payload) => apiClient.put("/settings", payload).then((r) => r.data);
export function uploadLogo(file) {
  const form = new FormData();
  form.append("file", file);
  return apiClient.post("/settings/logo", form).then((r) => r.data);
}

// --- Galería: [{ id, url, title, category, created_at }] ---
export const listGallery = (category = null) =>
  apiClient
    .get("/gallery", { params: category && category !== "all" ? { category } : {} })
    .then((r) => r.data);

export function uploadGalleryImage(file, category = "general", title = "") {
  const form = new FormData();
  form.append("file", file);
  form.append("category", category);
  form.append("title", title);
  return apiClient.post("/gallery", form).then((r) => r.data);
}
export const deleteGalleryImage = (id) => apiClient.delete(`/gallery/${id}`);
