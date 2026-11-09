<script setup>
import { ref, watch } from "vue";
import { listNotifications, markAllNotificationsRead } from "@/api/operations";
import { errorMessage } from "@/api/apiClient";
import { formatDateTime } from "@/utils/format";

const props = defineProps({
  show: Boolean,
});

defineEmits(["close"]);

// El backend envía clases de Bootstrap Icons; aquí se usa el ícono FontAwesome equivalente según el tema.
const THEME_ICONS = {
  success: "fa-solid fa-circle-check",
  warning: "fa-solid fa-clock",
  danger: "fa-solid fa-ban",
  info: "fa-solid fa-circle-info",
  secondary: "fa-solid fa-check",
  primary: "fa-solid fa-bell",
};

const logs = ref([]);
const isLoading = ref(false);
const loadError = ref("");

const fetchNotifications = async () => {
  isLoading.value = true;
  loadError.value = "";
  try {
    logs.value = (await listNotifications()) || [];
  } catch (error) {
    loadError.value = errorMessage(error, "No se pudieron cargar tus avisos.");
    logs.value = [];
  } finally {
    isLoading.value = false;
  }
};

const marcarTodasComoLeidas = async () => {
  try {
    await markAllNotificationsRead();
    logs.value.forEach((log) => (log.read = true));
  } catch (error) {
    loadError.value = errorMessage(error, "No se pudieron marcar los avisos como leídos.");
  }
};

watch(
  () => props.show,
  (visible) => {
    if (visible) fetchNotifications();
  },
);
</script>

<template>
  <div v-if="show" class="modal-backdrop fade show"></div>
  <div class="modal fade show d-block" tabindex="-1" role="dialog" v-if="show" @click.self="$emit('close')">
    <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
      <div class="modal-content border-0 shadow-lg rounded-4">

        <div class="modal-header text-white border-0">
          <h5 class="modal-title fw-bold">
            <font-awesome-icon icon="fa-solid fa-bell" class="me-2 text-warning" /> Historial de Actividad y Avisos
          </h5>
          <button type="button" class="btn-close btn-close-white" @click="$emit('close')"></button>
        </div>

        <div class="modal-body p-0 bg-light">
          <div v-if="isLoading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="text-muted mt-2 small">Cargando tus notificaciones...</p>
          </div>

          <div v-else-if="loadError" class="alert alert-danger m-3 small">{{ loadError }}</div>

          <div v-else-if="logs.length === 0" class="text-center py-5 text-muted">
            <font-awesome-icon icon="fa-solid fa-bell-slash" class="display-4 d-block mx-auto mb-3 text-secondary" />
            No tienes avisos recientes.
          </div>

          <div v-else class="list-group list-group-flush">
            <div v-for="log in logs" :key="log.id"
                 class="list-group-item list-group-item-action p-3 border-bottom"
                 :class="{'bg-white': log.read, 'bg-primary-subtle': !log.read}">
              <div class="d-flex align-items-start gap-3">

                <div class="icon-circle shadow-sm flex-shrink-0" :class="`bg-${log.theme || 'primary'}`">
                  <font-awesome-icon :icon="THEME_ICONS[log.theme] || THEME_ICONS.primary" class="text-white" />
                </div>

                <div class="flex-grow-1 min-w-0">
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <h6 class="mb-0 fw-bold text-truncate pe-3" :class="{'text-dark': log.read, 'text-primary': !log.read}">
                      {{ log.title }}
                    </h6>
                    <small class="text-muted text-nowrap" style="font-size: 0.75rem;">{{ formatDateTime(log.created_at) }}</small>
                  </div>
                  <p class="mb-0 text-muted small" style="white-space: pre-line;">{{ log.message }}</p>
                </div>

              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer bg-white border-top-0 d-flex justify-content-between align-items-center p-3">
          <span class="text-muted small">Últimos {{ logs.length }} avisos registrados</span>

          <div class="d-flex gap-2">
            <button @click="marcarTodasComoLeidas" class="btn btn-sm btn-outline-secondary rounded-pill px-3" :disabled="!logs.length">
              <font-awesome-icon icon="fa-solid fa-check" class="me-1" /> Marcar todas leídas
            </button>
            <button @click="$emit('close')" class="btn btn-sm btn-dark rounded-pill px-4 shadow-sm">
              Cerrar
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-header {
  background-color: var(--k-forest-soft);
}
.modal-backdrop { background-color: var(--k-forest); }
.modal { display: block; z-index: 1055; }

.icon-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
