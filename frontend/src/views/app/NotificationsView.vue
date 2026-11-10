<script setup>
import { ref, computed, onMounted } from "vue";
import Swal from "sweetalert2";
import { listNotifications, markAllNotificationsRead } from "@/api/operations";
import { errorMessage } from "@/api/apiClient";
import { formatDateTime } from "@/utils/format";

const avisos = ref([]);
const isLoading = ref(true);
const marking = ref(false);

const sinLeer = computed(() => avisos.value.filter((a) => !a.read).length);

const cargarAvisos = async () => {
  isLoading.value = true;
  try {
    avisos.value = await listNotifications();
  } catch (error) {
    Swal.fire({
      toast: true,
      position: "top-end",
      showConfirmButton: false,
      timer: 3000,
      icon: "error",
      title: errorMessage(error, "No se pudieron cargar tus avisos"),
    });
  } finally {
    isLoading.value = false;
  }
};

onMounted(cargarAvisos);

const marcarTodosLeidos = async () => {
  marking.value = true;
  try {
    await markAllNotificationsRead();
    avisos.value.forEach((a) => (a.read = true));

    // Le avisamos al menú lateral que actualice la campanita
    window.dispatchEvent(new Event("notificaciones-leidas"));

    Swal.mixin({
      toast: true,
      position: "top-end",
      showConfirmButton: false,
      timer: 2000,
      timerProgressBar: true,
    }).fire({ icon: "success", title: "Avisos marcados como leídos" });
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudieron marcar los avisos."), "error");
  } finally {
    marking.value = false;
  }
};

/** El backend envía nombres de Bootstrap Icons (bi-...); aquí se traducen a FontAwesome. */
const resolverIconoAviso = (icono) => {
  const valor = String(icono || "").toLowerCase();
  if (valor.includes("check")) return "fa-solid fa-circle-check";
  if (valor.includes("exclamation") || valor.includes("info")) return "fa-solid fa-circle-info";
  if (valor.includes("house") || valor.includes("door")) return "fa-solid fa-house-chimney";
  if (valor.includes("x-circle") || valor.includes("ban") || valor.includes("cancel"))
    return "fa-solid fa-ban";
  return "fa-solid fa-bell";
};

const theme = (aviso) => aviso.theme || "primary";
</script>

<template>
  <div class="container-fluid py-2">
    <div class="d-flex flex-wrap gap-3 justify-content-between align-items-center mb-4">
      <div>
        <h4 class="fw-bold text-dark mb-1">Centro de Avisos</h4>
        <p class="text-muted mb-0 small">Mantente al tanto de tus reservas y promociones exclusivas.</p>
      </div>
      <button
        class="btn btn-outline-dark rounded-pill px-4 shadow-sm fw-medium"
        :disabled="marking || sinLeer === 0"
        @click="marcarTodosLeidos"
      >
        <span v-if="marking" class="spinner-border spinner-border-sm me-2"></span>
        <font-awesome-icon v-else icon="fa-solid fa-circle-check" class="me-2" /> Marcar como leídos
      </button>
    </div>

    <div class="d-flex flex-column gap-3">
      <div v-if="isLoading" class="text-center py-5">
        <span class="spinner-border text-success" role="status"></span>
      </div>

      <div v-else-if="avisos.length === 0" class="text-center py-5">
        <font-awesome-icon icon="fa-solid fa-bell-slash" class="display-4 mb-3 d-block mx-auto text-light" />
        <h6 class="text-muted fw-bold">No tienes avisos recientes</h6>
        <p class="text-muted small">Aquí aparecerán las actualizaciones de tus reservas.</p>
      </div>

      <div
        v-for="aviso in avisos"
        :key="aviso.id"
        class="card border-0 shadow-sm rounded-4 overflow-hidden aviso-card"
        :class="[`border-start border-4 border-${theme(aviso)}`, { 'aviso-no-leido': !aviso.read }]"
      >
        <div class="card-body p-3 p-md-4 d-flex align-items-start gap-3">
          <div
            class="rounded-3 d-flex align-items-center justify-content-center flex-shrink-0"
            :class="`bg-${theme(aviso)} bg-opacity-10 text-${theme(aviso)}`"
            style="width: 50px; height: 50px"
          >
            <font-awesome-icon :icon="resolverIconoAviso(aviso.icon)" class="fs-4" />
          </div>

          <div class="flex-grow-1">
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-1">
              <h6 class="fw-bold mb-0 text-dark">
                <span v-if="!aviso.read" class="badge bg-warning text-dark me-2">Nuevo</span>
                {{ aviso.title }}
              </h6>
              <small class="text-muted">
                <font-awesome-icon icon="fa-solid fa-clock" class="me-1" />
                {{ formatDateTime(aviso.created_at) }}
              </small>
            </div>
            <p class="mb-0 text-secondary small">{{ aviso.message }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.aviso-card {
  transition:
    transform 0.2s ease,
    background-color 0.2s ease;
  cursor: default;
}

.aviso-card:hover {
  transform: translateX(6px);
  background-color: #f8f9fa !important;
}

.aviso-no-leido {
  background-color: var(--k-apple-soft);
}
</style>
