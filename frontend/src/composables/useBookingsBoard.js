/**
 * Tablero de reservas del personal: pestañas por estado, búsqueda, paginación, resumen de
 * pendientes y huéspedes en el hotel. Toda la comunicación pasa por @/api.
 */
import { ref, watch } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { listBookings } from "@/api/bookings";
import { getDashboard } from "@/api/operations";
import { BOOKING_STATUS as S, PERMISSIONS } from "@/constants/booking";
import { useAuthStore } from "@/stores/auth";
import { useDebouncedWatch } from "@/composables/useDebouncedWatch";
import { usePagination } from "@/composables/usePagination";

export const BOOKING_TABS = Object.freeze([
  {
    key: "pending_verification",
    label: "Por verificar",
    icon: "fa-solid fa-receipt",
    statuses: [S.PENDING_VERIFICATION],
  },
  {
    key: "pending_payment",
    label: "Pendientes de pago",
    icon: "fa-solid fa-clock",
    statuses: [S.PENDING_PAYMENT],
  },
  { key: "confirmed", label: "Confirmadas", icon: "fa-solid fa-calendar-days", statuses: [S.CONFIRMED] },
  { key: "checked_in", label: "En el hotel", icon: "fa-solid fa-bed", statuses: [S.CHECKED_IN] },
  { key: "history", label: "Historial", icon: "fa-solid fa-broom", statuses: [S.CHECKED_OUT, S.CANCELLED] },
]);

export const BOOKINGS_PAGE_SIZE = 10;

const tabByKey = (key) => BOOKING_TABS.find((t) => t.key === key);

export function useBookingsBoard({ initialTab } = {}) {
  const auth = useAuthStore();

  const bookings = ref([]);
  const summary = ref({ pending_verification: 0, pending_payment: 0 });
  const loading = ref(true);
  const activeTab = ref(tabByKey(initialTab) ? initialTab : BOOKING_TABS[0].key);
  const search = ref("");
  const inHouseGuests = ref(null);

  const pagination = usePagination(BOOKINGS_PAGE_SIZE, () => load());

  // Solo se aplica la respuesta de la última petición (evita que una pestaña lenta pise a otra).
  let lastRequest = 0;

  async function load() {
    const requestId = ++lastRequest;
    loading.value = true;
    try {
      const tab = tabByKey(activeTab.value) || BOOKING_TABS[0];
      const params = { status: tab.statuses.join(","), page: pagination.page.value, limit: pagination.limit };
      const term = search.value.trim();
      if (term) params.q = term;

      const data = await listBookings(params);
      if (requestId !== lastRequest) return;
      bookings.value = data.items || [];
      pagination.total.value = data.total || 0;
      if (data.summary) summary.value = data.summary;
    } catch (error) {
      if (requestId !== lastRequest) return;
      Swal.fire("Error", errorMessage(error, "No se pudieron cargar las reservas."), "error");
    } finally {
      if (requestId === lastRequest) loading.value = false;
    }
  }

  async function loadInHouseGuests() {
    if (!auth.can(PERMISSIONS.DASHBOARD_READ)) return;
    try {
      const data = await getDashboard();
      inHouseGuests.value = data?.stats?.in_house_guests ?? 0;
    } catch {
      inHouseGuests.value = null;
    }
  }

  const refresh = () => Promise.all([load(), loadInHouseGuests()]);

  const restart = () => {
    pagination.reset();
    load();
  };
  watch(activeTab, restart);
  useDebouncedWatch(search, restart);

  return {
    bookings,
    summary,
    loading,
    activeTab,
    search,
    inHouseGuests,
    page: pagination.page,
    total: pagination.total,
    totalPages: pagination.totalPages,
    goToPage: pagination.goTo,
    load,
    refresh,
  };
}
