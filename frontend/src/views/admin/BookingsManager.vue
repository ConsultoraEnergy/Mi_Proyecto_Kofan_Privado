<script setup>
import { ref, computed, onMounted, watch, defineAsyncComponent } from "vue";
import { useRoute } from "vue-router";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { listBookings, changeBookingStatus, openReceipt } from "@/api/bookings";
import { getDashboard } from "@/api/operations";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import {
  BOOKING_STATUS as S,
  BOOKING_STATUS_META,
  PERMISSIONS,
  canTransition,
  requiresReason,
} from "@/constants/booking";
import { formatDate, formatDateTime, formatMoney } from "@/utils/format";

const ModalEdicionReserva = defineAsyncComponent(() => import("@/components/ModalEdicionReserva.vue"));
const ModalFolio = defineAsyncComponent(() => import("@/components/ModalFolio.vue"));

const auth = useAuthStore();
const configStore = useConfigStore();
const route = useRoute();

const TABS = [
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
];

// Clases suaves del diseño para cada estado (la etiqueta y el ícono vienen de BOOKING_STATUS_META).
const SOFT_BADGES = {
  pending_verification: "badge-soft-sky",
  pending_payment: "badge-soft-sand",
  confirmed: "badge-soft-apple",
  checked_in: "badge-soft-sky",
  checked_out: "badge-soft-neutral",
  cancelled: "badge-soft-rose",
};

const limitePorPagina = 10;
const paginaActual = ref(1);
const totalRegistros = ref(0);
const totalPaginas = computed(() => Math.max(1, Math.ceil(totalRegistros.value / limitePorPagina)));

const reservas = ref([]);
const resumen = ref({ pending_verification: 0, pending_payment: 0 });
const cargandoReservas = ref(true);
const pestanaActiva = ref(TABS.some((t) => t.key === route.query.tab) ? route.query.tab : TABS[0].key);
const filtro = ref("");
const totalHuespedesEnCasa = ref(null);

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_APPLE = getBrandColor("--k-apple", "#8BCF5B");
const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");

const money = (value) => formatMoney(value, configStore.data.currency);
const statusMeta = (status) =>
  BOOKING_STATUS_META[status] || { label: status, icon: "fa-solid fa-circle-info" };

const puedeCambiarEstado = computed(() => auth.can(PERMISSIONS.BOOKINGS_CHANGE_STATUS));
const puedeEditar = computed(() => auth.can(PERMISSIONS.BOOKINGS_UPDATE));
const puedeVerComprobantes = computed(() => auth.can(PERMISSIONS.BOOKINGS_VIEW_RECEIPTS));
const puedeVerFolio = computed(() => auth.can(PERMISSIONS.FOLIOS_READ));

const cargarReservas = async () => {
  cargandoReservas.value = true;
  try {
    const tab = TABS.find((t) => t.key === pestanaActiva.value) || TABS[0];
    const params = { status: tab.statuses.join(","), page: paginaActual.value, limit: limitePorPagina };
    const termino = filtro.value.trim();
    if (termino) params.q = termino;

    const data = await listBookings(params);
    reservas.value = data.items || [];
    totalRegistros.value = data.total || 0;
    if (data.summary) resumen.value = data.summary;
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudieron cargar las reservas."), "error");
  } finally {
    cargandoReservas.value = false;
  }
};

let timeoutBuscador = null;
watch(filtro, () => {
  clearTimeout(timeoutBuscador);
  timeoutBuscador = setTimeout(() => {
    paginaActual.value = 1;
    cargarReservas();
  }, 350);
});

const cambiarPestana = (nuevaPestana) => {
  pestanaActiva.value = nuevaPestana;
  paginaActual.value = 1;
  cargarReservas();
};

const cambiarPagina = (nuevaPagina) => {
  if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas.value) {
    paginaActual.value = nuevaPagina;
    cargarReservas();
  }
};

const cargarHuespedesEnCasa = async () => {
  if (!auth.can(PERMISSIONS.DASHBOARD_READ)) return;
  try {
    const data = await getDashboard();
    totalHuespedesEnCasa.value = data?.stats?.in_house_guests ?? 0;
  } catch {
    totalHuespedesEnCasa.value = null;
  }
};

// El comprobante es privado: se descarga con el token y se abre en una pestaña nueva.
const verComprobante = (reserva) => {
  openReceipt(reserva.receipt_url).catch((error) => {
    Swal.fire("Error", errorMessage(error, "No se pudo cargar el comprobante de pago."), "error");
  });
};

const puede = (reserva, destino) => puedeCambiarEstado.value && canTransition(reserva.status, destino);

const TEXTOS_TRANSICION = {
  [S.CONFIRMED]: {
    titulo: "¿Aprobar el pago de esta reserva?",
    texto: "El anticipo quedará validado y la reserva pasará a confirmada.",
    boton: "Sí, aprobar pago",
    exito: "Pago aprobado. La reserva quedó confirmada.",
  },
  [S.PENDING_PAYMENT]: {
    titulo: "Rechazar comprobante",
    texto: "Indica al huésped por qué no se pudo validar el pago. Podrá subir un nuevo comprobante.",
    boton: "Rechazar comprobante",
    exito: "Comprobante rechazado. Se notificó al huésped.",
  },
  [S.CHECKED_IN]: {
    titulo: "¿Registrar la llegada?",
    texto: "Se abrirá la cuenta (folio) del huésped.",
    boton: "Sí, hacer check-in",
    exito: "Todo preparado para la llegada de este viajero.",
  },
  [S.CHECKED_OUT]: {
    titulo: "¿Cerrar la estancia?",
    texto: "La salida quedará registrada y el folio del huésped se cerrará.",
    boton: "Sí, hacer check-out",
    exito: "Check-out registrado. El folio quedó cerrado.",
  },
  [S.CANCELLED]: {
    titulo: "¿Deseas cancelar esta reserva?",
    texto: "Las fechas volverán a quedar disponibles. El motivo se mostrará al huésped.",
    boton: "Sí, cancelar",
    exito: "La reserva fue cancelada.",
  },
};

const actualizarEstado = async (reserva, destino) => {
  const textos = TEXTOS_TRANSICION[destino];
  const conMotivo = requiresReason(reserva.status, destino);

  const result = await Swal.fire({
    title: textos.titulo,
    text: `${reserva.code} · ${reserva.guest?.full_name || ""}. ${textos.texto}`,
    icon: conMotivo ? "warning" : "question",
    input: conMotivo ? "textarea" : undefined,
    inputLabel: conMotivo ? "Motivo (obligatorio)" : undefined,
    inputPlaceholder: conMotivo ? "Ej.: el valor transferido no coincide con el anticipo" : undefined,
    inputValidator: conMotivo
      ? (value) => (!value || !value.trim() ? "Debes escribir un motivo." : undefined)
      : undefined,
    showCancelButton: true,
    confirmButtonColor: COLOR_APPLE,
    cancelButtonColor: COLOR_FOREST,
    confirmButtonText: textos.boton,
    cancelButtonText: "Volver",
  });
  if (!result.isConfirmed) return;

  try {
    await changeBookingStatus(reserva.id, destino, conMotivo ? result.value.trim() : null);
    await Promise.all([cargarReservas(), cargarHuespedesEnCasa()]);
    Swal.fire({
      title: "Movimiento actualizado",
      text: textos.exito,
      icon: "success",
      timer: 1700,
      showConfirmButton: false,
    });
  } catch (error) {
    Swal.fire(
      "No fue posible actualizar esta reserva",
      errorMessage(error, "Inténtalo nuevamente en unos segundos."),
      "error",
    );
  }
};

const mostrarModalEdicion = ref(false);
const reservaAEditar = ref(null);
const esModoCheckIn = ref(false);

const abrirModalEdicion = (reserva, checkIn = false) => {
  reservaAEditar.value = reserva;
  esModoCheckIn.value = checkIn;
  mostrarModalEdicion.value = true;
};

const refrescarTabla = async () => {
  await Promise.all([cargarReservas(), cargarHuespedesEnCasa()]);
};

const mostrarModalFolio = ref(false);
const reservaParaFolio = ref(null);

const abrirModalFolio = (reserva) => {
  reservaParaFolio.value = reserva;
  mostrarModalFolio.value = true;
};

onMounted(() => {
  configStore.fetchSiteConfig();
  cargarReservas();
  cargarHuespedesEnCasa();
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

    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div
          class="eco-card border-0 shadow-sm p-3 rounded-4 stats-card h-100 clickable"
          @click="cambiarPestana('pending_verification')"
        >
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <h6 class="text-muted fw-bold mb-2 text-uppercase small-label">Pagos por verificar</h6>
              <h3 class="fw-bold mb-1 text-brand">
                {{ resumen.pending_verification }}
              </h3>
              <p class="text-muted small mb-0">Comprobantes por revisar</p>
            </div>
            <div class="icon-box tone-sky-box">
              <font-awesome-icon icon="fa-solid fa-receipt" />
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div
          class="eco-card border-0 shadow-sm p-3 rounded-4 stats-card h-100 clickable"
          @click="cambiarPestana('pending_payment')"
        >
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <h6 class="text-muted fw-bold mb-2 text-uppercase small-label">Pendientes de pago</h6>
              <h3 class="fw-bold mb-1 text-brand">
                {{ resumen.pending_payment }}
              </h3>
              <p class="text-muted small mb-0">Sin comprobante o rechazado</p>
            </div>
            <div class="icon-box tone-apple-box">
              <font-awesome-icon icon="fa-solid fa-clock" />
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="eco-card border-0 shadow-sm p-3 rounded-4 stats-card h-100">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <h6 class="text-muted fw-bold mb-2 text-uppercase small-label">Huéspedes Hoy</h6>
              <h3 class="fw-bold mb-1 text-brand">
                {{ totalHuespedesEnCasa ?? "—" }}
              </h3>
              <p class="text-muted small mb-0">En las instalaciones</p>
            </div>
            <div class="icon-box tone-bed-box">
              <font-awesome-icon icon="fa-solid fa-bed" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card eco-card border-0 shadow-sm rounded-4 overflow-hidden">
      <div
        class="card-header bg-transparent p-3 border-0 d-flex flex-column flex-xl-row justify-content-between align-items-center gap-3"
      >
        <div class="filter-chip-group">
          <button
            v-for="tab in TABS"
            :key="tab.key"
            class="filter-chip"
            :class="{ active: pestanaActiva === tab.key }"
            @click="cambiarPestana(tab.key)"
          >
            <font-awesome-icon :icon="tab.icon" class="me-2" />
            {{ tab.label }}
            <span
              v-if="tab.key === 'pending_verification' && resumen.pending_verification"
              class="badge rounded-pill bg-info text-dark ms-1"
              >{{ resumen.pending_verification }}</span
            >
            <span
              v-if="tab.key === 'pending_payment' && resumen.pending_payment"
              class="badge rounded-pill bg-warning text-dark ms-1"
              >{{ resumen.pending_payment }}</span
            >
          </button>
        </div>

        <div class="input-group shadow-sm rounded-pill overflow-hidden search-soft" style="max-width: 360px">
          <span class="input-group-text border-0 ps-3"
            ><font-awesome-icon icon="fa-solid fa-magnifying-glass" class="text-muted" />
          </span>
          <input
            v-model="filtro"
            type="text"
            class="form-control border-0 shadow-none"
            placeholder="Buscar por código, viajero, correo o documento..."
          />
        </div>
      </div>

      <div class="card-body p-0 position-relative" style="min-height: 300px">
        <div
          v-if="cargandoReservas"
          class="d-flex flex-column justify-content-center align-items-center h-100 position-absolute w-100 bg-white z-1"
          style="min-height: 300px"
        >
          <div class="spinner-border" style="width: 3rem; height: 3rem; color: var(--k-apple)" role="status">
            <span class="visually-hidden">Cargando...</span>
          </div>
          <p class="brand-handmade mt-3 mb-0">Actualizando las reservas del día...</p>
        </div>

        <div
          v-else-if="reservas.length === 0"
          class="d-flex flex-column justify-content-center align-items-center h-100 py-5 empty-state-copy"
        >
          <font-awesome-icon icon="fa-solid fa-leaf" class="display-6 mb-3" style="color: var(--k-apple)" />
          <h5 class="mb-1">No hay reservas en esta vista por ahora</h5>
          <p class="text-muted small mb-0">Cuando aparezcan nuevos movimientos, los verás aquí.</p>
        </div>

        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th class="ps-4 py-3 text-muted small fw-bold">CÓDIGO / CLIENTE</th>
                <th class="py-3 text-muted small fw-bold">HABITACIÓN</th>
                <th class="py-3 text-muted small fw-bold">FECHAS (IN - OUT)</th>
                <th class="py-3 text-muted small fw-bold">TOTAL</th>
                <th class="py-3 text-muted small fw-bold">ESTADO</th>
                <th class="text-center py-3 text-muted small fw-bold">ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="res in reservas" :key="res.id">
                <td class="ps-4">
                  <div class="fw-bold text-dark">
                    {{ res.code }}
                    <span
                      v-if="res.source === 'manual'"
                      class="badge bg-light text-muted border ms-1 fw-normal"
                      >Recepción</span
                    >
                  </div>
                  <div class="text-dark fw-bold" style="font-size: 0.9rem">
                    {{ res.guest?.full_name }}
                  </div>
                  <div class="text-muted mt-1" style="font-size: 0.75rem">
                    <font-awesome-icon icon="fa-solid fa-phone" class="me-1" />
                    {{ res.guest?.phone || "Sin celular" }} <br />
                    <font-awesome-icon icon="fa-solid fa-envelope" class="me-1" />
                    {{ res.guest?.email || "Sin correo" }}
                  </div>
                </td>
                <td>
                  <div class="fw-bold">{{ res.room?.name || "N/A" }}</div>
                  <div v-if="res.room?.number" class="small text-muted">N.º {{ res.room.number }}</div>
                </td>
                <td>
                  <div class="small text-muted"><strong>Entra:</strong> {{ formatDate(res.check_in) }}</div>
                  <div class="small text-muted"><strong>Sale:</strong> {{ formatDate(res.check_out) }}</div>
                  <div class="small text-muted">{{ res.nights }} noche(s)</div>
                </td>
                <td>
                  <div class="fw-bold text-success">{{ money(res.total_amount) }}</div>
                  <div class="small text-muted">Anticipo: {{ money(res.deposit_amount) }}</div>
                  <div
                    v-if="res.calculated_amount && res.total_amount !== res.calculated_amount"
                    class="small text-warning-emphasis"
                    :title="`Tarifa calculada: ${money(res.calculated_amount)}`"
                  >
                    Precio ajustado
                  </div>
                </td>
                <td>
                  <span
                    class="badge rounded-pill px-3 py-2 d-inline-flex align-items-center fw-normal"
                    :class="SOFT_BADGES[res.status] || 'badge-soft-neutral'"
                  >
                    <font-awesome-icon :icon="statusMeta(res.status).icon" class="me-2" />
                    {{ statusMeta(res.status).label }}
                  </span>
                  <div
                    v-if="res.status === 'pending_payment' && res.payment_due_at"
                    class="small text-muted mt-1"
                  >
                    Vence: {{ formatDateTime(res.payment_due_at) }}
                  </div>
                  <div
                    v-if="res.status_reason && ['pending_payment', 'cancelled'].includes(res.status)"
                    class="small text-muted mt-1 reason-text"
                    :title="res.status_reason"
                  >
                    Motivo: {{ res.status_reason }}
                  </div>
                </td>
                <td class="text-center align-middle">
                  <div class="d-flex justify-content-center flex-wrap gap-2">
                    <button
                      v-if="res.has_receipt && res.receipt_url && puedeVerComprobantes"
                      type="button"
                      class="btn btn-sm btn-outline-info rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Ver comprobante de pago"
                      @click="verComprobante(res)"
                    >
                      <font-awesome-icon icon="fa-solid fa-images" class="fs-6" />
                    </button>

                    <button
                      v-if="puede(res, 'confirmed')"
                      class="btn btn-sm btn-outline-success rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Aprobar pago"
                      @click="actualizarEstado(res, 'confirmed')"
                    >
                      <font-awesome-icon icon="fa-solid fa-check" class="fs-6" />
                    </button>

                    <button
                      v-if="res.status === 'pending_verification' && puede(res, 'pending_payment')"
                      class="btn btn-sm btn-outline-warning rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Rechazar comprobante"
                      @click="actualizarEstado(res, 'pending_payment')"
                    >
                      <font-awesome-icon icon="fa-solid fa-rotate-left" class="fs-6" />
                    </button>

                    <button
                      v-if="puede(res, 'checked_in')"
                      class="btn btn-sm btn-outline-primary rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Hacer check-in"
                      @click="abrirModalEdicion(res, true)"
                    >
                      <font-awesome-icon icon="fa-solid fa-door-open" class="fs-6" />
                    </button>

                    <button
                      v-if="puedeEditar && !['checked_out', 'cancelled'].includes(res.status)"
                      class="btn btn-sm btn-outline-dark rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Editar datos de la reserva"
                      @click="abrirModalEdicion(res, false)"
                    >
                      <font-awesome-icon icon="fa-regular fa-pen-to-square" class="fs-6" />
                    </button>

                    <button
                      v-if="puede(res, 'checked_out')"
                      class="btn btn-sm btn-outline-secondary rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Hacer check-out"
                      @click="actualizarEstado(res, 'checked_out')"
                    >
                      <font-awesome-icon icon="fa-solid fa-right-from-bracket" class="fs-6" />
                    </button>

                    <button
                      v-if="puedeVerFolio && ['checked_in', 'checked_out'].includes(res.status)"
                      class="btn btn-sm btn-outline-info rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Ver folio / cuenta del huésped"
                      @click="abrirModalFolio(res)"
                    >
                      <font-awesome-icon icon="fa-solid fa-receipt" class="fs-6" />
                    </button>

                    <button
                      v-if="puede(res, 'cancelled')"
                      class="btn btn-sm btn-outline-danger rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm action-btn"
                      title="Cancelar reserva"
                      @click="actualizarEstado(res, 'cancelled')"
                    >
                      <font-awesome-icon icon="fa-solid fa-xmark" class="fs-6" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="totalPaginas > 1"
          class="d-flex flex-column flex-md-row justify-content-between align-items-center p-3 bg-light border-top"
        >
          <span class="text-muted small fw-bold mb-2 mb-md-0">
            Mostrando página {{ paginaActual }} de {{ totalPaginas }} · {{ totalRegistros }} reservas
          </span>
          <div class="btn-group shadow-sm">
            <button
              :disabled="paginaActual === 1"
              class="btn btn-sm btn-white border"
              @click="cambiarPagina(paginaActual - 1)"
            >
              <font-awesome-icon icon="fa-solid fa-chevron-left" class="me-1" /> Anterior
            </button>
            <button
              :disabled="paginaActual >= totalPaginas"
              class="btn btn-sm btn-white border"
              @click="cambiarPagina(paginaActual + 1)"
            >
              Siguiente <font-awesome-icon icon="fa-solid fa-chevron-right" class="ms-1" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <ModalEdicionReserva
      :show="mostrarModalEdicion"
      :reserva="reservaAEditar"
      :modo-check-in="esModoCheckIn"
      @close="mostrarModalEdicion = false"
      @actualizado="refrescarTabla"
    />
    <ModalFolio :show="mostrarModalFolio" :reserva="reservaParaFolio" @close="mostrarModalFolio = false" />
  </div>
</template>

<style scoped>
.eco-card {
  background: linear-gradient(135deg, rgba(139, 207, 91, 0.08) 0%, var(--k-cream) 100%);
  border: 1px solid var(--k-border);
}

.eco-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(15, 59, 42, 0.08);
}

.icon-box {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  font-size: 1.2rem;
}

.tone-apple-box {
  background: rgba(139, 207, 91, 0.2);
  color: var(--k-forest);
}

.tone-sky-box {
  background: var(--k-sky-soft);
  color: var(--k-sky);
}

.tone-bed-box {
  background: rgba(36, 64, 58, 0.1);
  color: var(--k-forest);
}

.action-btn {
  width: 35px;
  height: 35px;
}

.clickable {
  cursor: pointer;
}

.reason-text {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.small-label {
  font-size: 0.75rem;
  letter-spacing: 0.5px;
}

.filter-chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
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
  border-color: rgba(139, 207, 91, 0.35);
}

.filter-chip.active {
  background: rgba(139, 207, 91, 0.2);
  color: var(--k-forest);
  border-color: rgba(139, 207, 91, 0.45);
  box-shadow: 0 8px 18px rgba(139, 207, 91, 0.14);
}

.search-soft,
.search-soft .input-group-text,
.search-soft .form-control {
  background: var(--k-offwhite);
}

.table thead th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.table tbody tr:hover {
  background: rgba(238, 248, 253, 0.32);
}

.btn-group .btn:hover {
  background-color: #f8f9fa;
}

.empty-state-copy {
  font-family: "Handlee", cursive;
  color: var(--k-forest);
}

.badge-soft-apple {
  background: rgba(139, 207, 91, 0.18);
  color: var(--k-forest);
  border: 1px solid rgba(139, 207, 91, 0.45);
}

.badge-soft-sand {
  background: var(--k-sand-soft);
  color: var(--k-sand);
  border: 1px solid rgba(212, 175, 55, 0.32);
}

.badge-soft-sky {
  background: var(--k-sky-soft);
  color: var(--k-sky);
  border: 1px solid rgba(52, 152, 219, 0.25);
}

.badge-soft-neutral {
  background: rgba(36, 64, 58, 0.08);
  color: var(--k-forest);
  border: 1px solid rgba(36, 64, 58, 0.18);
}

.badge-soft-rose {
  background: rgba(229, 184, 184, 0.2);
  color: #8a4c4c;
  border: 1px solid rgba(229, 184, 184, 0.5);
}
</style>
