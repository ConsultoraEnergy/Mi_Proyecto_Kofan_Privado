<script setup>
import { assetUrl } from "@/config/env";
import { NO_PHOTO_PLACEHOLDER, operationalStatusMeta } from "@/constants/rooms";
import { useMoney } from "@/composables/useMoney";

defineProps({
  rooms: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  /** { edit, viewHistory, book } */
  can: { type: Object, required: true },
  /** id del modal de edición (Bootstrap lo abre con data-bs-target). */
  formModalId: { type: String, default: "" },
});

defineEmits(["calendar", "history", "edit", "delete"]);

const money = useMoney();

const onImageError = (event) => {
  event.target.onerror = null;
  event.target.src = NO_PHOTO_PLACEHOLDER;
};
</script>

<template>
  <div class="table-responsive p-0">
    <table class="table table-hover align-middle mb-0 table-serene">
      <thead class="table-soft">
        <tr>
          <th class="ps-4 py-3 text-muted small fw-bold">NOMBRE</th>
          <th class="py-3 text-muted small fw-bold">PRECIO/NOCHE</th>
          <th class="py-3 text-muted small fw-bold">CAPACIDAD</th>
          <th class="py-3 text-muted small fw-bold">ESTADO</th>
          <th class="text-center py-3 text-muted small fw-bold">DISPONIBILIDAD</th>
          <th class="text-center py-3 text-muted small fw-bold">ACCIONES</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="6" class="text-center py-5">
            <div class="spinner-border" style="color: var(--k-apple)" role="status">
              <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="brand-handmade mt-3 mb-0">Preparando los espacios del hotel...</p>
          </td>
        </tr>

        <tr v-else-if="rooms.length === 0">
          <td colspan="6" class="text-center text-muted py-5">
            <font-awesome-icon
              icon="fa-solid fa-leaf"
              class="display-6 mb-3 d-block mx-auto"
              style="color: var(--k-apple)"
            />
            <p class="empty-state-copy mb-1">Aún no hay habitaciones para este filtro.</p>
            <small>Cuando registres un nuevo espacio, aparecerá aquí.</small>
          </td>
        </tr>

        <template v-else>
          <tr v-for="room in rooms" :key="room.id">
            <td class="ps-4">
              <div class="d-flex align-items-center">
                <img
                  :src="assetUrl(room.main_image) || NO_PHOTO_PLACEHOLDER"
                  class="rounded me-3 border shadow-sm room-thumb"
                  alt=""
                  @error="onImageError"
                />
                <div>
                  <div class="fw-bold text-brand">{{ room.name }}</div>
                  <small class="text-muted">
                    N° {{ room.number }}<span v-if="room.room_type"> · {{ room.room_type.name }}</span>
                  </small>
                </div>
              </div>
            </td>

            <td class="fw-semibold text-brand">{{ money(room.price_per_night) }}</td>

            <td class="text-muted">{{ room.capacity }} pers.</td>

            <td>
              <span
                class="badge px-3 py-2 rounded-pill"
                :class="operationalStatusMeta(room.operational_status).badge"
              >
                <font-awesome-icon :icon="operationalStatusMeta(room.operational_status).icon" class="me-1" />
                {{ operationalStatusMeta(room.operational_status).label }}
              </span>
              <div v-if="!room.is_active" class="small text-muted mt-1">
                <font-awesome-icon icon="fa-solid fa-eye-slash" class="me-1" /> No habilitada para la venta
              </div>
            </td>

            <td class="text-center">
              <button
                v-if="can.book"
                type="button"
                class="btn btn-sm btn-soft-sky rounded-pill px-3 fw-medium shadow-sm"
                style="font-size: 0.82rem"
                @click="$emit('calendar', room)"
              >
                <font-awesome-icon icon="fa-solid fa-calendar-days" class="me-1" /> Ver Fechas
              </button>
            </td>

            <td class="text-center">
              <div class="d-flex justify-content-center gap-2">
                <button
                  v-if="can.viewHistory"
                  type="button"
                  class="btn btn-sm btn-outline-dark rounded-circle action-btn"
                  title="Historial de cambios"
                  @click="$emit('history', room)"
                >
                  <font-awesome-icon icon="fa-solid fa-clock" class="fs-6" />
                </button>

                <template v-if="can.edit">
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary rounded-circle action-btn"
                    data-bs-toggle="modal"
                    :data-bs-target="`#${formModalId}`"
                    title="Editar habitación"
                    @click="$emit('edit', room)"
                  >
                    <font-awesome-icon icon="fa-regular fa-pen-to-square" class="fs-6" />
                  </button>

                  <button
                    type="button"
                    class="btn btn-sm btn-outline-danger rounded-circle action-btn"
                    title="Retirar habitación"
                    @click="$emit('delete', room)"
                  >
                    <font-awesome-icon icon="fa-solid fa-trash" class="fs-6" />
                  </button>
                </template>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.room-thumb {
  width: 60px;
  height: 50px;
  object-fit: cover;
}

.action-btn {
  width: 35px;
  height: 35px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--bs-box-shadow-sm);
}

.table-soft th {
  background: rgba(52, 152, 219, 0.08) !important;
}

.table-serene tbody tr:hover {
  background: rgba(52, 152, 219, 0.1);
}

.empty-state-copy {
  font-size: 1.1rem;
}

.badge-soft-success {
  background: rgba(139, 207, 91, 0.18);
  color: var(--k-forest);
  border: 1px solid rgba(139, 207, 91, 0.45);
}

.badge-soft-maintenance {
  background: var(--k-sky-soft);
  color: var(--k-sky);
  border: 1px solid rgba(52, 152, 219, 0.25);
}

.badge-soft-warning {
  background: var(--k-sand-soft);
  color: var(--k-sand);
  border: 1px solid rgba(212, 175, 55, 0.32);
}

.badge-soft-danger {
  background: rgba(229, 184, 184, 0.2);
  color: #8a4c4c;
  border: 1px solid rgba(229, 184, 184, 0.5);
}
</style>
