<script setup>
import { ref, computed, onMounted } from "vue";
import Swal from "sweetalert2";
import { useAuthStore } from "@/stores/auth";
import { myBookings, uploadReceipt, openReceipt } from "@/api/bookings";
import { errorMessage } from "@/api/apiClient";
import { BOOKING_STATUS, BOOKING_STATUS_META } from "@/constants/booking";
import { formatDate, formatDateTime, formatMoney } from "@/utils/format";

const auth = useAuthStore();

const RECEIPT_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
const RECEIPT_MAX_MB = 5;

// --- 1. ESTADO ---
const checkInDate = ref("");
const checkOutDate = ref("");
const rango = ref(null); // { desde, hasta } aplicado con el botón de búsqueda
const filtroEstado = ref("todas");
const isLoading = ref(true);
const reservas = ref([]);
const expandidas = ref(new Set());

const receiptInput = ref(null);
const reservaParaComprobante = ref(null);
const subiendoId = ref(null);

const tabs = [
  { id: "todas", label: "Todas", estados: null },
  { id: "pendientes", label: "Pendientes", estados: [BOOKING_STATUS.PENDING_PAYMENT, BOOKING_STATUS.PENDING_VERIFICATION] },
  { id: "confirmadas", label: "Confirmadas", estados: [BOOKING_STATUS.CONFIRMED] },
  { id: "en-curso", label: "En Curso", estados: [BOOKING_STATUS.CHECKED_IN] },
];

// --- 2. COMPUTADAS ---
const reservasEnRango = computed(() => {
  if (!rango.value) return reservas.value;
  const { desde, hasta } = rango.value;
  return reservas.value.filter((r) => r.check_in >= desde && r.check_in <= hasta);
});

const listaVisual = computed(() => {
  const tab = tabs.find((t) => t.id === filtroEstado.value);
  if (!tab?.estados) return reservasEnRango.value;
  return reservasEnRango.value.filter((r) => tab.estados.includes(r.status));
});

const statusMeta = (status) =>
  BOOKING_STATUS_META[status] || { label: status, badge: "bg-light text-dark", icon: "fa-solid fa-circle-info" };

// --- 3. API ---
const cargarMisReservas = async () => {
  isLoading.value = true;
  try {
    reservas.value = await myBookings();
    // Las reservas que requieren acción del cliente se muestran abiertas.
    expandidas.value = new Set(
      reservas.value.filter((r) => r.status === BOOKING_STATUS.PENDING_PAYMENT).map((r) => r.id),
    );
  } catch (error) {
    Swal.fire({
      toast: true,
      position: "top-end",
      showConfirmButton: false,
      timer: 3000,
      icon: "error",
      title: errorMessage(error, "No se pudieron cargar tus reservas"),
    });
  } finally {
    isLoading.value = false;
  }
};

onMounted(cargarMisReservas);

// --- 4. FILTROS ---
const filtrarLista = () => {
  if (!checkInDate.value || !checkOutDate.value) {
    Swal.fire({
      icon: "warning",
      title: "Fechas incompletas",
      text: "Selecciona un rango de inicio y fin.",
      confirmButtonColor: "#212529",
    });
    return;
  }
  rango.value = { desde: checkInDate.value, hasta: checkOutDate.value };
};

const limpiarFiltros = () => {
  if (!checkInDate.value && !checkOutDate.value && !rango.value && filtroEstado.value === "todas") return;
  checkInDate.value = "";
  checkOutDate.value = "";
  rango.value = null;
  filtroEstado.value = "todas";
  Swal.mixin({
    toast: true,
    position: "top-end",
    showConfirmButton: false,
    timer: 2000,
  }).fire({ icon: "success", title: "Filtros eliminados" });
};

// --- 5. DETALLE ---
const toggleDetalle = (id) => {
  const set = new Set(expandidas.value);
  if (set.has(id)) set.delete(id);
  else set.add(id);
  expandidas.value = set;
};

// --- 6. COMPROBANTES ---
/** Se llama directamente desde el clic para que el navegador no bloquee la pestaña nueva. */
const verComprobante = async (reserva) => {
  try {
    await openReceipt(reserva.receipt_url);
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo abrir el comprobante."), "error");
  }
};

const elegirComprobante = (reserva) => {
  reservaParaComprobante.value = reserva;
  receiptInput.value?.click();
};

const subirComprobante = async (event) => {
  const file = event.target.files?.[0];
  const reserva = reservaParaComprobante.value;
  event.target.value = "";
  if (!file || !reserva) return;

  if (!RECEIPT_TYPES.includes(file.type)) {
    Swal.fire("Archivo no válido", "El comprobante debe ser una imagen JPEG, PNG o WebP, o un PDF.", "warning");
    return;
  }
  if (file.size > RECEIPT_MAX_MB * 1024 * 1024) {
    Swal.fire("Archivo muy pesado", `El comprobante no puede superar ${RECEIPT_MAX_MB} MB.`, "warning");
    return;
  }

  subiendoId.value = reserva.id;
  try {
    await uploadReceipt(reserva.id, file);
    await Swal.fire({
      icon: "success",
      title: "Comprobante enviado",
      text: "Verificaremos tu pago y te avisaremos cuando la reserva quede confirmada.",
      confirmButtonColor: "#212529",
    });
    await cargarMisReservas();
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo subir el comprobante."), "error");
  } finally {
    subiendoId.value = null;
    reservaParaComprobante.value = null;
  }
};
</script>

<template>
  <div class="container-fluid py-2">
    <div class="d-flex flex-wrap gap-3 justify-content-between align-items-center mb-4">
      <div>
        <h4 class="fw-bold text-dark mb-1">Mis Reservas</h4>
        <p class="text-muted mb-0 small">
          Titular:
          <span class="fw-bold text-dark">{{ auth.user?.full_name || "Huésped" }}</span>
        </p>
      </div>
      <router-link
        :to="{ name: 'hospedaje-home' }"
        class="btn btn-explorar rounded-pill px-4 shadow-sm fw-medium text-decoration-none"
      >
        <font-awesome-icon icon="fa-solid fa-house-chimney" class="me-2" />
        Explorar Habitaciones
      </router-link>
    </div>

    <div class="card border-0 shadow-sm rounded-4 p-3 mb-4 bg-white d-inline-block w-100">
      <div class="d-flex flex-wrap gap-3 align-items-end">
        <div>
          <label class="form-label small fw-bold text-secondary mb-1">Llegada desde</label>
          <input
            type="date"
            v-model="checkInDate"
            class="form-control rounded-3 shadow-none border-light-subtle bg-light"
            style="min-width: 160px"
          />
        </div>

        <div>
          <label class="form-label small fw-bold text-secondary mb-1">Hasta</label>
          <input
            type="date"
            v-model="checkOutDate"
            class="form-control rounded-3 shadow-none border-light-subtle bg-light"
            style="min-width: 160px"
          />
        </div>

        <div class="d-flex gap-2 ms-auto ms-md-0">
          <button
            @click="filtrarLista"
            class="btn bg-transparent border-0 text-dark rounded-circle d-inline-flex align-items-center justify-content-center transition-all"
            style="width: 42px; height: 42px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.03)"
            title="Buscar reservas"
          >
            <font-awesome-icon icon="fa-solid fa-magnifying-glass" class="fs-5 fw-bold" />
          </button>

          <button
            v-if="checkInDate || checkOutDate || rango"
            @click="limpiarFiltros"
            class="btn btn-light border text-danger rounded-circle shadow-sm d-inline-flex align-items-center justify-content-center transition-all"
            style="width: 42px; height: 42px"
            title="Limpiar fechas"
          >
            <font-awesome-icon icon="fa-solid fa-xmark" />
          </button>
        </div>
      </div>
    </div>

    <div class="bg-light p-1 rounded-pill d-flex border shadow-sm mb-4 overflow-auto">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="btn rounded-pill px-4 fw-bold border-0 flex-grow-1 transition-all text-nowrap"
        :class="filtroEstado === tab.id ? 'btn-dark text-white shadow' : 'text-muted'"
        @click="filtroEstado = tab.id"
      >
        {{ tab.label }}
        <span v-if="tab.id === 'todas'" class="ms-1">({{ reservasEnRango.length }})</span>
      </button>
    </div>

    <input
      ref="receiptInput"
      type="file"
      class="d-none"
      accept="image/jpeg,image/png,image/webp,application/pdf"
      @change="subirComprobante"
    />

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
      <div class="table-responsive">
        <table class="table align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th class="py-3 px-4 text-muted small fw-bold">DETALLE DEL HOSPEDAJE</th>
              <th class="py-3 text-muted small fw-bold text-center">REGISTRO</th>
              <th class="py-3 text-center text-muted small fw-bold">ESTANCIA (IN - OUT)</th>
              <th class="py-3 text-end text-muted small fw-bold">TOTAL</th>
              <th class="py-3 text-center text-muted small fw-bold">ESTADO</th>
              <th class="py-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="6" class="text-center py-5">
                <span class="spinner-border text-success" role="status"></span>
              </td>
            </tr>

            <template v-else>
            <template v-for="reserva in listaVisual" :key="reserva.id">
              <tr class="cursor-pointer" @click="toggleDetalle(reserva.id)">
                <td class="px-4 py-3">
                  <div class="d-flex align-items-center">
                    <div
                      class="bg-success bg-opacity-10 text-success rounded-circle d-flex align-items-center justify-content-center me-3 flex-shrink-0"
                      style="width: 40px; height: 40px"
                    >
                      <font-awesome-icon icon="fa-solid fa-house-chimney" class="fs-5" />
                    </div>
                    <div>
                      <div class="fw-bold text-dark">
                        {{ reserva.room?.name || "Habitación" }}
                        <span v-if="reserva.room?.number" class="text-muted fw-normal small">· N.º {{ reserva.room.number }}</span>
                      </div>
                      <small class="text-muted">
                        <font-awesome-icon icon="fa-solid fa-tag" class="me-1" /> {{ reserva.code }}
                      </small>
                    </div>
                  </div>
                </td>
                <td class="text-muted small text-center">{{ formatDateTime(reserva.created_at) }}</td>
                <td class="text-center">
                  <div class="small text-muted mb-1">
                    <font-awesome-icon icon="fa-solid fa-right-to-bracket" class="text-success me-1" />
                    In: {{ formatDate(reserva.check_in) }}
                  </div>
                  <div class="small text-muted">
                    <font-awesome-icon icon="fa-solid fa-right-from-bracket" class="text-danger me-1" />
                    Out: {{ formatDate(reserva.check_out) }}
                  </div>
                  <div class="small text-muted">
                    <font-awesome-icon icon="fa-solid fa-moon" class="me-1" />
                    {{ reserva.nights }} {{ reserva.nights === 1 ? "noche" : "noches" }}
                  </div>
                </td>
                <td class="text-end small">
                  <div class="fw-bold text-dark">{{ formatMoney(reserva.total_amount) }}</div>
                  <div class="text-muted">Anticipo: {{ formatMoney(reserva.deposit_amount) }}</div>
                </td>
                <td class="text-center">
                  <span
                    class="badge rounded-pill px-3 py-2 d-inline-flex align-items-center fw-normal"
                    :class="statusMeta(reserva.status).badge"
                  >
                    <font-awesome-icon :icon="statusMeta(reserva.status).icon" class="me-2" />
                    {{ statusMeta(reserva.status).label }}
                  </span>
                </td>
                <td class="text-end pe-4">
                  <font-awesome-icon
                    icon="fa-solid fa-chevron-right"
                    class="text-muted chevron"
                    :class="{ 'chevron-open': expandidas.has(reserva.id) }"
                    :title="expandidas.has(reserva.id) ? 'Ocultar detalle' : 'Ver detalle'"
                  />
                </td>
              </tr>

              <tr v-if="expandidas.has(reserva.id)" class="detalle-row">
                <td colspan="6" class="px-4 py-3">
                  <div
                    v-if="reserva.status === BOOKING_STATUS.PENDING_PAYMENT"
                    class="alert alert-warning rounded-4 small mb-3"
                  >
                    <div class="fw-bold mb-1">
                      <font-awesome-icon icon="fa-solid fa-receipt" class="me-2" />
                      Necesitamos un nuevo comprobante de pago
                    </div>
                    <div v-if="reserva.status_reason">Motivo: {{ reserva.status_reason }}</div>
                    <div v-if="reserva.payment_due_at">
                      <font-awesome-icon icon="fa-solid fa-clock" class="me-1" />
                      Tienes plazo hasta el <strong>{{ formatDateTime(reserva.payment_due_at) }}</strong>; después la
                      reserva se cancelará automáticamente.
                    </div>
                  </div>

                  <div
                    v-else-if="reserva.status === BOOKING_STATUS.PENDING_VERIFICATION"
                    class="alert alert-info rounded-4 small mb-3"
                  >
                    <font-awesome-icon icon="fa-solid fa-circle-info" class="me-2" />
                    Estamos verificando tu comprobante de pago. Te avisaremos cuando la reserva quede confirmada.
                  </div>

                  <div
                    v-else-if="reserva.status === BOOKING_STATUS.CANCELLED && reserva.status_reason"
                    class="alert alert-danger rounded-4 small mb-3"
                  >
                    <font-awesome-icon icon="fa-solid fa-ban" class="me-2" />
                    Motivo de la cancelación: {{ reserva.status_reason }}
                  </div>

                  <div class="row g-3 small">
                    <div class="col-sm-6 col-lg-3">
                      <div class="text-muted">Tarifa</div>
                      <div class="fw-semibold">
                        {{ formatMoney(reserva.price_per_night) }} × {{ reserva.nights }}
                        {{ reserva.nights === 1 ? "noche" : "noches" }}
                      </div>
                    </div>
                    <div class="col-sm-6 col-lg-3">
                      <div class="text-muted">Total</div>
                      <div class="fw-semibold">{{ formatMoney(reserva.total_amount) }}</div>
                    </div>
                    <div class="col-sm-6 col-lg-3">
                      <div class="text-muted">Anticipo ({{ reserva.deposit_percent }} %)</div>
                      <div class="fw-semibold">{{ formatMoney(reserva.deposit_amount) }}</div>
                    </div>
                    <div class="col-sm-6 col-lg-3">
                      <div class="text-muted">Huéspedes</div>
                      <div class="fw-semibold">{{ 1 + (reserva.companions?.length || 0) }}</div>
                    </div>
                    <div v-if="reserva.notes" class="col-12">
                      <div class="text-muted">Notas</div>
                      <div>{{ reserva.notes }}</div>
                    </div>
                  </div>

                  <div class="d-flex flex-wrap gap-2 mt-3">
                    <button
                      v-if="reserva.has_receipt && reserva.receipt_url"
                      type="button"
                      class="btn btn-sm btn-outline-dark rounded-pill px-3"
                      @click.stop="verComprobante(reserva)"
                    >
                      <font-awesome-icon icon="fa-solid fa-eye" class="me-1" /> Ver comprobante
                    </button>
                    <button
                      v-if="reserva.status === BOOKING_STATUS.PENDING_PAYMENT"
                      type="button"
                      class="btn btn-sm btn-explorar rounded-pill px-3"
                      :disabled="subiendoId === reserva.id"
                      @click.stop="elegirComprobante(reserva)"
                    >
                      <span v-if="subiendoId === reserva.id" class="spinner-border spinner-border-sm me-1"></span>
                      <font-awesome-icon v-else icon="fa-solid fa-cloud-arrow-up" class="me-1" />
                      Subir nuevo comprobante
                    </button>
                    <span v-if="reserva.status === BOOKING_STATUS.PENDING_PAYMENT" class="small text-muted align-self-center">
                      JPEG, PNG, WebP o PDF · máx. {{ RECEIPT_MAX_MB }} MB
                    </span>
                  </div>
                </td>
              </tr>
            </template>
            </template>

            <tr v-if="!isLoading && listaVisual.length === 0">
              <td colspan="6" class="text-center py-5 text-muted">
                <font-awesome-icon icon="fa-solid fa-magnifying-glass" class="display-4 mb-3 d-block mx-auto text-light" />
                <p>No se encontraron resultados en esta categoría o con los filtros aplicados.</p>
                <button
                  v-if="reservas.length"
                  @click="limpiarFiltros"
                  class="btn btn-sm btn-link text-success text-decoration-none fw-bold"
                >
                  Ver todas las reservas
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.btn-explorar {
  background-color: var(--k-forest);
  color: var(--k-offwhite);
  border: none;
  transition: background-color 0.3s ease;
}

.btn-explorar:hover {
  background-color: var(--k-apple);
  color: var(--k-offwhite);
}

.transition-all {
  transition: all 0.3s ease;
}
.cursor-pointer {
  cursor: pointer;
}
.cursor-pointer:hover {
  background-color: #f8f9fa !important;
}
.chevron {
  transition: transform 0.2s ease;
}
.chevron-open {
  transform: rotate(90deg);
}
.detalle-row > td {
  background-color: #fbfcfb;
}
</style>
