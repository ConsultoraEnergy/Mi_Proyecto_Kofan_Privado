<script setup>
import { BOOKING_STATUS as S, BOOKING_STATUS_META } from "@/constants/booking";
import { useMoney } from "@/composables/useMoney";
import { formatDate, formatDateTime } from "@/utils/format";
import BookingRowActions from "@/components/admin/bookings/BookingRowActions.vue";

defineProps({
  bookings: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  /** Permisos de BookingRowActions. */
  can: { type: Object, required: true },
});

defineEmits(["receipt", "transition", "check-in", "edit", "folio"]);

const money = useMoney();

// Clases suaves del diseño para cada estado (la etiqueta y el ícono vienen de BOOKING_STATUS_META).
const SOFT_BADGES = {
  pending_verification: "badge-soft-sky",
  pending_payment: "badge-soft-sand",
  confirmed: "badge-soft-apple",
  checked_in: "badge-soft-sky",
  checked_out: "badge-soft-neutral",
  cancelled: "badge-soft-rose",
};

const statusMeta = (status) =>
  BOOKING_STATUS_META[status] || { label: status, icon: "fa-solid fa-circle-info" };

const showReason = (booking) =>
  booking.status_reason && [S.PENDING_PAYMENT, S.CANCELLED].includes(booking.status);
</script>

<template>
  <div class="position-relative" style="min-height: 300px">
    <div
      v-if="loading"
      class="d-flex flex-column justify-content-center align-items-center h-100 position-absolute w-100 bg-white z-1"
      style="min-height: 300px"
    >
      <div class="spinner-border" style="width: 3rem; height: 3rem; color: var(--k-apple)" role="status">
        <span class="visually-hidden">Cargando...</span>
      </div>
      <p class="brand-handmade mt-3 mb-0">Actualizando las reservas del día...</p>
    </div>

    <div
      v-else-if="bookings.length === 0"
      class="d-flex flex-column justify-content-center align-items-center h-100 py-5 empty-state-copy"
    >
      <font-awesome-icon icon="fa-solid fa-leaf" class="display-6 mb-3" style="color: var(--k-apple)" />
      <h5 class="mb-1">No hay reservas en esta vista por ahora</h5>
      <p class="text-muted small mb-0">Cuando aparezcan nuevos movimientos, los verás aquí.</p>
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th class="ps-4 py-3 text-muted small fw-bold">Código / cliente</th>
            <th class="py-3 text-muted small fw-bold">Habitación</th>
            <th class="py-3 text-muted small fw-bold">Fechas (in - out)</th>
            <th class="py-3 text-muted small fw-bold">Total</th>
            <th class="py-3 text-muted small fw-bold">Estado</th>
            <th class="text-center py-3 text-muted small fw-bold">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="res in bookings" :key="res.id">
            <td class="ps-4">
              <div class="fw-bold text-dark">
                {{ res.code }}
                <span v-if="res.source === 'manual'" class="badge bg-light text-muted border ms-1 fw-normal"
                  >Recepción</span
                >
              </div>
              <div class="text-dark fw-bold" style="font-size: 0.9rem">{{ res.guest?.full_name }}</div>
              <div class="text-muted mt-1" style="font-size: 0.75rem">
                <font-awesome-icon icon="fa-solid fa-phone" class="me-1" />
                {{ res.guest?.phone || "Sin celular" }} <br />
                <font-awesome-icon icon="fa-solid fa-envelope" class="me-1" />
                {{ res.guest?.email || "Sin correo" }}
              </div>
            </td>
            <td>
              <div class="fw-bold">{{ res.room?.name || "N/A" }}</div>
              <div v-if="res.room?.number" class="small text-muted">N.º {{ res.room.number }}</div>
            </td>
            <td>
              <div class="small text-muted"><strong>Entra:</strong> {{ formatDate(res.check_in) }}</div>
              <div class="small text-muted"><strong>Sale:</strong> {{ formatDate(res.check_out) }}</div>
              <div class="small text-muted">{{ res.nights }} noche(s)</div>
            </td>
            <td>
              <div class="fw-bold text-success">{{ money(res.total_amount) }}</div>
              <div class="small text-muted">Anticipo: {{ money(res.deposit_amount) }}</div>
              <div
                v-if="res.calculated_amount && res.total_amount !== res.calculated_amount"
                class="small text-warning-emphasis"
                :title="`Tarifa calculada: ${money(res.calculated_amount)}`"
              >
                Precio ajustado
              </div>
            </td>
            <td>
              <span
                class="badge rounded-pill px-3 py-2 d-inline-flex align-items-center fw-normal"
                :class="SOFT_BADGES[res.status] || 'badge-soft-neutral'"
              >
                <font-awesome-icon :icon="statusMeta(res.status).icon" class="me-2" />
                {{ statusMeta(res.status).label }}
              </span>
              <div
                v-if="res.status === S.PENDING_PAYMENT && res.payment_due_at"
                class="small text-muted mt-1"
              >
                Vence: {{ formatDateTime(res.payment_due_at) }}
              </div>
              <div
                v-if="showReason(res)"
                class="small text-muted mt-1 reason-text"
                :title="res.status_reason"
              >
                Motivo: {{ res.status_reason }}
              </div>
            </td>
            <td class="text-center align-middle">
              <BookingRowActions
                :booking="res"
                :can="can"
                @receipt="$emit('receipt', $event)"
                @transition="(booking, target) => $emit('transition', booking, target)"
                @check-in="$emit('check-in', $event)"
                @edit="$emit('edit', $event)"
                @folio="$emit('folio', $event)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table thead th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.table tbody tr:hover {
  background: rgba(238, 248, 253, 0.32);
}

.reason-text {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-state-copy {
  font-family: "Handlee", cursive;
  color: var(--k-forest);
}

.badge-soft-apple {
  background: rgba(139, 207, 91, 0.18);
  color: var(--k-forest);
  border: 1px solid rgba(139, 207, 91, 0.45);
}

.badge-soft-sand {
  background: var(--k-sand-soft);
  color: var(--k-sand);
  border: 1px solid rgba(212, 175, 55, 0.32);
}

.badge-soft-sky {
  background: var(--k-sky-soft);
  color: var(--k-sky);
  border: 1px solid rgba(52, 152, 219, 0.25);
}

.badge-soft-neutral {
  background: rgba(36, 64, 58, 0.08);
  color: var(--k-forest);
  border: 1px solid rgba(36, 64, 58, 0.18);
}

.badge-soft-rose {
  background: rgba(229, 184, 184, 0.2);
  color: #8a4c4c;
  border: 1px solid rgba(229, 184, 184, 0.5);
}
</style>
