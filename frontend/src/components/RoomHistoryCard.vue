<script setup>
import { ref, onMounted } from "vue";
import { listAuditLogs } from "@/api/operations";
import { formatDateTime } from "@/utils/format";
import RoomHistoryModal from "@/components/RoomHistoryModal.vue";

const ACTIONS = {
  create: { label: "Creación", dot: "bg-success" },
  update: { label: "Actualización", dot: "bg-primary" },
  delete: { label: "Eliminación", dot: "bg-danger" },
  add_images: { label: "Fotos agregadas", dot: "bg-info" },
  remove_image: { label: "Foto eliminada", dot: "bg-warning" },
};

const logs = ref([]);
const isLoading = ref(true);
const modalVisible = ref(false);

const actionMeta = (action) => ACTIONS[action] || { label: action, dot: "bg-secondary" };

const fetchLogs = async () => {
  try {
    isLoading.value = true;
    const response = await listAuditLogs({ entity: "room", page: 1, limit: 3 });
    logs.value = response.items || [];
  } catch {
    logs.value = [];
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchLogs);
</script>

<template>
  <div class="card border-0 shadow-sm rounded-4 p-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="fw-bold mb-0">Historial de Habitaciones</h5>
      <span class="text-muted small fw-bold">{{ logs.length }} mov.</span>
    </div>

    <div v-if="isLoading" class="text-center py-4">
      <div class="spinner-border spinner-border-sm text-success"></div>
    </div>

    <div v-else-if="logs.length === 0" class="text-center text-muted py-3 small">
      No hay registros recientes.
    </div>

    <div v-else>
      <div
        v-for="log in logs"
        :key="log.id"
        class="d-flex align-items-center bg-white border shadow-sm rounded-3 py-2 px-3 mb-2 notification-item"
      >
        <div :class="['activity-dot me-3 flex-shrink-0', actionMeta(log.action).dot]"></div>

        <div class="flex-grow-1 min-w-0">
          <h6 class="mb-0 fw-bold small text-truncate">{{ log.entity_label || "Habitación" }}</h6>
          <p class="mb-0 text-muted extra-small text-truncate text-uppercase">
            {{ actionMeta(log.action).label }} por {{ log.actor ? log.actor.split("@")[0] : "Sistema" }}
          </p>
        </div>

        <div class="text-muted extra-small fw-bold ms-2 flex-shrink-0 text-end">
          {{ formatDateTime(log.created_at) }}
        </div>
      </div>
    </div>

    <button
      class="btn btn-light btn-sm w-100 mt-2 fw-bold text-muted border-0 hover-gray"
      :disabled="isLoading"
      @click="modalVisible = true"
    >
      Ver historial completo
    </button>

    <RoomHistoryModal :show="modalVisible" @close="modalVisible = false" />
  </div>
</template>

<style scoped>
.activity-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.extra-small {
  font-size: 0.7rem;
}

.rounded-4 {
  border-radius: 1.25rem !important;
}

.hover-gray:hover {
  background-color: #e9ecef !important;
}

.min-w-0 {
  min-width: 0;
}

.notification-item {
  transition: all 0.2s ease-in-out;
  border-color: #f0f0f0 !important;
}

.notification-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.08) !important;
}
</style>
