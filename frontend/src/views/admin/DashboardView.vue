<script setup>
import { ref, onMounted, computed } from "vue";
import { getDashboard } from "@/api/operations";
import { errorMessage } from "@/api/apiClient";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { BOOKING_STATUS_META, PERMISSIONS } from "@/constants/booking";
import { formatMoney, formatDateTime } from "@/utils/format";
import RoomHistoryCard from "@/components/RoomHistoryCard.vue";
import ActivityNotificationsModal from "@/components/ActivityNotificationsModal.vue";

const auth = useAuthStore();
const configStore = useConfigStore();

const stats = ref({
  month_revenue: 0,
  confirmed_bookings: 0,
  pending_verification: 0,
  in_house_guests: 0,
  arrivals_today: 0,
  departures_today: 0,
  occupancy_percent: 0,
  occupied_rooms: 0,
  sellable_rooms: 0,
});

const modalAvisosVisible = ref(false);
const habitacionesPopulares = ref([]);
const ultimosMovimientos = ref([]);
const loadError = ref("");

const cargarDashboard = async () => {
  loadError.value = "";
  try {
    const data = await getDashboard();
    stats.value = { ...stats.value, ...(data?.stats || {}) };
    habitacionesPopulares.value = data?.popular_rooms || [];
    ultimosMovimientos.value = data?.recent_activity || [];
  } catch (error) {
    loadError.value = errorMessage(error, "No se pudieron cargar los indicadores del panel.");
  }
};

const maxReservasPopulares = computed(() =>
  Math.max(1, ...habitacionesPopulares.value.map((hab) => hab.bookings || 0)),
);

const statusMeta = (status) => BOOKING_STATUS_META[status] || { label: status, badge: "bg-secondary" };

const prioridades = computed(() => [
  {
    label: "Llegadas hoy",
    value: stats.value.arrivals_today,
    icon: "fa-solid fa-door-open",
    tone: "sky",
  },
  {
    label: "Salidas hoy",
    value: stats.value.departures_today,
    icon: "fa-solid fa-key",
    tone: "apple",
  },
  {
    label: "Reservas confirmadas",
    value: stats.value.confirmed_bookings,
    icon: "fa-solid fa-calendar-check",
    tone: "sand",
  },
]);

onMounted(() => {
  cargarDashboard();
});
</script>

<template>
  <div class="admin-dashboard">
    <div v-if="loadError" class="alert alert-danger small">{{ loadError }}</div>

    <section class="eco-card priorities-section p-4 mb-4">
      <div
        class="d-flex flex-column flex-lg-row justify-content-between align-items-start gap-3"
      >
        <div>
          <p class="brand-handmade mb-1">Bienvenida a {{ configStore.hotelName }}</p>
          <h2 class="section-title h3 mb-2">Prioridades del Día</h2>
          <p class="text-muted mb-0">
            Revisa primero los pagos por verificar, las llegadas, las salidas y el
            nivel de ocupación para mantener una experiencia tranquila.
          </p>
        </div>

        <div class="d-flex flex-wrap gap-2">
          <router-link
            v-if="auth.can(PERMISSIONS.BOOKINGS_READ_ALL)"
            :to="{ name: 'admin-bookings' }"
            class="btn btn-brand"
          >
            <font-awesome-icon icon="fa-solid fa-calendar-day" class="me-2" />
            Reservas de hoy
          </router-link>
          <router-link
            v-if="auth.can(PERMISSIONS.ROOMS_READ_ALL)"
            :to="{ name: 'admin-rooms' }"
            class="btn btn-soft-sky"
          >
            <font-awesome-icon icon="fa-solid fa-bed" class="me-2" /> Estado de
            habitaciones
          </router-link>
        </div>
      </div>

      <component
        :is="auth.can(PERMISSIONS.BOOKINGS_READ_ALL) ? 'router-link' : 'div'"
        :to="{ name: 'admin-bookings', query: { tab: 'pending_verification' } }"
        class="verify-banner d-flex align-items-center gap-3 mt-3 text-decoration-none"
        :class="{ 'has-pending': stats.pending_verification > 0 }"
      >
        <div class="priority-icon">
          <font-awesome-icon icon="fa-solid fa-receipt" />
        </div>
        <div class="flex-grow-1">
          <p class="small text-uppercase mb-0 fw-bold">Pagos por verificar</p>
          <small class="text-muted">
            {{ stats.pending_verification > 0
              ? "Hay comprobantes de anticipo esperando revisión."
              : "No hay comprobantes pendientes de revisión." }}
          </small>
        </div>
        <h3 class="mb-0 fw-bold text-brand">{{ stats.pending_verification }}</h3>
      </component>

      <div class="row g-3 mt-1">
        <div
          v-for="item in prioridades"
          :key="item.label"
          class="col-sm-4"
        >
          <div class="priority-pill" :class="`tone-${item.tone}`">
            <div class="priority-icon">
              <font-awesome-icon :icon="item.icon" />
            </div>
            <div>
              <p class="small text-uppercase mb-1 text-muted">
                {{ item.label }}
              </p>
              <h4 class="mb-0 fw-bold text-brand">{{ item.value }}</h4>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="row g-4 mb-4">
      <div class="col-md-4">
        <div class="eco-card h-100 p-3 card-stat">
          <div class="d-flex justify-content-between">
            <div>
              <p class="text-muted small fw-bold mb-1 text-uppercase">
                Ingresos del Mes
              </p>
              <h3 class="fw-bold mb-0 text-brand">
                {{ formatMoney(stats.month_revenue, configStore.data.currency) }}
              </h3>
            </div>
            <div class="icon-circle icon-leaf">
              <font-awesome-icon icon="fa-solid fa-hand-holding-dollar" />
            </div>
          </div>
          <div class="mt-3 small text-muted">Mes en curso</div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="eco-card h-100 p-3 card-stat">
          <div class="d-flex justify-content-between">
            <div>
              <p class="text-muted small fw-bold mb-1 text-uppercase">
                Huéspedes Hoy
              </p>
              <h3 class="fw-bold mb-0 text-brand">{{ stats.in_house_guests }}</h3>
            </div>
            <div class="icon-circle icon-sand">
              <font-awesome-icon icon="fa-solid fa-users" />
            </div>
          </div>
          <div class="mt-3 small text-muted">En las instalaciones</div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="eco-card h-100 p-3 card-stat">
          <div class="d-flex justify-content-between">
            <div>
              <p class="text-muted small fw-bold mb-1 text-uppercase">
                Ocupación
              </p>
              <h3 class="fw-bold mb-0 text-brand">
                {{ stats.occupancy_percent }}%
              </h3>
            </div>
            <div class="icon-circle icon-soft">
              <font-awesome-icon icon="fa-solid fa-bed" />
            </div>
          </div>
          <div class="progress mt-3" style="height: 7px">
            <div
              class="progress-bar progress-brand"
              :style="{ width: Math.min(stats.occupancy_percent, 100) + '%' }"
            ></div>
          </div>
          <div class="mt-2 small text-muted">
            {{ stats.occupied_rooms }} de {{ stats.sellable_rooms }} habitaciones ocupadas
          </div>
        </div>
      </div>
    </div>

    <div class="row g-4">
      <div class="col-lg-8">
        <div class="eco-card rounded-4 p-4 h-100">
          <p class="brand-handmade small mb-1">Preferencias de los huéspedes</p>
          <h5 class="section-title mb-4">Habitaciones más solicitadas</h5>

          <p v-if="!habitacionesPopulares.length" class="text-muted small mb-0">
            Aún no hay reservas suficientes para mostrar tendencias.
          </p>

          <div
            v-for="(hab, index) in habitacionesPopulares"
            :key="hab.room_id"
            class="mb-4"
          >
            <div class="d-flex justify-content-between mb-1">
              <span class="fw-bold text-brand">{{ hab.name }}</span>
              <span class="text-muted small">{{ hab.bookings }} reservas</span>
            </div>
            <div class="progress" style="height: 10px">
              <div
                class="progress-bar progress-brand"
                :class="index % 2 === 0 ? 'tone-sky-bar' : 'tone-apple-bar'"
                :style="{ width: Math.round((hab.bookings / maxReservasPopulares) * 100) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-4">
        <div class="card border-0 shadow-sm rounded-4 p-4 mb-4">
          <h5 class="fw-bold mb-4">Actividad de Reservas</h5>

          <p v-if="!ultimosMovimientos.length" class="text-muted small">Sin movimientos recientes.</p>

          <div v-for="item in ultimosMovimientos.slice(0, 3)" :key="`${item.booking_id}-${item.at}`"
               class="d-flex mb-3 align-items-center p-3 bg-white border shadow-sm rounded-3 notification-item">
            <div class="activity-dot flex-shrink-0 me-3" :class="item.status === 'cancelled' ? 'bg-danger' : 'bg-success'"></div>
            <div class="flex-grow-1 min-w-0">
              <h6 class="mb-0 fw-bold small text-truncate">{{ item.guest_name }}</h6>
              <p class="mb-0 text-muted extra-small text-truncate">
                <span class="badge me-1" :class="statusMeta(item.status).badge">{{ statusMeta(item.status).label }}</span>
                {{ item.room_name }} · {{ formatDateTime(item.at) }}
              </p>
            </div>
            <div class="fw-bold small text-nowrap ms-2">{{ formatMoney(item.total_amount, configStore.data.currency) }}</div>
          </div>

          <button @click="modalAvisosVisible = true" class="btn btn-light btn-sm w-100 mt-2 fw-bold text-muted rounded-3">
            Ver mis avisos
          </button>
        </div>

        <RoomHistoryCard v-if="auth.can(PERMISSIONS.AUDIT_READ)" />
      </div>
    </div>

    <ActivityNotificationsModal :show="modalAvisosVisible" @close="modalAvisosVisible = false" />

  </div>
</template>

<style scoped>
.priorities-section {
  background: linear-gradient(
    135deg,
    rgba(212, 175, 55, 0.12) 0%,
    var(--k-cream) 60%,
    var(--k-apple-soft) 100%
  );
  border: 1px solid var(--k-border);
  border-radius: 20px;
}

.btn-brand:hover {
  filter: brightness(1.03);
}

.btn-soft-sky:hover {
  box-shadow: 0 10px 20px rgba(52, 152, 219, 0.18);
}

.card-stat {
  border: 1px solid var(--k-border);
  background: var(--k-cream);
  border-radius: 18px;
  transition: transform 0.25s ease;
}

.card-stat:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
}

.priority-pill {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 1rem;
  border-radius: 16px;
  border: 1px solid var(--k-border);
  background: rgba(255, 255, 255, 0.78);
  transition: all 0.3s ease;
}

.priority-pill:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.08);
}

.priority-icon,
.icon-circle {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
}

.tone-sky .priority-icon,
.icon-sky {
  background: var(--k-sky-soft);
  color: var(--k-sky);
}

.tone-apple .priority-icon,
.icon-leaf {
  background: var(--k-apple-soft);
  color: var(--k-forest);
}

.tone-sand .priority-icon,
.icon-sand {
  background: var(--k-sand-soft);
  color: var(--k-sand);
}

.tone-forest .priority-icon,
.icon-soft {
  background: rgba(15, 59, 42, 0.1);
  color: var(--k-forest);
}

.trend-up {
  color: var(--k-forest-soft);
}

.progress {
  background: rgba(15, 59, 42, 0.06);
  border-radius: 999px;
}

.progress-brand {
  background: linear-gradient(90deg, var(--k-forest), var(--k-apple));
}

.tone-sky-bar {
  background: linear-gradient(90deg, var(--k-sky-light), var(--k-sky));
}

.tone-apple-bar {
  background: linear-gradient(90deg, var(--k-apple), var(--k-apple-light));
}

.verify-banner {
  padding: 1rem;
  border-radius: 16px;
  border: 1px solid var(--k-border);
  background: rgba(255, 255, 255, 0.78);
  color: inherit;
}

.verify-banner .priority-icon {
  background: var(--k-sky-soft);
  color: var(--k-sky);
}

.verify-banner.has-pending {
  border-color: var(--k-sand);
  background: var(--k-sand-soft);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.06);
}

.verify-banner.has-pending .priority-icon {
  background: var(--k-sand);
  color: var(--k-offwhite);
}

.activity-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.activity-dot.is-ok {
  background: var(--k-apple);
}

.activity-dot.is-cancel {
  background: var(--k-danger-soft);
}

.extra-small {
  font-size: 0.75rem;
}

.rounded-4 {
  border-radius: 1.25rem;
}
</style>
