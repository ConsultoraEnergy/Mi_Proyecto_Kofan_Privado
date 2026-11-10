/** Catálogo público de habitaciones agrupado por tipo (Home). */
import { computed, ref } from "vue";
import { listRooms, listRoomTypes } from "@/api/rooms";

export const OTHER_ROOMS_SECTION = Object.freeze({ code: "otros", name: "Otros alojamientos" });

/**
 * Agrupa las habitaciones por tipo, en el orden del catálogo de tipos. Los tipos que no vienen en
 * el catálogo (p. ej. inactivos) se agregan al final; las habitaciones sin tipo van a "Otros".
 * Solo se devuelven secciones con habitaciones.
 */
export function groupRoomsByType(rooms, types) {
  const groups = new Map(types.map((t) => [t.code, { code: t.code, name: t.name, rooms: [] }]));
  const other = { ...OTHER_ROOMS_SECTION, rooms: [] };
  for (const room of rooms) {
    const code = room.room_type?.code;
    if (code && !groups.has(code)) groups.set(code, { code, name: room.room_type.name, rooms: [] });
    (code ? groups.get(code) : other).rooms.push(room);
  }
  return [...groups.values(), other].filter((g) => g.rooms.length > 0);
}

export function useRoomCatalog() {
  const rooms = ref([]);
  const roomTypes = ref([]);
  const loading = ref(false);
  const error = ref("");

  const sections = computed(() => groupRoomsByType(rooms.value, roomTypes.value));

  async function load() {
    loading.value = true;
    error.value = "";
    try {
      const [page, types] = await Promise.all([listRooms({ limit: 100 }), listRoomTypes()]);
      rooms.value = page.items;
      roomTypes.value = types;
    } catch (err) {
      console.error("Error al cargar los alojamientos:", err);
      error.value = "No fue posible cargar las habitaciones en este momento.";
      rooms.value = [];
    } finally {
      loading.value = false;
    }
  }

  return { rooms, roomTypes, sections, loading, error, load };
}
