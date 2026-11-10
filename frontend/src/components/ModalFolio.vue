<script setup>
import { ref, reactive, watch, computed } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { getFolioByBooking, addFolioCharge, removeFolioCharge } from "@/api/operations";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { PERMISSIONS } from "@/constants/booking";
import { formatDate, formatDateTime, formatMoney } from "@/utils/format";

const props = defineProps({
  show: Boolean,
  reserva: { type: Object, default: null },
});

const emit = defineEmits(["close"]);

const auth = useAuthStore();
const configStore = useConfigStore();

const generando = ref(false);
const folio = ref(null);
const cargando = ref(false);
const errorMensaje = ref("");
const guardandoCargo = ref(false);
const nuevoCargo = reactive({ description: "", amount: "" });

const hotel = computed(() => configStore.data);
const puedeEditar = computed(() => folio.value?.status === "open" && auth.can(PERMISSIONS.FOLIOS_WRITE));
const money = (value) => formatMoney(value, configStore.data.currency);

const cargarFolio = async () => {
  cargando.value = true;
  errorMensaje.value = "";
  folio.value = null;
  try {
    folio.value = await getFolioByBooking(props.reserva.id);
  } catch (error) {
    errorMensaje.value =
      error?.response?.status === 404
        ? "Esta reserva aún no tiene folio. El folio (cuenta del huésped) se abre automáticamente al hacer el check-in."
        : errorMessage(error, "No se pudo consultar el folio del huésped.");
  } finally {
    cargando.value = false;
  }
};

watch(
  () => props.show,
  (visible) => {
    if (visible && props.reserva) {
      nuevoCargo.description = "";
      nuevoCargo.amount = "";
      configStore.fetchSiteConfig();
      cargarFolio();
    }
  },
);

const agregarCargo = async () => {
  const description = nuevoCargo.description.trim();
  const amount = Number(nuevoCargo.amount);
  if (!description || !(amount > 0)) {
    Swal.fire("Datos incompletos", "Escribe el concepto y un valor mayor a cero.", "warning");
    return;
  }
  guardandoCargo.value = true;
  try {
    folio.value = await addFolioCharge(folio.value.id, description, amount);
    nuevoCargo.description = "";
    nuevoCargo.amount = "";
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo registrar el consumo."), "error");
  } finally {
    guardandoCargo.value = false;
  }
};

const quitarCargo = async (cargo) => {
  const result = await Swal.fire({
    title: "¿Quitar este consumo?",
    text: `${cargo.description} · ${money(cargo.amount)}`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, quitar",
    cancelButtonText: "Volver",
  });
  if (!result.isConfirmed) return;
  try {
    folio.value = await removeFolioCharge(folio.value.id, cargo.id);
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo quitar el consumo."), "error");
  }
};

const cerrar = () => {
  emit("close");
};

const descargarPDF = async () => {
  if (!folio.value) return;
  generando.value = true;

  try {
    const { default: html2pdf } = await import("html2pdf.js");
    const elemento = document.getElementById("documento-folio");

    const opciones = {
      margin: 10,
      filename: `Folio_${folio.value.number}_${folio.value.guest_name || "Huesped"}.pdf`,
      image: { type: "jpeg", quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, ignoreElements: (el) => el.classList?.contains("no-print") },
      jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    };

    await html2pdf().set(opciones).from(elemento).save();
  } catch (error) {
    Swal.fire("Error", "No se pudo generar el PDF.", "error");
  } finally {
    generando.value = false;
  }
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
      <div class="bg-dark text-white p-3 d-flex justify-content-between align-items-center">
        <h5 class="mb-0 fw-bold">
          <font-awesome-icon icon="fa-solid fa-receipt" class="text-warning me-2" />
          Folio / cuenta del huésped<span v-if="folio"> N.º {{ folio.number }}</span>
        </h5>
        <button class="btn btn-sm text-white fs-5 border-0 hover-danger" @click="cerrar">
          <font-awesome-icon icon="fa-solid fa-xmark" />
        </button>
      </div>

      <div class="p-4 overflow-auto bg-light" style="flex: 1">
        <div v-if="cargando" class="text-center py-5">
          <div class="spinner-border text-success mb-3" role="status"></div>
          <p class="text-muted fw-bold">Consultando la cuenta del huésped...</p>
        </div>

        <div v-else-if="errorMensaje" class="text-center py-5 bg-white rounded shadow-sm border">
          <font-awesome-icon icon="fa-solid fa-receipt" class="display-1 text-muted opacity-50 mb-3" />
          <h5 class="fw-bold text-dark">Folio no disponible</h5>
          <p class="text-muted w-75 mx-auto">{{ errorMensaje }}</p>
        </div>

        <template v-else-if="folio">
          <div v-if="puedeEditar" class="bg-white p-3 border rounded shadow-sm mb-3">
            <h6 class="fw-bold text-success mb-2">Registrar consumo extra</h6>
            <form class="row g-2 align-items-end" @submit.prevent="agregarCargo">
              <div class="col-md-7">
                <label class="form-label small fw-bold text-muted mb-1">Concepto</label>
                <input
                  v-model="nuevoCargo.description"
                  type="text"
                  class="form-control form-control-sm"
                  placeholder="Ej: 2 cervezas, 1 desayuno..."
                  maxlength="200"
                  required
                />
              </div>
              <div class="col-md-3">
                <label class="form-label small fw-bold text-muted mb-1">Valor</label>
                <input
                  v-model="nuevoCargo.amount"
                  type="number"
                  class="form-control form-control-sm"
                  min="1"
                  step="any"
                  placeholder="15000"
                  required
                />
              </div>
              <div class="col-md-2 d-grid">
                <button type="submit" class="btn btn-sm btn-success" :disabled="guardandoCargo">
                  <span v-if="guardandoCargo" class="spinner-border spinner-border-sm"></span>
                  <template v-else><font-awesome-icon icon="fa-solid fa-plus" /> Agregar</template>
                </button>
              </div>
            </form>
          </div>

          <div id="documento-folio" class="bg-white p-5 border rounded shadow-sm" style="color: #333">
            <div class="row border-bottom pb-3 mb-4 align-items-center">
              <div class="col-sm-6">
                <h2 class="fw-bold text-uppercase" style="color: #0f3b2a">{{ configStore.hotelName }}</h2>
                <p v-if="hotel.address || hotel.city" class="mb-0 small">
                  {{ [hotel.address, hotel.city, hotel.country].filter(Boolean).join(", ") }}
                </p>
                <p v-if="hotel.phone" class="mb-0 small">Tel: {{ hotel.phone }}</p>
                <p v-if="hotel.contact_email" class="mb-0 small">Email: {{ hotel.contact_email }}</p>
              </div>
              <div class="col-sm-6 text-end">
                <h4 class="text-muted mb-1">FOLIO N.º {{ folio.number }}</h4>
                <p class="mb-0 fw-bold">
                  Reserva: <span class="fw-normal">{{ folio.booking_code }}</span>
                </p>
                <p class="mb-0 fw-bold">
                  Apertura: <span class="fw-normal">{{ formatDateTime(folio.opened_at) }}</span>
                </p>
                <p v-if="folio.closed_at" class="mb-0 fw-bold">
                  Cierre: <span class="fw-normal">{{ formatDateTime(folio.closed_at) }}</span>
                </p>
                <span class="badge mt-1" :class="folio.status === 'open' ? 'bg-success' : 'bg-secondary'">
                  {{ folio.status === "open" ? "Abierto" : "Cerrado" }}
                </span>
              </div>
            </div>

            <div class="row mb-4">
              <div class="col-12">
                <h6 class="fw-bold border-bottom pb-1" style="color: #0f3b2a">Datos del Huésped</h6>
              </div>
              <div class="col-sm-6">
                <p class="mb-1"><strong>Nombre:</strong> {{ folio.guest_name }}</p>
                <p class="mb-1"><strong>Documento:</strong> {{ folio.guest_document || "N/A" }}</p>
              </div>
              <div class="col-sm-6 text-end">
                <p class="mb-1"><strong>Teléfono:</strong> {{ folio.guest_phone || "N/A" }}</p>
                <p class="mb-1"><strong>Email:</strong> {{ folio.guest_email }}</p>
              </div>
            </div>

            <h6 class="fw-bold border-bottom pb-1" style="color: #0f3b2a">Detalle de Servicios</h6>
            <table class="table table-bordered table-sm mt-3">
              <thead class="table-light">
                <tr>
                  <th>Descripción</th>
                  <th class="text-center">Fecha</th>
                  <th class="text-end">Valor</th>
                  <th v-if="puedeEditar" class="text-center no-print" style="width: 48px"></th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    Alojamiento - {{ folio.room_name
                    }}<span v-if="folio.room_number"> (N.º {{ folio.room_number }})</span> ·
                    {{ folio.nights }} noche(s)
                  </td>
                  <td class="text-center">
                    {{ formatDate(folio.check_in) }} al {{ formatDate(folio.check_out) }}
                  </td>
                  <td class="text-end">{{ money(folio.room_subtotal) }}</td>
                  <td v-if="puedeEditar" class="no-print"></td>
                </tr>
                <tr v-for="cargo in folio.charges" :key="cargo.id">
                  <td>Consumo: {{ cargo.description }}</td>
                  <td class="text-center">{{ formatDateTime(cargo.created_at) }}</td>
                  <td class="text-end">{{ money(cargo.amount) }}</td>
                  <td v-if="puedeEditar" class="text-center no-print">
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-danger py-0 px-1"
                      title="Quitar consumo"
                      @click="quitarCargo(cargo)"
                    >
                      <font-awesome-icon icon="fa-solid fa-trash" />
                    </button>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="2" class="text-end fw-bold">TOTAL:</td>
                  <td class="text-end fw-bold fs-5 text-success">{{ money(folio.total_amount) }}</td>
                  <td v-if="puedeEditar" class="no-print"></td>
                </tr>
              </tfoot>
            </table>

            <div class="mt-5 text-center text-muted small border-top pt-3">
              <p class="mb-0">¡Gracias por preferir {{ configStore.hotelName }}!</p>
              <p class="mb-0">Documento interno, no es factura electrónica.</p>
            </div>
          </div>
        </template>
      </div>

      <div class="p-3 bg-light border-top text-end">
        <button type="button" class="btn btn-secondary me-2" @click="cerrar">Cerrar</button>
        <button
          type="button"
          class="btn btn-danger px-4"
          :disabled="generando || !folio"
          @click="descargarPDF"
        >
          <span v-if="generando" class="spinner-border spinner-border-sm me-2"></span>
          <font-awesome-icon v-else icon="fa-solid fa-file-pdf" class="me-2" /> Descargar PDF
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
  background-color: rgba(0, 0, 0, 0.6);
  z-index: 1060;
  backdrop-filter: blur(4px);
}
.modal-box {
  animation: scaleIn 0.3s ease-out forwards;
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
#documento-folio {
  font-family: Arial, sans-serif;
}
</style>
