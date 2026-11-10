/**
 * Inventario de habitaciones del panel: listado paginado, búsqueda, filtro por tipo, filtros
 * rápidos por estado, catálogo de tipos y retiro de habitaciones.
 */
import { computed, ref, watch } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { deleteRoom, listRooms, listRoomTypes } from "@/api/rooms";
import { ROOM_FILTERS } from "@/constants/rooms";
import { useDebouncedWatch } from "@/composables/useDebouncedWatch";
import { usePagination } from "@/composables/usePagination";
import { brandColors } from "@/utils/brandColors";

export const ROOMS_PAGE_SIZE = 50;

export function useRoomsInventory() {
  const rooms = ref([]);
  const roomTypes = ref([]);
  const loading = ref(true);
  const search = ref("");
  const typeFilter = ref("");
  const quickFilter = ref("all");

  const pagination = usePagination(ROOMS_PAGE_SIZE, () => loadRooms());

  const filteredRooms = computed(() => {
    const filter = ROOM_FILTERS.find((f) => f.key === quickFilter.value) || ROOM_FILTERS[0];
    return rooms.value.filter(filter.test);
  });

  const counts = computed(() =>
    Object.fromEntries(ROOM_FILTERS.map((f) => [f.key, rooms.value.filter(f.test).length])),
  );

  let lastRequest = 0;

  async function loadRooms() {
    const requestId = ++lastRequest;
    loading.value = true;
    try {
      const params = { include_inactive: true, page: pagination.page.value, limit: pagination.limit };
      const term = search.value.trim();
      if (term) params.q = term;
      if (typeFilter.value) params.room_type = typeFilter.value;
      const data = await listRooms(params);
      if (requestId !== lastRequest) return;
      rooms.value = data.items || [];
      pagination.total.value = data.total || 0;
    } catch (error) {
      if (requestId !== lastRequest) return;
      Swal.fire("Error", errorMessage(error, "No se pudieron cargar las habitaciones."), "error");
    } finally {
      if (requestId === lastRequest) loading.value = false;
    }
  }

  async function loadTypes() {
    try {
      roomTypes.value = await listRoomTypes(true);
    } catch {
      roomTypes.value = [];
    }
  }

  const restart = () => {
    pagination.reset();
    loadRooms();
  };
  useDebouncedWatch(search, restart);
  watch(typeFilter, restart);

  async function removeRoom(room) {
    const colors = brandColors();
    const result = await Swal.fire({
      title: "¿Deseas retirar esta habitación del inventario?",
      text: "Solo se pueden eliminar habitaciones sin reservas registradas.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: colors.apple,
      cancelButtonColor: colors.forest,
      confirmButtonText: "Sí, retirarla",
      cancelButtonText: "Conservar",
    });
    if (!result.isConfirmed) return false;

    try {
      await deleteRoom(room.id);
      Swal.fire({
        icon: "success",
        title: "Espacio retirado",
        text: "La lista quedó actualizada correctamente.",
        timer: 1600,
        showConfirmButton: false,
      });
      await loadRooms();
      return true;
    } catch (error) {
      if (error?.response?.status === 409) {
        Swal.fire(
          "No se puede eliminar",
          `${errorMessage(error)} Puedes editarla y desmarcar "Habilitada para la venta" para que deje de ofrecerse.`,
          "info",
        );
      } else {
        Swal.fire(
          "No fue posible completar la acción",
          errorMessage(error, "Inténtalo nuevamente en unos segundos."),
          "error",
        );
      }
      return false;
    }
  }

  return {
    rooms,
    roomTypes,
    loading,
    search,
    typeFilter,
    quickFilter,
    filteredRooms,
    counts,
    page: pagination.page,
    totalPages: pagination.totalPages,
    goToPage: pagination.goTo,
    loadRooms,
    loadTypes,
    removeRoom,
  };
}
