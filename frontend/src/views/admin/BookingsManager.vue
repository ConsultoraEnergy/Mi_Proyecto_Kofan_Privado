<script setup>
import { computed, defineAsyncComponent, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { PERMISSIONS } from "@/constants/booking";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { BOOKING_TABS, useBookingsBoard } from "@/composables/useBookingsBoard";
import { useBookingActions } from "@/composables/useBookingActions";
import FilterChips from "@/components/common/FilterChips.vue";
import PaginationBar from "@/components/common/PaginationBar.vue";
import BookingStatsCards from "@/components/admin/bookings/BookingStatsCards.vue";
import BookingsTable from "@/components/admin/bookings/BookingsTable.vue";

const ModalEdicionReserva = defineAsyncComponent(() => import("@/components/ModalEdicionReserva.vue"));
const ModalFolio = defineAsyncComponent(() => import("@/components/ModalFolio.vue"));

const auth = useAuthStore();
const configStore = useConfigStore();
const route = useRoute();

const board = useBookingsBoard({ initialTab: route.query.tab });
const { bookings, summary, loading, activeTab, search, inHouseGuests, page, total, totalPages } = board;
const { changeStatus, viewReceipt } = useBookingActions({ onChanged: board.refresh });

const can = computed(() => ({
  changeStatus: auth.can(PERMISSIONS.BOOKINGS_CHANGE_STATUS),
  edit: auth.can(PERMISSIONS.BOOKINGS_UPDATE),
  viewReceipts: auth.can(PERMISSIONS.BOOKINGS_VIEW_RECEIPTS),
  viewFolio: auth.can(PERMISSIONS.FOLIOS_READ),
}));

const tabOptions = computed(() =>
  BOOKING_TABS.map((tab) => ({
    ...tab,
    count: summary.value[tab.key],
    badgeClass: { pending_verification: "bg-info text-dark", pending_payment: "bg-warning text-dark" }[
      tab.key
    ],
  })),
);

// --- Modales ---
const editModal = ref({ show: false, booking: null, checkIn: false });
const openEdit = (booking, checkIn = false) => {
  editModal.value = { show: true, booking, checkIn };
};

const folioModal = ref({ show: false, booking: null });
const openFolio = (booking) => {
  folioModal.value = { show: true, booking };
};

onMounted(() => {
  configStore.fetchSiteConfig();
  board.refresh();
});
</script>

<template>
  <div class="bookings-manager container-fluid py-4">
    <div class="mb-4">
      <p class="brand-handmade mb-1">Seguimiento sereno de cada llegada</p>
      <h2 class="section-title mb-1 d-flex align-items-center gap-2">
        <font-awesome-icon icon="fa-solid fa-calendar-days" />
        Gestión de Reservas
      </h2>
      <p class="text-muted mb-0">
        Verifica los comprobantes de pago, prioriza llegadas y salidas y acompaña las estancias activas.
      </p>
    </div>

    <BookingStatsCards :summary="summary" :in-house-guests="inHouseGuests" @select="activeTab = $event" />

    <div class="card eco-card board-card border-0 shadow-sm rounded-4 overflow-hidden">
      <div
        class="card-header bg-transparent p-3 border-0 d-flex flex-column flex-xl-row justify-content-between align-items-center gap-3"
      >
        <FilterChips v-model="activeTab" :options="tabOptions" />

        <div class="input-group shadow-sm rounded-pill overflow-hidden search-soft" style="max-width: 360px">
          <span class="input-group-text border-0 ps-3">
            <font-awesome-icon icon="fa-solid fa-magnifying-glass" class="text-muted" />
          </span>
          <input
            v-model="search"
            type="search"
            class="form-control border-0 shadow-none"
            placeholder="Buscar por código, viajero, correo o documento..."
            aria-label="Buscar reservas"
          />
        </div>
      </div>

      <div class="card-body p-0">
        <BookingsTable
          :bookings="bookings"
          :loading="loading"
          :can="can"
          @receipt="viewReceipt"
          @transition="changeStatus"
          @check-in="openEdit($event, true)"
          @edit="openEdit($event, false)"
          @folio="openFolio"
        />
        <PaginationBar
          :page="page"
          :total-pages="totalPages"
          :total="total"
          item-label="reservas"
          @change="board.goToPage"
        />
      </div>
    </div>

    <ModalEdicionReserva
      :show="editModal.show"
      :reserva="editModal.booking"
      :modo-check-in="editModal.checkIn"
      @close="editModal.show = false"
      @actualizado="board.refresh"
    />
    <ModalFolio :show="folioModal.show" :reserva="folioModal.booking" @close="folioModal.show = false" />
  </div>
</template>

<style scoped>
.board-card {
  background: linear-gradient(135deg, rgba(139, 207, 91, 0.08) 0%, var(--k-cream) 100%);
}

.search-soft,
.search-soft .input-group-text,
.search-soft .form-control {
  background: var(--k-offwhite);
}
</style>
