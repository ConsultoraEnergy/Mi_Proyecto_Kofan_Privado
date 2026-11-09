/** Galería pública: [{ id, url, title, category, created_at }]. Las URL se muestran con assetUrl(). */
import { defineStore } from "pinia";
import { errorMessage } from "@/api/apiClient";
import { listGallery, uploadGalleryImage, deleteGalleryImage } from "@/api/content";

export const useGalleryStore = defineStore("gallery", {
  state: () => ({
    images: [],
    isLoading: false,
    error: null,
  }),
  actions: {
    async fetchImages(category = null) {
      this.isLoading = true;
      this.error = null;
      try {
        this.images = await listGallery(category);
      } catch (error) {
        this.error = errorMessage(error, "Error al cargar la galería.");
      } finally {
        this.isLoading = false;
      }
    },

    /** category: slug en minúscula (p. ej. "instalaciones"). */
    async uploadImage(file, category = "general", title = "") {
      try {
        const image = await uploadGalleryImage(file, category, title);
        this.images.unshift(image);
        return { success: true };
      } catch (error) {
        return { success: false, error: errorMessage(error, "Error al subir") };
      }
    },

    async deleteImage(imageId) {
      try {
        await deleteGalleryImage(imageId);
        this.images = this.images.filter((img) => img.id !== imageId);
        return { success: true };
      } catch (error) {
        return { success: false, error: errorMessage(error, "Error al eliminar") };
      }
    },
  },
});
