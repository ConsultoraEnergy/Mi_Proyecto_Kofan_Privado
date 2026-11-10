import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  // CONFIGURACIÓN DEL PROXY (EL PUENTE)
  server: {
    // En desarrollo el frontend y la API comparten origen: así la cookie de sesión
    // (HttpOnly, SameSite=Lax) funciona igual que en producción detrás de un mismo dominio.
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/static": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return;
          }

          if (id.includes("html2pdf.js")) {
            return "pdf-tools";
          }

          if (id.includes("v-calendar") || id.includes("vuedraggable")) {
            return "booking-tools";
          }

          if (id.includes("@fortawesome")) {
            return "icons-vendor";
          }

          if (id.includes("sweetalert2") || id.includes("bootstrap")) {
            return "ui-vendor";
          }

          if (id.includes("vue") || id.includes("pinia") || id.includes("vue-router")) {
            return "vue-vendor";
          }
        },
      },
    },
  },
});
