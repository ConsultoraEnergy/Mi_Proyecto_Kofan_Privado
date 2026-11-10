<script setup>
import { ref, computed, reactive, watch, onMounted, onUnmounted } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { getBookedDates, getQuote } from "@/api/rooms";
import { createManualBooking } from "@/api/bookings";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { DOCUMENT_TYPES, PERMISSIONS } from "@/constants/booking";
import { formatMoney, fromIsoDate, toIsoDate, nightsBetween } from "@/utils/format";
import { DatePicker as VDatePicker } from "v-calendar";
import "v-calendar/style.css";

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");

const props = defineProps({
  show: Boolean,
  habitacion: { type: Object, default: null },
});

const emit = defineEmits(["close", "reservaCreada"]);

const auth = useAuthStore();
const configStore = useConfigStore();
const puedeAjustarPrecio = computed(() => auth.can(PERMISSIONS.BOOKINGS_OVERRIDE_PRICE));

const pasoActual = ref(1);
const guardando = ref(false);
const reservasOcupadas = ref([]);
const minDate = ref(new Date());
const columnasCalendario = ref(window.innerWidth >= 768 ? 2 : 1);
const cotizacion = ref(null);
const errorCotizacion = ref("");
const errorFechas = ref("");

const actualizarColumnas = () => {
  columnasCalendario.value = window.innerWidth >= 768 ? 2 : 1;
};

onMounted(() => window.addEventListener("resize", actualizarColumnas));
onUnmounted(() => window.removeEventListener("resize", actualizarColumnas));

const range = ref({
  start: null,
  end: null,
});

const formularioAdmin = reactive({
  full_name: "",
  email: "",
  phone: "",
  document_type: "",
  document_number: "",
  precio_negociado: "",
  notes: "",
});

const money = (value) => formatMoney(value, configStore.data.currency);
const vacioANulo = (value) => {
  const limpio = typeof value === "string" ? value.trim() : value;
  return limpio === "" || limpio === undefined ? null : limpio;
};

const checkIn = computed(() => toIsoDate(range.value?.start));
const checkOut = computed(() => toIsoDate(range.value?.end));
const noches = computed(() => nightsBetween(checkIn.value, checkOut.value));
const rangeComplete = computed(() => !!(checkIn.value && checkOut.value && noches.value > 0));

// Precio calculado por el servidor para el rango elegido.
watch([checkIn, checkOut], async () => {
  cotizacion.value = null;
  errorCotizacion.value = "";
  if (!rangeComplete.value || !props.habitacion?.id) return;
  try {
    cotizacion.value = await getQuote(props.habitacion.id, checkIn.value, checkOut.value);
  } catch (error) {
    errorCotizacion.value = errorMessage(error, "No se pudo calcular el precio.");
  }
});

const cargarFechasOcupadas = async () => {
  errorFechas.value = "";
  if (!props.habitacion?.id) return;
  try {
    const rangos = await getBookedDates(props.habitacion.id);
    // El día de salida queda libre: se bloquea desde la entrada hasta la noche anterior a la salida.
    reservasOcupadas.value = (rangos || []).map(({ check_in, check_out }) => {
      const end = fromIsoDate(check_out);
      end.setDate(end.getDate() - 1);
      return { start: fromIsoDate(check_in), end };
    });
  } catch (error) {
    reservasOcupadas.value = [];
    errorFechas.value = errorMessage(error, "No se pudieron cargar las fechas ocupadas.");
  }
};

watch(
  () => props.show,
  (visible) => {
    if (visible && props.habitacion) {
      configStore.fetchSiteConfig();
      cargarFechasOcupadas();
    }
    if (!visible) {
      range.value = { start: null, end: null };
      reservasOcupadas.value = [];
    }
  },
);

watch(
  () => props.habitacion,
  (nueva) => {
    if (props.show && nueva) cargarFechasOcupadas();
  },
);

const attributes = computed(() => [
  {
    key: "ocupado",
    highlight: {
      color: "red",
      fillMode: "light",
    },
    dates: reservasOcupadas.value,
    popover: {
      label: "Reservado",
      visibility: "hover",
    },
  },
]);

const formatoCorto = (date) => date?.toLocaleDateString("es-CO", { day: "numeric", month: "short" });
const fechaEntradaCorta = computed(() => formatoCorto(range.value?.start));
const fechaSalidaCorta = computed(() => formatoCorto(range.value?.end));
const fechaEntradaFormateada = computed(() =>
  range.value?.start?.toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" }),
);
const fechaSalidaFormateada = computed(() =>
  range.value?.end?.toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" }),
);

const avanzarPaso = () => {
  if (rangeComplete.value) {
    pasoActual.value = 2;
  }
};

const crearReservaAdmin = async () => {
  if (!props.habitacion?.id || !rangeComplete.value) return;
  guardando.value = true;

  const payload = {
    room_id: props.habitacion.id,
    check_in: checkIn.value,
    check_out: checkOut.value,
    guest: {
      full_name: formularioAdmin.full_name.trim(),
      email: formularioAdmin.email.trim(),
      phone: vacioANulo(formularioAdmin.phone),
      document_type: vacioANulo(formularioAdmin.document_type),
      document_number: vacioANulo(formularioAdmin.document_number),
    },
    notes: vacioANulo(formularioAdmin.notes),
  };
  // Precio negociado: solo con permiso explícito; si no, el servidor aplica la tarifa.
  if (
    puedeAjustarPrecio.value &&
    formularioAdmin.precio_negociado !== "" &&
    formularioAdmin.precio_negociado !== null
  ) {
    payload.total_amount = Number(formularioAdmin.precio_negociado);
  }

  try {
    const reserva = await createManualBooking(payload);

    Swal.fire({
      title: "¡Reserva Confirmada!",
      text: `La reserva ${reserva?.code || ""} quedó confirmada por ${money(reserva?.total_amount)}.`,
      icon: "success",
      confirmButtonColor: COLOR_FOREST,
    });

    emit("reservaCreada");
    cerrar();
  } catch (error) {
    Swal.fire({
      title: "No se pudo crear la reserva",
      text: errorMessage(error, "Verifique los datos e intente de nuevo."),
      icon: "error",
      confirmButtonColor: COLOR_FOREST,
    });
    if (error?.response?.status === 409) cargarFechasOcupadas();
  } finally {
    guardando.value = false;
  }
};

const cerrar = () => {
  pasoActual.value = 1;
  range.value = { start: null, end: null };
  reservasOcupadas.value = [];
  cotizacion.value = null;
  Object.assign(formularioAdmin, {
    full_name: "",
    email: "",
    phone: "",
    document_type: "",
    document_number: "",
    precio_negociado: "",
    notes: "",
  });
  emit("close");
};
</script>

<template>
  <div
    v-if="show"
    class="modal-overlay d-flex justify-content-center align-items-center"
    @click.self="cerrar"
  >
    <div
      class="modal-box bg-white rounded-4 shadow-lg overflow-hidden"
      style="max-width: 750px; width: 95%; max-height: 92vh; overflow-y: auto"
    >
      <div
        class="bg-dark text-white p-3 d-flex justify-content-between align-items-center border-bottom border-success border-3"
      >
        <h5 class="mb-0 fw-bold d-flex align-items-center">
          <font-awesome-icon icon="fa-solid fa-bed" class="text-success me-3 fs-4" />
          Reservar: Hab. {{ habitacion?.number }} · {{ habitacion?.name }}
        </h5>
        <button class="btn btn-sm text-white fs-5 border-0 hover-danger" @click="cerrar">
          <font-awesome-icon icon="fa-solid fa-xmark" />
        </button>
      </div>

      <div class="p-0">
        <div v-if="pasoActual === 1">
          <div class="p-4 text-center bg-light border-bottom">
            <h5 class="text-success fw-bold mb-1">Paso 1: Seleccione fechas</h5>
            <p class="text-muted small mb-0">
              Haga clic en el día de entrada y luego en el de salida. Los días en rojo no están disponibles
              (el día de salida de otra reserva queda libre).
            </p>
            <p v-if="errorFechas" class="text-danger small mb-0 mt-2">{{ errorFechas }}</p>
          </div>

          <div class="p-3 d-flex justify-content-center calendar-container">
            <VDatePicker
              v-model.range="range"
              is-range
              :min-date="minDate"
              :disabled-dates="reservasOcupadas"
              :attributes="attributes"
              color="green"
              title-position="left"
              :columns="columnasCalendario"
              :trim-weeks="true"
            />
          </div>

          <div class="p-3 bg-light border-top d-flex justify-content-between align-items-center gap-3">
            <div class="text-start">
              <span v-if="rangeComplete">
                <strong class="text-success">{{ fechaEntradaCorta }}</strong> al
                <strong class="text-success">{{ fechaSalidaCorta }}</strong>
                <span class="badge bg-success rounded-pill ms-2">{{ noches }} noches</span>
                <span v-if="cotizacion" class="ms-2 fw-bold">{{ money(cotizacion.total_amount) }}</span>
              </span>
              <span v-else class="text-muted small">Esperando selección de fechas...</span>
            </div>
            <button
              class="btn btn-success px-5 rounded-pill shadow-sm fw-bold"
              :disabled="!rangeComplete"
              @click="avanzarPaso"
            >
              Continuar <font-awesome-icon icon="fa-solid fa-arrow-right" class="ms-2" />
            </button>
          </div>
        </div>

        <div v-if="pasoActual === 2" class="p-4">
          <button
            class="btn btn-link text-decoration-none text-secondary p-0 mb-4 hover-dark"
            @click="pasoActual = 1"
          >
            <font-awesome-icon icon="fa-solid fa-arrow-left" class="me-2" /> Volver a selección de fechas
          </button>

          <div
            class="bg-success-light p-3 rounded-3 border border-success border-opacity-25 mb-4 text-center"
          >
            <h6 class="text-success fw-bold mb-3">Resumen de Estadía</h6>
            <div class="row small fw-bold text-dark">
              <div class="col-6 border-end border-success border-opacity-25">
                <font-awesome-icon icon="fa-solid fa-calendar-check" class="me-2 text-success" /> Entra:
                {{ fechaEntradaFormateada }}
              </div>
              <div class="col-6">
                <font-awesome-icon icon="fa-solid fa-calendar-minus" class="me-2 text-success" /> Sale:
                {{ fechaSalidaFormateada }}
              </div>
            </div>
            <div class="mt-3 small">
              <template v-if="cotizacion">
                {{ cotizacion.nights }} noche(s) × {{ money(cotizacion.price_per_night) }} =
                <strong class="fs-6">{{ money(cotizacion.total_amount) }}</strong>
                <span class="text-muted d-block"
                  >Anticipo de referencia ({{ cotizacion.deposit_percent }} %):
                  {{ money(cotizacion.deposit_amount) }}</span
                >
              </template>
              <span v-else-if="errorCotizacion" class="text-danger">{{ errorCotizacion }}</span>
            </div>
          </div>

          <form @submit.prevent="crearReservaAdmin">
            <div class="row g-3">
              <div class="col-md-7">
                <label class="form-label small fw-bold text-success">Nombre del Huésped</label>
                <input
                  v-model="formularioAdmin.full_name"
                  type="text"
                  class="form-control"
                  required
                  minlength="2"
                  placeholder="Ej. Juan Invitado"
                />
              </div>
              <div class="col-md-5">
                <label class="form-label small fw-bold text-success">Celular</label>
                <input
                  v-model="formularioAdmin.phone"
                  type="tel"
                  class="form-control"
                  placeholder="310 123 4567"
                />
              </div>
              <div class="col-md-12">
                <label class="form-label small fw-bold text-success">Correo Electrónico</label>
                <input
                  v-model="formularioAdmin.email"
                  type="email"
                  class="form-control"
                  required
                  placeholder="juan@email.com"
                />
              </div>
              <div class="col-md-5">
                <label class="form-label small fw-bold text-success">Tipo de documento (opcional)</label>
                <select v-model="formularioAdmin.document_type" class="form-select">
                  <option value="">Seleccione...</option>
                  <option v-for="doc in DOCUMENT_TYPES" :key="doc.value" :value="doc.value">
                    {{ doc.label }}
                  </option>
                </select>
              </div>
              <div class="col-md-7">
                <label class="form-label small fw-bold text-success">Número de documento (opcional)</label>
                <input v-model="formularioAdmin.document_number" type="text" class="form-control" />
              </div>
              <div v-if="puedeAjustarPrecio" class="col-md-6">
                <label class="form-label small fw-bold text-success">Precio negociado (opcional)</label>
                <input
                  v-model="formularioAdmin.precio_negociado"
                  type="number"
                  class="form-control"
                  min="1"
                  step="any"
                  placeholder="Vacío = tarifa del sistema"
                />
              </div>
              <div class="col-md-12">
                <label class="form-label small fw-bold text-success">Observaciones (Opcional)</label>
                <textarea
                  v-model="formularioAdmin.notes"
                  class="form-control"
                  rows="2"
                  maxlength="1000"
                  placeholder="Ej. Llegará tarde, requiere cama extra..."
                ></textarea>
              </div>
            </div>

            <div class="text-end mt-4 pt-3 border-top">
              <button type="submit" class="btn btn-dark px-4 rounded-pill shadow-sm" :disabled="guardando">
                <span v-if="guardando" class="spinner-border spinner-border-sm me-2"></span>
                <font-awesome-icon v-else icon="fa-solid fa-save" class="me-2" /> Confirmar Reserva
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Estilos del Modal Overlay con Blur moderno */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(15, 59, 42, 0.5);
  z-index: 1060;
  backdrop-filter: blur(6px);
  transition: all 0.3s ease;
}

/* Animación de entrada de la tarjeta */
.modal-box {
  animation: scaleIn 0.3s ease-out forwards;
  border: 1px solid rgba(15, 59, 42, 0.1);
}

@keyframes scaleIn {
  from {
    transform: scale(0.9) translateY(20px);
    opacity: 0;
  }
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

/* Clases de utilidad personalizadas */
.bg-success-light {
  background-color: rgba(139, 207, 91, 0.12);
}

.hover-danger:hover {
  background-color: var(--k-danger) !important;
  color: var(--k-offwhite) !important;
}

.hover-dark:hover {
  color: var(--k-forest) !important;
}

/* Ajustes para el contenedor del calendario */
.calendar-container :deep(.vc-container) {
  width: 100%;
  --vc-accent-green: var(--k-forest); /* Color de marca */
}

.calendar-container :deep(.vc-pane-container) {
  background-color: white;
}
:deep(.vc-day.is-not-in-month) {
  visibility: hidden !important;
  pointer-events: none !important;
}

/* Opcional: Asegura que el contenedor no genere barras de scroll raras */
:deep(.vc-pane-container) {
  overflow: hidden;
}
</style>
