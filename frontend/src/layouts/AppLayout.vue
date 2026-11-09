<script setup>
import { ref } from "vue";
import Swal from "sweetalert2";
import Sidebar from "@/views/app/SidebarView.vue";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { resendVerification } from "@/api/auth";
import { errorMessage } from "@/api/apiClient";

const auth = useAuthStore();
useConfigStore().fetchSiteConfig();

const sending = ref(false);

const reenviarVerificacion = async () => {
  sending.value = true;
  try {
    const result = await resendVerification();
    Swal.fire({
      icon: "success",
      title: "Enlace enviado",
      text: result?.message || "Te enviamos un nuevo enlace de verificación.",
      timer: 3000,
      showConfirmButton: false,
    });
  } catch (error) {
    Swal.fire("No se pudo enviar", errorMessage(error), "error");
  } finally {
    sending.value = false;
  }
};
</script>

<template>
  <div class="app-layout">
    <div class="container-fluid mt-5 pt-5">
      <div class="row">
        <aside class="col-12 col-lg-3 bd-sidebar mb-4">
          <Sidebar />
        </aside>

        <main class="col-12 col-lg-9">
          <div
            v-if="auth.user && !auth.user.email_verified"
            class="alert alert-warning d-flex flex-wrap align-items-center gap-3 rounded-4 shadow-sm"
            role="alert"
          >
            <font-awesome-icon icon="fa-solid fa-envelope" class="fs-4" />
            <div class="flex-grow-1 small">
              <strong>Verifica tu correo ({{ auth.user.email }}).</strong>
              Al verificarlo vincularemos a tu cuenta las reservas que hayas hecho como invitado.
            </div>
            <button
              type="button"
              class="btn btn-sm btn-outline-dark rounded-pill px-3"
              :disabled="sending"
              @click="reenviarVerificacion"
            >
              <span v-if="sending" class="spinner-border spinner-border-sm me-1"></span>
              <font-awesome-icon v-else icon="fa-solid fa-paper-plane" class="me-1" />
              Reenviar enlace
            </button>
          </div>

          <div class="p-4 shadow-sm bg-white rounded-4 min-vh-100">
            <router-view />
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  background-color: #f8f9fa;
  min-height: 100vh;
}

@media (min-width: 992px) {
  .bd-sidebar {
    position: sticky;
    top: 100px;
    /* Ajustamos el alto para que no choque con el footer */
    height: calc(100vh - 120px);
    overflow-y: auto;
  }
}
</style>
