<script setup>
import { ref, onMounted, computed, watch } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import {
  listRooms,
  createRoom,
  updateRoom,
  deleteRoom,
  addRoomImages,
  removeRoomImage,
  listRoomTypes,
  createRoomType,
  updateRoomType,
} from "@/api/rooms";
import { assetUrl } from "@/config/env";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { PERMISSIONS } from "@/constants/booking";
import { formatMoney } from "@/utils/format";
import ImageUploader from "@/components/ImageUploader.vue";
import RoomCalendarModal from "@/components/RoomCalendarModal.vue";
import RoomHistoryModal from "@/components/RoomHistoryModal.vue";

const auth = useAuthStore();
const configStore = useConfigStore();

const puedeEditar = computed(() => auth.can(PERMISSIONS.ROOMS_WRITE));
const puedeVerHistorial = computed(() => auth.can(PERMISSIONS.AUDIT_READ));
const puedeReservar = computed(() => auth.can(PERMISSIONS.BOOKINGS_CREATE_MANUAL));

const OPERATIONAL_STATUS = {
  available: { label: "Disponible", icon: "fa-solid fa-leaf", badge: "badge-soft-success" },
  cleaning: { label: "En limpieza", icon: "fa-solid fa-broom", badge: "badge-soft-maintenance" },
  maintenance: { label: "En mantenimiento", icon: "fa-solid fa-user-gear", badge: "badge-soft-warning" },
  out_of_service: { label: "Fuera de servicio", icon: "fa-solid fa-ban", badge: "badge-soft-danger" },
};

const MAX_FOTOS = 5;
const LIMITE = 50;

const isLoading = ref(true);
const habitaciones = ref([]);
const totalHabitaciones = ref(0);
const paginaActual = ref(1);
const totalPaginas = computed(() => Math.max(1, Math.ceil(totalHabitaciones.value / LIMITE)));
const roomFilter = ref("all");
const busqueda = ref("");
const filtroTipo = ref("");
const tiposHabitacion = ref([]);
const isSubmitting = ref(false);

const habitacionesFiltradas = computed(() => {
  if (roomFilter.value === "active") return habitaciones.value.filter((hab) => hab.is_active);
  if (roomFilter.value === "inactive") return habitaciones.value.filter((hab) => !hab.is_active);
  if (roomFilter.value === "attention") {
    return habitaciones.value.filter((hab) => hab.operational_status !== "available");
  }
  return habitaciones.value;
});

const roomCounts = computed(() => ({
  all: habitaciones.value.length,
  active: habitaciones.value.filter((hab) => hab.is_active).length,
  inactive: habitaciones.value.filter((hab) => !hab.is_active).length,
  attention: habitaciones.value.filter((hab) => hab.operational_status !== "available").length,
}));

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_APPLE = getBrandColor("--k-apple", "#8BCF5B");
const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");
const COLOR_DANGER = getBrandColor("--k-danger", "#e74c3c");

const money = (value) => formatMoney(value, configStore.data.currency);
const statusMeta = (status) => OPERATIONAL_STATUS[status] || OPERATIONAL_STATUS.available;

const uploaderRef = ref(null);
const isEditing = ref(false);

const initialFormState = () => ({
  number: "",
  name: "",
  room_type_id: "",
  description: "",
  price_per_night: "",
  capacity: 1,
  bedrooms: 1,
  beds: "",
  amenities: [],
  is_active: true,
  operational_status: "available",
  images: [],
  main_image: null,
});

const EDITABLE_FIELDS = [
  "number",
  "name",
  "room_type_id",
  "description",
  "price_per_night",
  "capacity",
  "bedrooms",
  "beds",
  "amenities",
  "is_active",
  "operational_status",
  "main_image",
];

const roomForm = ref(initialFormState());
let originalForm = null;
const currentRoomId = ref(null);
const imagenesParaCargar = ref([]);
const closeBtnRef = ref(null);
const modalVisible = ref(false);
const habitacionSeleccionada = ref(null);
const historialVisible = ref(false);
const habitacionHistorial = ref(null);

const cargarTipos = async () => {
  try {
    tiposHabitacion.value = await listRoomTypes(true);
  } catch (error) {
    tiposHabitacion.value = [];
  }
};

const cargarHabitaciones = async () => {
  isLoading.value = true;
  try {
    const params = { include_inactive: true, page: paginaActual.value, limit: LIMITE };
    if (busqueda.value.trim()) params.q = busqueda.value.trim();
    if (filtroTipo.value) params.room_type = filtroTipo.value;
    const data = await listRooms(params);
    habitaciones.value = data.items || [];
    totalHabitaciones.value = data.total || 0;
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudieron cargar las habitaciones."), "error");
  } finally {
    isLoading.value = false;
  }
};

let timeoutBusqueda = null;
watch(busqueda, () => {
  clearTimeout(timeoutBusqueda);
  timeoutBusqueda = setTimeout(() => {
    paginaActual.value = 1;
    cargarHabitaciones();
  }, 350);
});

watch(filtroTipo, () => {
  paginaActual.value = 1;
  cargarHabitaciones();
});

const cambiarPagina = (pagina) => {
  if (pagina >= 1 && pagina <= totalPaginas.value) {
    paginaActual.value = pagina;
    cargarHabitaciones();
  }
};

onMounted(() => {
  configStore.fetchSiteConfig();
  cargarTipos();
  cargarHabitaciones();
});

const resetForm = () => {
  roomForm.value = initialFormState();
  originalForm = null;
  isEditing.value = false;
  currentRoomId.value = null;
  imagenesParaCargar.value = [];
  if (uploaderRef.value) uploaderRef.value.reset();
};

const prepararCreacion = () => resetForm();

const formDesdeHabitacion = (hab) => ({
  number: hab.number,
  name: hab.name,
  room_type_id: hab.room_type?.id || "",
  description: hab.description || "",
  price_per_night: hab.price_per_night,
  capacity: hab.capacity,
  bedrooms: hab.bedrooms || 1,
  beds: hab.beds || "",
  amenities: [...(hab.amenities || [])],
  is_active: hab.is_active,
  operational_status: hab.operational_status || "available",
  images: [...(hab.images || [])],
  main_image: hab.main_image || null,
});

const prepararEdicion = (hab) => {
  resetForm();
  isEditing.value = true;
  currentRoomId.value = hab.id;
  roomForm.value = formDesdeHabitacion(hab);
  originalForm = JSON.parse(JSON.stringify(roomForm.value));
};

const normalizar = (form) => ({
  number: String(form.number).trim(),
  name: form.name.trim(),
  room_type_id: form.room_type_id,
  description: (form.description || "").trim(),
  price_per_night: Number(form.price_per_night),
  capacity: Number(form.capacity),
  bedrooms: Number(form.bedrooms),
  beds: (form.beds || "").trim(),
  amenities: form.amenities,
  is_active: form.is_active,
  operational_status: form.operational_status,
  main_image: form.main_image,
});

const camposModificados = () => {
  const actual = normalizar(roomForm.value);
  const antes = normalizar(originalForm);
  const cambios = {};
  EDITABLE_FIELDS.forEach((campo) => {
    if (JSON.stringify(actual[campo]) !== JSON.stringify(antes[campo])) cambios[campo] = actual[campo];
  });
  return cambios;
};

const guardarHabitacion = async () => {
  const { number, name, price_per_night, room_type_id } = roomForm.value;

  if (
    !number ||
    !name ||
    !price_per_night ||
    !room_type_id ||
    (!isEditing.value && imagenesParaCargar.value.length === 0)
  ) {
    Swal.fire({
      icon: "error",
      title: "Faltan algunos datos",
      text: "Completa la información principal, el tipo de habitación y al menos una foto para continuar.",
    });
    return;
  }

  isSubmitting.value = true;
  try {
    const archivos = imagenesParaCargar.value;

    if (isEditing.value) {
      const cambios = camposModificados();
      if (Object.keys(cambios).length) await updateRoom(currentRoomId.value, cambios);
      if (archivos.length > 0) await addRoomImages(currentRoomId.value, archivos);
      Swal.fire({
        icon: "success",
        title: "Espacio actualizado",
        text: "Los cambios de la habitación quedaron guardados.",
        timer: 1800,
        showConfirmButton: false,
      });
    } else {
      const { main_image: _mainImage, ...payload } = normalizar(roomForm.value);
      const creada = await createRoom(payload);
      try {
        await addRoomImages(creada.id, archivos);
        Swal.fire({
          icon: "success",
          title: "Espacio registrado",
          text: "La habitación ahora está lista para recibir huéspedes.",
          timer: 1800,
          showConfirmButton: false,
        });
      } catch (error) {
        Swal.fire(
          "Habitación creada sin fotos",
          errorMessage(error, "No se pudieron subir las fotos. Edítala para intentarlo de nuevo."),
          "warning",
        );
      }
    }

    resetForm();
    if (closeBtnRef.value) closeBtnRef.value.click();
  } catch (error) {
    Swal.fire({
      icon: "error",
      title: "No pudimos guardar este espacio",
      text: errorMessage(error, "Verifica los datos o tu conexión e inténtalo nuevamente."),
    });
  } finally {
    isSubmitting.value = false;
    await cargarHabitaciones();
  }
};

const eliminarHabitacion = async (hab) => {
  const result = await Swal.fire({
    title: "¿Deseas retirar esta habitación del inventario?",
    text: "Solo se pueden eliminar habitaciones sin reservas registradas.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: COLOR_APPLE,
    cancelButtonColor: COLOR_FOREST,
    confirmButtonText: "Sí, retirarla",
    cancelButtonText: "Conservar",
  });

  if (!result.isConfirmed) return;
  try {
    await deleteRoom(hab.id);
    Swal.fire({
      icon: "success",
      title: "Espacio retirado",
      text: "La lista quedó actualizada correctamente.",
      timer: 1600,
      showConfirmButton: false,
    });
    await cargarHabitaciones();
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
  }
};

const eliminarImagenExistente = async (imageUrl) => {
  const result = await Swal.fire({
    title: "¿Borrar esta foto?",
    text: "Se eliminará permanentemente.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: COLOR_DANGER,
    cancelButtonColor: COLOR_FOREST,
    confirmButtonText: "Sí, borrar",
    cancelButtonText: "Cancelar",
  });

  if (!result.isConfirmed) return;
  try {
    const actualizada = await removeRoomImage(currentRoomId.value, imageUrl);
    roomForm.value.images = [...(actualizada.images || [])];
    roomForm.value.main_image = actualizada.main_image || null;
    originalForm.images = [...roomForm.value.images];
    originalForm.main_image = roomForm.value.main_image;
    Swal.fire({ icon: "success", title: "Foto eliminada", timer: 1500, showConfirmButton: false });
    await cargarHabitaciones();
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo eliminar la foto"), "error");
  }
};

const SIN_FOTO =
  "data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%2260%22%20height%3D%2250%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2060%2050%22%20preserveAspectRatio%3D%22none%22%3E%3Crect%20width%3D%2260%22%20height%3D%2250%22%20fill%3D%22%23eeeeee%22%2F%3E%3Ctext%20text-anchor%3D%22middle%22%20x%3D%2230%22%20y%3D%2230%22%20style%3D%22fill%3A%23aaaaaa%3Bfont-weight%3Abold%3Bfont-size%3A10px%3Bfont-family%3AArial%2CHelvetica%2Csans-serif%22%3ESin%20Foto%3C%2Ftext%3E%3C%2Fsvg%3E";

const manejarErrorImagen = (e) => {
  e.target.onerror = null;
  e.target.src = SIN_FOTO;
};

// La foto principal se guarda junto con el resto de cambios al pulsar "Guardar cambios".
const seleccionarPrincipal = (imgUrl) => {
  roomForm.value.main_image = imgUrl;
};

const abrirCalendario = (habitacion) => {
  if (!habitacion) return;
  habitacionSeleccionada.value = { ...habitacion };
  modalVisible.value = true;
};

const cerrarCalendario = () => {
  modalVisible.value = false;
  habitacionSeleccionada.value = null;
};

const abrirHistorial = (habitacion) => {
  habitacionHistorial.value = habitacion;
  historialVisible.value = true;
};

const listaAmenidadesBase = [
  "Aire Acondicionado",
  "Ventilador",
  "Televisión",
  "Wifi",
  "Baño Privado",
  "Nevera / Minibar",
  "Zonas Verdes",
  "Vista a la Selva",
  "Malla Catamarán",
  "Tina / Jacuzzi",
  "Balcón",
];

// Incluye amenidades ya guardadas en la habitación aunque no estén en la lista base.
const listaAmenidades = computed(() => [
  ...listaAmenidadesBase,
  ...(roomForm.value.amenities || []).filter((a) => !listaAmenidadesBase.includes(a)),
]);

// --- Tipos de habitación (catálogo) ---
const mostrarTipos = ref(false);
const tipoForm = ref({ id: null, code: "", name: "", description: "", is_active: true, sort_order: 0 });
const guardandoTipo = ref(false);

const limpiarTipoForm = () => {
  tipoForm.value = { id: null, code: "", name: "", description: "", is_active: true, sort_order: 0 };
};

const editarTipo = (tipo) => {
  tipoForm.value = { ...tipo };
};

const guardarTipo = async () => {
  guardandoTipo.value = true;
  try {
    const { id, code, name, description, is_active, sort_order } = tipoForm.value;
    const datos = {
      name: name.trim(),
      description: (description || "").trim(),
      is_active,
      sort_order: Number(sort_order) || 0,
    };
    if (id) await updateRoomType(id, datos);
    else await createRoomType({ code: code.trim().toLowerCase(), ...datos });
    limpiarTipoForm();
    await cargarTipos();
    Swal.fire({
      icon: "success",
      title: "Tipo de habitación guardado",
      timer: 1400,
      showConfirmButton: false,
    });
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo guardar el tipo de habitación."), "error");
  } finally {
    guardandoTipo.value = false;
  }
};
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

      <div v-if="puedeEditar" class="d-flex gap-2 flex-wrap">
        <button class="btn btn-soft-sky shadow-sm rounded-pill px-4" @click="mostrarTipos = !mostrarTipos">
          <font-awesome-icon icon="fa-solid fa-tag" class="me-2" />
          Tipos de habitación
        </button>
        <button
          class="btn btn-brand shadow-sm rounded-pill px-4"
          data-bs-toggle="modal"
          data-bs-target="#modalHabitacion"
          @click="prepararCreacion"
        >
          <font-awesome-icon icon="fa-solid fa-leaf" class="me-2" />
          Nueva Habitación
        </button>
      </div>
    </div>

    <div v-if="puedeEditar && mostrarTipos" class="card eco-card border-0 shadow-sm rounded-4 p-3 mb-4">
      <h6 class="fw-bold mb-3">Tipos de habitación</h6>
      <div class="table-responsive mb-3">
        <table class="table table-sm align-middle mb-0">
          <thead class="table-soft">
            <tr>
              <th class="small text-muted">Código</th>
              <th class="small text-muted">Nombre</th>
              <th class="small text-muted">Orden</th>
              <th class="small text-muted">Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!tiposHabitacion.length">
              <td colspan="5" class="text-muted small text-center py-3">Aún no hay tipos registrados.</td>
            </tr>
            <tr v-for="tipo in tiposHabitacion" :key="tipo.id">
              <td>
                <code>{{ tipo.code }}</code>
              </td>
              <td>{{ tipo.name }}</td>
              <td>{{ tipo.sort_order }}</td>
              <td>
                <span class="badge" :class="tipo.is_active ? 'bg-success' : 'bg-secondary'">
                  {{ tipo.is_active ? "Activo" : "Inactivo" }}
                </span>
              </td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-secondary rounded-pill" @click="editarTipo(tipo)">
                  <font-awesome-icon icon="fa-regular fa-pen-to-square" /> Editar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <form class="row g-2 align-items-end" @submit.prevent="guardarTipo">
        <div class="col-md-2">
          <label class="form-label small fw-bold mb-1">Código</label>
          <input
            v-model="tipoForm.code"
            type="text"
            class="form-control form-control-sm"
            placeholder="cabana"
            :disabled="!!tipoForm.id"
            required
            pattern="[a-z0-9\-]{2,40}"
            title="Minúsculas, números y guiones"
          />
        </div>
        <div class="col-md-3">
          <label class="form-label small fw-bold mb-1">Nombre</label>
          <input
            v-model="tipoForm.name"
            type="text"
            class="form-control form-control-sm"
            placeholder="Cabaña"
            required
            minlength="2"
          />
        </div>
        <div class="col-md-3">
          <label class="form-label small fw-bold mb-1">Descripción</label>
          <input v-model="tipoForm.description" type="text" class="form-control form-control-sm" />
        </div>
        <div class="col-md-1">
          <label class="form-label small fw-bold mb-1">Orden</label>
          <input v-model="tipoForm.sort_order" type="number" class="form-control form-control-sm" />
        </div>
        <div class="col-md-1">
          <div class="form-check mb-1">
            <input id="tipo-activo" v-model="tipoForm.is_active" class="form-check-input" type="checkbox" />
            <label class="form-check-label small" for="tipo-activo">Activo</label>
          </div>
        </div>
        <div class="col-md-2 d-flex gap-1">
          <button type="submit" class="btn btn-sm btn-brand flex-grow-1" :disabled="guardandoTipo">
            {{ tipoForm.id ? "Actualizar" : "Agregar" }}
          </button>
          <button
            v-if="tipoForm.id"
            type="button"
            class="btn btn-sm btn-light border"
            @click="limpiarTipoForm"
          >
            <font-awesome-icon icon="fa-solid fa-xmark" />
          </button>
        </div>
      </form>
    </div>

    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
      <div class="filter-chip-group">
        <button class="filter-chip" :class="{ active: roomFilter === 'all' }" @click="roomFilter = 'all'">
          <font-awesome-icon icon="fa-solid fa-bed" class="me-2" />
          Todas
          <span class="chip-count">{{ roomCounts.all }}</span>
        </button>
        <button
          class="filter-chip"
          :class="{ active: roomFilter === 'active' }"
          @click="roomFilter = 'active'"
        >
          <font-awesome-icon icon="fa-solid fa-leaf" class="me-2" />
          Habilitadas
          <span class="chip-count">{{ roomCounts.active }}</span>
        </button>
        <button
          class="filter-chip"
          :class="{ active: roomFilter === 'inactive' }"
          @click="roomFilter = 'inactive'"
        >
          <font-awesome-icon icon="fa-solid fa-ban" class="me-2" />
          No habilitadas
          <span class="chip-count">{{ roomCounts.inactive }}</span>
        </button>
        <button
          class="filter-chip"
          :class="{ active: roomFilter === 'attention' }"
          @click="roomFilter = 'attention'"
        >
          <font-awesome-icon icon="fa-solid fa-broom" class="me-2" />
          Limpieza / mantenimiento
          <span class="chip-count">{{ roomCounts.attention }}</span>
        </button>
      </div>

      <div class="d-flex gap-2 flex-wrap">
        <select v-model="filtroTipo" class="form-select form-select-sm rounded-pill" style="max-width: 200px">
          <option value="">Todos los tipos</option>
          <option v-for="tipo in tiposHabitacion" :key="tipo.id" :value="tipo.code">{{ tipo.name }}</option>
        </select>
        <input
          v-model="busqueda"
          type="text"
          class="form-control form-control-sm rounded-pill"
          style="max-width: 240px"
          placeholder="Buscar por nombre o número..."
        />
      </div>
    </div>

    <div class="card eco-card border-0 shadow-sm rounded-4 overflow-hidden">
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
            <tr v-if="isLoading">
              <td colspan="6" class="text-center py-5">
                <div class="spinner-border" style="color: var(--k-apple)" role="status"></div>
                <p class="brand-handmade mt-3 mb-0">Preparando los espacios del hotel...</p>
              </td>
            </tr>

            <tr v-else-if="habitacionesFiltradas.length === 0">
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
              <tr v-for="hab in habitacionesFiltradas" :key="hab.id" class="align-middle">
                <td class="ps-4">
                  <div class="d-flex align-items-center">
                    <img
                      :src="assetUrl(hab.main_image) || SIN_FOTO"
                      class="rounded me-3 border shadow-sm"
                      style="width: 60px; height: 50px; object-fit: cover"
                      alt=""
                      @error="manejarErrorImagen"
                    />
                    <div>
                      <div class="fw-bold text-brand">{{ hab.name }}</div>
                      <small class="text-muted"
                        >N° {{ hab.number
                        }}<span v-if="hab.room_type"> · {{ hab.room_type.name }}</span></small
                      >
                    </div>
                  </div>
                </td>

                <td class="fw-semibold text-brand">
                  {{ money(hab.price_per_night) }}
                </td>

                <td class="text-muted">{{ hab.capacity }} pers.</td>

                <td>
                  <span
                    class="badge px-3 py-2 rounded-pill"
                    :class="statusMeta(hab.operational_status).badge"
                  >
                    <font-awesome-icon :icon="statusMeta(hab.operational_status).icon" class="me-1" />
                    {{ statusMeta(hab.operational_status).label }}
                  </span>
                  <div v-if="!hab.is_active" class="small text-muted mt-1">
                    <font-awesome-icon icon="fa-solid fa-eye-slash" class="me-1" /> No habilitada para la
                    venta
                  </div>
                </td>

                <td class="text-center align-middle">
                  <button
                    v-if="puedeReservar"
                    class="btn btn-sm btn-soft-sky rounded-pill px-3 fw-medium shadow-sm"
                    style="font-size: 0.82rem"
                    @click="abrirCalendario(hab)"
                  >
                    <font-awesome-icon icon="fa-solid fa-calendar-days" class="me-1" /> Ver Fechas
                  </button>
                </td>

                <td class="text-center align-middle">
                  <div class="d-flex justify-content-center gap-2">
                    <button
                      v-if="puedeVerHistorial"
                      class="btn btn-sm btn-outline-dark rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Historial de cambios"
                      @click="abrirHistorial(hab)"
                    >
                      <font-awesome-icon icon="fa-solid fa-clock" class="fs-6" />
                    </button>

                    <template v-if="puedeEditar">
                      <button
                        class="btn btn-sm btn-outline-secondary rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                        style="width: 35px; height: 35px"
                        data-bs-toggle="modal"
                        data-bs-target="#modalHabitacion"
                        title="Editar habitación"
                        @click="prepararEdicion(hab)"
                      >
                        <font-awesome-icon icon="fa-regular fa-pen-to-square" class="fs-6" />
                      </button>

                      <button
                        class="btn btn-sm btn-outline-danger rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                        style="width: 35px; height: 35px"
                        title="Retirar habitación"
                        @click="eliminarHabitacion(hab)"
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

      <div
        v-if="totalPaginas > 1"
        class="d-flex justify-content-between align-items-center p-3 bg-light border-top"
      >
        <span class="text-muted small fw-bold">Página {{ paginaActual }} de {{ totalPaginas }}</span>
        <div class="btn-group shadow-sm">
          <button
            class="btn btn-sm btn-white border"
            :disabled="paginaActual === 1"
            @click="cambiarPagina(paginaActual - 1)"
          >
            <font-awesome-icon icon="fa-solid fa-chevron-left" class="me-1" /> Anterior
          </button>
          <button
            class="btn btn-sm btn-white border"
            :disabled="paginaActual >= totalPaginas"
            @click="cambiarPagina(paginaActual + 1)"
          >
            Siguiente <font-awesome-icon icon="fa-solid fa-chevron-right" class="ms-1" />
          </button>
        </div>
      </div>
    </div>

    <div v-if="puedeEditar" id="modalHabitacion" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content border-0 shadow-lg eco-card">
          <div class="modal-header modal-soft-header border-0">
            <h5 class="modal-title section-title mb-0">
              <font-awesome-icon :icon="isEditing ? 'fa-solid fa-bed' : 'fa-solid fa-leaf'" class="me-2" />
              {{ isEditing ? "Editar Habitación" : "Registrar Habitación" }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" @click="resetForm"></button>
          </div>

          <form @submit.prevent="guardarHabitacion">
            <div class="modal-body p-4">
              <div class="row g-3">
                <div class="col-md-4">
                  <label class="form-label fw-bold">N° Habitación</label>
                  <input v-model="roomForm.number" type="text" class="form-control" required maxlength="20" />
                </div>

                <div class="col-md-8">
                  <label class="form-label fw-bold">Nombre</label>
                  <input
                    v-model="roomForm.name"
                    type="text"
                    class="form-control"
                    required
                    minlength="2"
                    maxlength="120"
                  />
                </div>

                <div class="col-md-6">
                  <label class="form-label fw-bold">Precio por noche</label>
                  <input
                    v-model="roomForm.price_per_night"
                    type="number"
                    min="1"
                    step="any"
                    class="form-control"
                    required
                  />
                </div>

                <div class="col-md-6">
                  <label class="form-label fw-bold">Capacidad Total (Pers.)</label>
                  <input
                    v-model="roomForm.capacity"
                    type="number"
                    min="1"
                    max="50"
                    class="form-control"
                    required
                  />
                </div>

                <div class="col-md-6">
                  <label class="form-label fw-bold">Tipo de Alojamiento</label>
                  <select v-model="roomForm.room_type_id" class="form-select" required>
                    <option value="" disabled>Selecciona una opción...</option>
                    <option v-for="tipo in tiposHabitacion" :key="tipo.id" :value="tipo.id">
                      {{ tipo.name }}{{ tipo.is_active ? "" : " (inactivo)" }}
                    </option>
                  </select>
                  <small v-if="!tiposHabitacion.length" class="text-muted"
                    >Primero crea un tipo en "Tipos de habitación".</small
                  >
                </div>

                <div class="col-md-6">
                  <label class="form-label fw-bold">N° de Habitaciones (Cuartos)</label>
                  <input
                    v-model="roomForm.bedrooms"
                    type="number"
                    min="1"
                    max="20"
                    class="form-control"
                    required
                  />
                </div>

                <div class="col-12 mt-3">
                  <label class="form-label fw-bold">Distribución de Camas</label>
                  <input
                    v-model="roomForm.beds"
                    type="text"
                    class="form-control"
                    maxlength="200"
                    placeholder="Ej: 1 Cama Doble, 2 Sencillas"
                  />
                  <small class="text-muted"
                    >Este texto es el que verá el cliente en la tarjeta principal.</small
                  >
                </div>

                <div class="col-md-6 mt-3">
                  <label class="form-label fw-bold">Estado Operativo</label>
                  <select v-model="roomForm.operational_status" class="form-select">
                    <option v-for="(meta, value) in OPERATIONAL_STATUS" :key="value" :value="value">
                      {{ meta.label }}
                    </option>
                  </select>
                </div>

                <div class="col-md-6 mt-3 d-flex align-items-end">
                  <div class="form-check form-switch mb-2">
                    <input
                      id="room-is-active"
                      v-model="roomForm.is_active"
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                    />
                    <label class="form-check-label fw-bold" for="room-is-active"
                      >Habilitada para la venta</label
                    >
                  </div>
                </div>

                <div class="col-12 mt-3">
                  <label class="form-label fw-bold">Descripción de la Habitación</label>
                  <textarea
                    v-model="roomForm.description"
                    class="form-control border-light-subtle shadow-sm"
                    rows="2"
                    maxlength="3000"
                    placeholder="Ej: Cabaña romántica ideal para parejas..."
                  ></textarea>
                </div>

                <div class="col-12 mt-4">
                  <label class="form-label fw-bold mb-3 border-bottom pb-2 w-100"
                    >¿Qué incluye la habitación? (Amenidades)</label
                  >
                  <div class="row g-2">
                    <div
                      v-for="(amenidad, index) in listaAmenidades"
                      :key="amenidad"
                      class="col-md-4 col-sm-6"
                    >
                      <div
                        class="form-check form-switch p-2 rounded bg-light border border-light-subtle transition-all"
                        :class="{
                          'border-success bg-success-subtle':
                            roomForm.amenities && roomForm.amenities.includes(amenidad),
                        }"
                      >
                        <input
                          :id="'amenidad-' + index"
                          v-model="roomForm.amenities"
                          class="form-check-input ms-1 me-2"
                          type="checkbox"
                          role="switch"
                          :value="amenidad"
                        />
                        <label
                          class="form-check-label text-dark"
                          :for="'amenidad-' + index"
                          style="cursor: pointer"
                        >
                          {{ amenidad }}
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="isEditing && roomForm.images && roomForm.images.length" class="col-12 mt-4">
                  <label class="form-label fw-bold mb-1">Fotos Actuales de la Habitación</label>
                  <p class="text-muted small mb-3">
                    Haz clic en la <font-awesome-icon icon="fa-solid fa-star" class="tone-sand" /> para elegir
                    la foto principal (se guarda con "Guardar cambios").
                  </p>

                  <div class="row g-2">
                    <div v-for="imgUrl in roomForm.images" :key="imgUrl" class="col-4 col-md-3">
                      <div
                        class="card h-100 p-1 position-relative border transition-all photo-card"
                        :class="{
                          'border-success border-2 shadow principal-highlight':
                            imgUrl === roomForm.main_image,
                        }"
                      >
                        <span
                          v-if="imgUrl === roomForm.main_image"
                          class="position-absolute principal-badge rounded-pill bg-success text-white shadow-sm px-2"
                          style="top: -5px; left: -5px; font-size: 0.75rem; z-index: 2"
                        >
                          Principal
                        </span>

                        <img
                          :src="assetUrl(imgUrl)"
                          class="rounded object-fit-cover w-100"
                          style="height: 90px"
                          alt=""
                        />

                        <button
                          type="button"
                          class="btn btn-danger btn-sm position-absolute rounded-circle d-inline-flex align-items-center justify-content-center shadow"
                          style="width: 28px; height: 28px; bottom: 5px; right: 5px"
                          title="Eliminar foto"
                          @click.stop="eliminarImagenExistente(imgUrl)"
                        >
                          <font-awesome-icon icon="fa-solid fa-trash" class="image-action-icon" />
                        </button>

                        <button
                          v-if="imgUrl !== roomForm.main_image"
                          type="button"
                          class="btn btn-light btn-sm position-absolute rounded-circle d-inline-flex align-items-center justify-content-center shadow"
                          style="width: 28px; height: 28px; bottom: 5px; left: 5px"
                          title="Hacer foto principal"
                          @click.stop="seleccionarPrincipal(imgUrl)"
                        >
                          <font-awesome-icon icon="fa-solid fa-star" class="image-action-icon tone-sand" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="col-12 mt-3">
                  <ImageUploader
                    ref="uploaderRef"
                    v-model="imagenesParaCargar"
                    :max-files="MAX_FOTOS"
                    :existing-count="roomForm.images ? roomForm.images.length : 0"
                    :is-editing="isEditing"
                  />
                </div>
              </div>
            </div>

            <div class="modal-footer border-0 p-4 pt-0">
              <button
                ref="closeBtnRef"
                type="button"
                class="btn btn-light border px-4 rounded-pill"
                data-bs-dismiss="modal"
                @click="resetForm"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="btn btn-brand px-4 rounded-pill shadow-sm"
                :disabled="isSubmitting"
              >
                {{ isSubmitting ? "Guardando..." : isEditing ? "Guardar cambios" : "Guardar habitación" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <RoomCalendarModal
      v-if="modalVisible && habitacionSeleccionada"
      :show="modalVisible"
      :habitacion="habitacionSeleccionada"
      @close="cerrarCalendario"
      @reserva-creada="cargarHabitaciones"
    />

    <RoomHistoryModal
      v-if="puedeVerHistorial"
      :show="historialVisible"
      :room-id="habitacionHistorial?.id"
      :room-label="habitacionHistorial ? `${habitacionHistorial.number} · ${habitacionHistorial.name}` : ''"
      @close="historialVisible = false"
    />
  </div>
</template>

<style scoped>
.filter-chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.btn-brand:hover {
  box-shadow: 0 10px 22px rgba(139, 207, 91, 0.18);
}

.filter-chip {
  border: 1px solid var(--k-border);
  background: var(--k-offwhite);
  padding: 0.65rem 1rem;
  border-radius: 999px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.filter-chip:hover {
  background: var(--k-apple-soft);
  border-color: rgba(139, 207, 91, 0.4);
}

.filter-chip.active {
  background: rgba(139, 207, 91, 0.2);
  color: var(--k-forest);
  border-color: rgba(139, 207, 91, 0.45);
  box-shadow: 0 8px 18px rgba(139, 207, 91, 0.14);
}

.chip-count {
  margin-left: 0.45rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  font-size: 0.75rem;
}

.tone-sand {
  color: var(--k-sand);
}

.image-action-icon {
  font-size: 0.8rem;
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

.modal-soft-header {
  background: linear-gradient(135deg, var(--k-sky-soft) 0%, var(--k-offwhite) 100%);
}

.border-dashed {
  border-style: dashed !important;
}

.photo-card {
  overflow: hidden;
}

.principal-highlight {
  background-color: rgba(139, 207, 91, 0.12);
}

.principal-badge {
  top: -6px;
  left: -6px;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 3px 8px;
  z-index: 5;
}

.action-btn {
  bottom: 8px;
  opacity: 0;
  transform: scale(0.8);
  width: 28px;
  height: 28px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: all 0.2s ease-in-out;
}

.btn-trash {
  right: 8px;
}
.btn-star {
  right: 42px;
}

.photo-card:hover .action-btn {
  opacity: 1;
  transform: scale(1);
}
</style>
