<script setup>
import { ref, reactive, watch, computed } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { updateBooking, changeBookingStatus } from "@/api/bookings";
import { getQuote } from "@/api/rooms";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { DOCUMENT_TYPES, PERMISSIONS } from "@/constants/booking";
import { formatMoney, nightsBetween } from "@/utils/format";

const props = defineProps({
  show: Boolean,
  reserva: { type: Object, default: null },
  modoCheckIn: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "actualizado"]);

const auth = useAuthStore();
const configStore = useConfigStore();
const puedeAjustarPrecio = computed(() => auth.can(PERMISSIONS.BOOKINGS_OVERRIDE_PRICE));

const guardando = ref(false);
const cotizacion = ref(null);
const errorCotizacion = ref("");

const form = reactive({
  full_name: "",
  email: "",
  phone: "",
  document_type: "",
  document_number: "",
  check_in: "",
  check_out: "",
  notes: "",
  precio_negociado: "",
  companions: [],
});

// Copia de los valores originales para enviar solo lo que cambió.
let original = null;

const money = (value) => formatMoney(value, configStore.data.currency);
const vacioANulo = (value) => {
  const limpio = typeof value === "string" ? value.trim() : value;
  return limpio === "" || limpio === undefined ? null : limpio;
};

const guestPayload = () => ({
  full_name: form.full_name.trim(),
  email: form.email.trim(),
  phone: vacioANulo(form.phone),
  document_type: vacioANulo(form.document_type),
  document_number: vacioANulo(form.document_number),
});

const companionsPayload = () =>
  form.companions.map((c) => ({
    full_name: c.full_name.trim(),
    document_type: vacioANulo(c.document_type),
    document_number: vacioANulo(c.document_number),
    relationship: (c.relationship || "").trim(),
  }));

const yaIngreso = computed(() => props.reserva?.status === "checked_in");
const nochesNuevas = computed(() => nightsBetween(form.check_in, form.check_out));
const fechasCambiaron = computed(
  () => !!original && (form.check_in !== original.check_in || form.check_out !== original.check_out),
);

// Precio que calcula el servidor para las nuevas fechas (solo informativo).
const actualizarCotizacion = async () => {
  cotizacion.value = null;
  errorCotizacion.value = "";
  if (!props.reserva || !fechasCambiaron.value || nochesNuevas.value < 1) return;
  try {
    cotizacion.value = await getQuote(props.reserva.room.id, form.check_in, form.check_out);
  } catch (error) {
    errorCotizacion.value = errorMessage(error, "No se pudo calcular el nuevo precio.");
  }
};

watch(() => [form.check_in, form.check_out], actualizarCotizacion);

watch(
  () => props.show,
  (visible) => {
    if (!visible || !props.reserva) return;
    const r = props.reserva;
    form.full_name = r.guest?.full_name || "";
    form.email = r.guest?.email || "";
    form.phone = r.guest?.phone || "";
    form.document_type = r.guest?.document_type || "";
    form.document_number = r.guest?.document_number || "";
    form.check_in = r.check_in || "";
    form.check_out = r.check_out || "";
    form.notes = r.notes || "";
    form.precio_negociado = "";
    form.companions = (r.companions || []).map((c) => ({
      full_name: c.full_name || "",
      document_type: c.document_type || "",
      document_number: c.document_number || "",
      relationship: c.relationship || "",
    }));
    cotizacion.value = null;
    errorCotizacion.value = "";
    original = {
      check_in: form.check_in,
      check_out: form.check_out,
      notes: form.notes,
      guest: JSON.stringify(guestPayload()),
      companions: JSON.stringify(companionsPayload()),
    };
  },
);

const agregarAcompanante = () => {
  form.companions.push({ full_name: "", document_type: "", document_number: "", relationship: "" });
};

const quitarAcompanante = (index) => {
  form.companions.splice(index, 1);
};

/** Construye el PATCH solo con los campos modificados. El precio lo recalcula el servidor. */
const construirCambios = () => {
  const cambios = {};
  if (form.check_in !== original.check_in) cambios.check_in = form.check_in;
  if (form.check_out !== original.check_out) cambios.check_out = form.check_out;
  const guest = guestPayload();
  if (JSON.stringify(guest) !== original.guest) cambios.guest = guest;
  const companions = companionsPayload();
  if (JSON.stringify(companions) !== original.companions) cambios.companions = companions;
  if (form.notes !== original.notes) cambios.notes = vacioANulo(form.notes);
  if (puedeAjustarPrecio.value && form.precio_negociado !== "" && form.precio_negociado !== null) {
    cambios.total_amount = Number(form.precio_negociado);
  }
  return cambios;
};

const guardarDetalles = async () => {
  if (nochesNuevas.value < 1) {
    Swal.fire("Fechas inválidas", "La salida debe ser posterior a la entrada.", "warning");
    return;
  }
  guardando.value = true;
  const id = props.reserva.id;
  try {
    const cambios = construirCambios();
    if (Object.keys(cambios).length) {
      await updateBooking(id, cambios);
    }

    if (props.modoCheckIn) {
      await changeBookingStatus(id, "checked_in");
      Swal.fire({
        icon: "success",
        title: "¡Check-in exitoso!",
        text: "El huésped ya está registrado y su folio está abierto.",
        timer: 2000,
        showConfirmButton: false,
      });
    } else if (Object.keys(cambios).length) {
      Swal.fire({
        icon: "success",
        title: "¡Guardado!",
        text: "Los detalles se actualizaron correctamente.",
        timer: 1500,
        showConfirmButton: false,
      });
    }

    emit("actualizado");
    cerrar();
  } catch (error) {
    // 409: fechas no disponibles, check-in antes de la fecha, reserva modificada por otra persona...
    Swal.fire(
      "No se pudo guardar",
      errorMessage(error, "Hubo un problema al procesar la solicitud."),
      "error",
    );
    emit("actualizado");
  } finally {
    guardando.value = false;
  }
};

const cerrar = () => {
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
      style="max-width: 800px; width: 95%; max-height: 90vh; display: flex; flex-direction: column"
    >
      <div
        class="bg-dark text-white p-3 d-flex justify-content-between align-items-center border-bottom border-success border-3"
      >
        <h5 class="mb-0 fw-bold d-flex align-items-center">
          <font-awesome-icon
            :icon="modoCheckIn ? 'fa-solid fa-door-open' : 'fa-solid fa-user-pen'"
            class="text-success me-3 fs-4"
          />
          {{ modoCheckIn ? "Realizar Check-in:" : "Editar reserva:" }} {{ reserva?.code }}
        </h5>
        <button class="btn btn-sm text-white fs-5 border-0 hover-danger" @click="cerrar">
          <font-awesome-icon icon="fa-solid fa-xmark" />
        </button>
      </div>

      <div class="p-4 overflow-auto" style="flex: 1">
        <form id="formEdicionReserva" @submit.prevent="guardarDetalles">
          <h6 class="fw-bold text-success mb-3 border-bottom pb-2">Estadía y Cobro</h6>
          <div class="row g-3 mb-4 bg-light p-3 rounded border">
            <div class="col-md-4">
              <label class="form-label small fw-bold text-muted">
                Ingreso <font-awesome-icon v-if="yaIngreso" icon="fa-solid fa-lock" class="text-warning" />
              </label>
              <input
                v-model="form.check_in"
                type="date"
                class="form-control"
                :disabled="yaIngreso"
                required
              />
            </div>
            <div class="col-md-4">
              <label class="form-label small fw-bold text-success">Salida</label>
              <input
                v-model="form.check_out"
                type="date"
                class="form-control border-success"
                :min="form.check_in"
                required
              />
            </div>
            <div class="col-md-4">
              <label class="form-label small fw-bold text-dark">Total actual</label>
              <div class="form-control fw-bold bg-white text-dark">{{ money(reserva?.total_amount) }}</div>
              <small class="text-muted"
                >{{ reserva?.nights }} noche(s) · anticipo {{ money(reserva?.deposit_amount) }}</small
              >
            </div>

            <div v-if="fechasCambiaron" class="col-12">
              <div v-if="cotizacion" class="alert alert-info small mb-0 py-2">
                Con las nuevas fechas ({{ cotizacion.nights }} noche(s)) la tarifa sería
                <strong>{{ money(cotizacion.total_amount) }}</strong
                >. El servidor recalcula el precio y valida la disponibilidad al guardar.
              </div>
              <div v-else-if="errorCotizacion" class="alert alert-warning small mb-0 py-2">
                {{ errorCotizacion }}
              </div>
            </div>

            <div v-if="puedeAjustarPrecio" class="col-md-6">
              <label class="form-label small fw-bold text-muted">Precio negociado (opcional)</label>
              <input
                v-model="form.precio_negociado"
                type="number"
                class="form-control"
                min="1"
                step="any"
                placeholder="Dejar vacío para usar la tarifa"
              />
              <small class="text-muted">Solo si se acordó un valor distinto a la tarifa.</small>
            </div>
          </div>

          <h6 class="fw-bold text-success mb-3 border-bottom pb-2 mt-4">Datos del Titular</h6>
          <div class="row g-3 mb-4">
            <div class="col-md-12">
              <label class="form-label small fw-bold text-muted">Nombre Completo / Razón Social</label>
              <input v-model="form.full_name" type="text" class="form-control" required minlength="2" />
            </div>
            <div class="col-md-6">
              <label class="form-label small fw-bold text-muted">Tipo Documento</label>
              <select v-model="form.document_type" class="form-select" :required="modoCheckIn">
                <option value="">Seleccione...</option>
                <option v-for="doc in DOCUMENT_TYPES" :key="doc.value" :value="doc.value">
                  {{ doc.label }}
                </option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label small fw-bold text-muted">Número de Documento</label>
              <input
                v-model="form.document_number"
                type="text"
                class="form-control"
                :required="modoCheckIn"
              />
            </div>
            <div class="col-md-6">
              <label class="form-label small fw-bold text-muted">Celular</label>
              <input v-model="form.phone" type="tel" class="form-control" />
            </div>
            <div class="col-md-6">
              <label class="form-label small fw-bold text-muted">Correo Electrónico</label>
              <input v-model="form.email" type="email" class="form-control" required />
            </div>
          </div>

          <div class="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2 mt-4">
            <h6 class="fw-bold text-success mb-0">Registro de Acompañantes</h6>
            <button type="button" class="btn btn-sm btn-outline-success" @click="agregarAcompanante">
              <font-awesome-icon icon="fa-solid fa-plus" /> Agregar
            </button>
          </div>

          <div
            v-if="form.companions.length === 0"
            class="text-center p-3 bg-light rounded text-muted small mb-4"
          >
            No hay acompañantes registrados. Presiona "Agregar" si vienen más personas.
          </div>

          <div
            v-for="(acomp, index) in form.companions"
            :key="'acomp-' + index"
            class="row g-2 mb-3 p-3 border rounded position-relative bg-light"
          >
            <button
              type="button"
              class="btn btn-sm btn-danger position-absolute top-0 end-0 m-2"
              style="width: 30px; height: 30px; padding: 0"
              @click="quitarAcompanante(index)"
            >
              <font-awesome-icon icon="fa-solid fa-trash" />
            </button>
            <div class="col-12">
              <strong class="small text-dark">Acompañante {{ index + 1 }}</strong>
            </div>
            <div class="col-md-6">
              <input
                v-model="acomp.full_name"
                type="text"
                class="form-control form-control-sm"
                placeholder="Nombre completo"
                required
                minlength="2"
              />
            </div>
            <div class="col-md-3">
              <select v-model="acomp.document_type" class="form-select form-select-sm">
                <option value="">Tipo ID...</option>
                <option v-for="doc in DOCUMENT_TYPES" :key="doc.value" :value="doc.value">
                  {{ doc.label }}
                </option>
              </select>
            </div>
            <div class="col-md-3">
              <input
                v-model="acomp.document_number"
                type="text"
                class="form-control form-control-sm"
                placeholder="N° Documento"
              />
            </div>
            <div class="col-md-12">
              <input
                v-model="acomp.relationship"
                type="text"
                class="form-control form-control-sm"
                placeholder="Parentesco (Ej: Hijo, Esposa)"
                maxlength="40"
              />
            </div>
          </div>

          <h6 class="fw-bold text-success mb-3 border-bottom pb-2 mt-4">Notas</h6>
          <textarea
            v-model="form.notes"
            class="form-control mb-3"
            rows="2"
            maxlength="1000"
            placeholder="Observaciones internas de la reserva"
          ></textarea>

          <div class="alert alert-light border small mb-0">
            <font-awesome-icon icon="fa-solid fa-circle-info" class="me-1" />
            Los consumos extra (minibar, restaurante, etc.) se registran en el folio del huésped, disponible
            desde el check-in.
          </div>
        </form>
      </div>

      <div class="p-3 bg-light border-top text-end">
        <button type="button" class="btn btn-secondary me-2" @click="cerrar">Cancelar</button>
        <button type="submit" form="formEdicionReserva" class="btn btn-dark px-4" :disabled="guardando">
          <span v-if="guardando" class="spinner-border spinner-border-sm me-2"></span>
          <font-awesome-icon
            v-else
            :icon="modoCheckIn ? 'fa-solid fa-circle-check' : 'fa-solid fa-save'"
            class="me-2"
          />
          {{ modoCheckIn ? "Confirmar Check-in" : "Guardar cambios" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(15, 59, 42, 0.5);
  z-index: 1060;
  backdrop-filter: blur(4px);
}
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
.hover-danger:hover {
  color: #dc3545 !important;
}
</style>
