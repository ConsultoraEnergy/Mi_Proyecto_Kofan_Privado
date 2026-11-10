<script setup>
import { computed, onMounted, ref } from "vue";
import { PERMISSIONS } from "@/constants/booking";
import { ROOM_FILTERS } from "@/constants/rooms";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useRoomsInventory } from "@/composables/useRoomsInventory";
import FilterChips from "@/components/common/FilterChips.vue";
import PaginationBar from "@/components/common/PaginationBar.vue";
import RoomFormModal from "@/components/admin/rooms/RoomFormModal.vue";
import RoomTypesPanel from "@/components/admin/rooms/RoomTypesPanel.vue";
import RoomsTable from "@/components/admin/rooms/RoomsTable.vue";
import RoomCalendarModal from "@/components/RoomCalendarModal.vue";
import RoomHistoryModal from "@/components/RoomHistoryModal.vue";

const FORM_MODAL_ID = "modalHabitacion";

const auth = useAuthStore();
const configStore = useConfigStore();

const inventory = useRoomsInventory();
const { roomTypes, loading, search, typeFilter, quickFilter, filteredRooms, counts, page, totalPages } =
  inventory;

const can = computed(() => ({
  edit: auth.can(PERMISSIONS.ROOMS_WRITE),
  viewHistory: auth.can(PERMISSIONS.AUDIT_READ),
  book: auth.can(PERMISSIONS.BOOKINGS_CREATE_MANUAL),
}));

const filterOptions = computed(() => ROOM_FILTERS.map((f) => ({ ...f, count: counts.value[f.key] })));

const showTypes = ref(false);
const formModal = ref(null);

const calendar = ref({ show: false, room: null });
const openCalendar = (room) => {
  calendar.value = { show: true, room: { ...room } };
};
const closeCalendar = () => {
  calendar.value = { show: false, room: null };
};

const history = ref({ show: false, room: null });
const openHistory = (room) => {
  history.value = { show: true, room };
};

onMounted(() => {
  configStore.fetchSiteConfig();
  inventory.loadTypes();
  inventory.loadRooms();
});
</script>

<template>
  <div class="container-fluid py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
      <div>
        <p class="brand-handmade mb-1">Espacios listos para recibir viajeros</p>
        <h2 class="section-title mb-1 d-flex align-items-center gap-2">
          <font-awesome-icon icon="fa-solid fa-bed" />
          Gestión de Habitaciones
        </h2>
        <p class="text-muted mb-0">
          Organiza disponibilidad, mantenimiento y calendario con una vista clara y serena.
        </p>
      </div>

      <div v-if="can.edit" class="d-flex gap-2 flex-wrap">
        <button
          type="button"
          class="btn btn-soft-sky shadow-sm rounded-pill px-4"
          :aria-expanded="showTypes"
          @click="showTypes = !showTypes"
        >
          <font-awesome-icon icon="fa-solid fa-tag" class="me-2" />
          Tipos de habitación
        </button>
        <button
          type="button"
          class="btn btn-brand shadow-sm rounded-pill px-4"
          data-bs-toggle="modal"
          :data-bs-target="`#${FORM_MODAL_ID}`"
          @click="formModal?.openCreate()"
        >
          <font-awesome-icon icon="fa-solid fa-leaf" class="me-2" />
          Nueva Habitación
        </button>
      </div>
    </div>

    <RoomTypesPanel v-if="can.edit && showTypes" :types="roomTypes" @saved="inventory.loadTypes" />

    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
      <FilterChips v-model="quickFilter" :options="filterOptions" />

      <div class="d-flex gap-2 flex-wrap">
        <select
          v-model="typeFilter"
          class="form-select form-select-sm rounded-pill"
          style="max-width: 200px"
          aria-label="Filtrar por tipo"
        >
          <option value="">Todos los tipos</option>
          <option v-for="type in roomTypes" :key="type.id" :value="type.code">{{ type.name }}</option>
        </select>
        <input
          v-model="search"
          type="search"
          class="form-control form-control-sm rounded-pill"
          style="max-width: 240px"
          placeholder="Buscar por nombre o número..."
          aria-label="Buscar habitaciones"
        />
      </div>
    </div>

    <div class="card eco-card border-0 shadow-sm rounded-4 overflow-hidden">
      <RoomsTable
        :rooms="filteredRooms"
        :loading="loading"
        :can="can"
        :form-modal-id="FORM_MODAL_ID"
        @calendar="openCalendar"
        @history="openHistory"
        @edit="formModal?.openEdit($event)"
        @delete="inventory.removeRoom"
      />
      <PaginationBar :page="page" :total-pages="totalPages" @change="inventory.goToPage" />
    </div>

    <RoomFormModal
      v-if="can.edit"
      ref="formModal"
      :modal-id="FORM_MODAL_ID"
      :room-types="roomTypes"
      @changed="inventory.loadRooms"
    />

    <RoomCalendarModal
      v-if="calendar.show && calendar.room"
      :show="calendar.show"
      :habitacion="calendar.room"
      @close="closeCalendar"
      @reserva-creada="inventory.loadRooms"
    />

    <RoomHistoryModal
      v-if="can.viewHistory"
      :show="history.show"
      :room-id="history.room?.id"
      :room-label="history.room ? `${history.room.number} · ${history.room.name}` : ''"
      @close="history.show = false"
    />
  </div>
</template>
