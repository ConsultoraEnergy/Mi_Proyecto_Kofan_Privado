/**
 * Reserva web (invitado o con sesión).
 *
 * El precio SIEMPRE lo calcula el servidor: aquí solo se muestra la cotización de
 * GET /rooms/{id}/quote. El cálculo local (noches × precio) es una vista previa temporal
 * mientras llega la cotización y nunca se envía.
 */
import { defineStore } from "pinia";
import { ref, reactive, computed, watch } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { getBookedDates, getQuote } from "@/api/rooms";
import { createWebBooking } from "@/api/bookings";
import { useConfigStore } from "@/stores/config";
import { statusLabel } from "@/constants/booking";
import { fromIsoDate, nightsBetween, toIsoDate } from "@/utils/format";

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");
const COLOR_DANGER = getBrandColor("--k-danger", "#e74c3c");

export const RECEIPT_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
export const RECEIPT_MAX_MB = 5;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export const useReservaStore = defineStore("reserva", () => {
  const isModalOpen = ref(false);
  const isSubmitting = ref(false);
  const habitacionSeleccionada = ref(null);

  const selectedDateRange = ref(null);
  const disabledDates = ref([]);
  const minDate = ref(new Date());

  // Cotización del servidor
  const quote = ref(null);
  const quoteLoading = ref(false);
  const quoteError = ref("");
  let quoteRequestId = 0;

  const form = reactive({
    nombreCompleto: "",
    correo: "",
    telefono: "",
    tipoDocumento: "CC",
    numeroDocumento: "",
    aceptaPolitica: false,
    comprobante: null,
    comprobantePreview: null,
  });

  const errors = reactive({
    nombreCompleto: false,
    correo: false,
    telefono: false,
    dates: false,
    comprobante: false,
    politica: false,
  });

  const checkIn = computed(() => toIsoDate(selectedDateRange.value?.start));
  const checkOut = computed(() => toIsoDate(selectedDateRange.value?.end));

  /** Resumen a mostrar: la cotización del servidor o, mientras llega, una estimación local. */
  const resumen = computed(() => {
    if (quote.value) return { ...quote.value, estimated: false };
    const nights = nightsBetween(checkIn.value, checkOut.value);
    const room = habitacionSeleccionada.value;
    if (!nights || !room) return null;
    const configStore = useConfigStore();
    const total = nights * (room.price_per_night || 0);
    const percent = configStore.data.deposit_percent;
    return {
      nights,
      price_per_night: room.price_per_night,
      total_amount: total,
      deposit_percent: percent,
      deposit_amount: (total * percent) / 100,
      currency: configStore.data.currency,
      estimated: true,
    };
  });

  const fetchQuote = async () => {
    const requestId = ++quoteRequestId;
    quote.value = null;
    quoteError.value = "";
    const room = habitacionSeleccionada.value;
    if (!room || !checkIn.value || !checkOut.value || checkIn.value === checkOut.value) {
      quoteLoading.value = false;
      return;
    }
    quoteLoading.value = true;
    try {
      const data = await getQuote(room.id, checkIn.value, checkOut.value);
      if (requestId === quoteRequestId) quote.value = data;
    } catch (error) {
      if (requestId === quoteRequestId) quoteError.value = errorMessage(error, "No pudimos calcular el precio de esas fechas.");
    } finally {
      if (requestId === quoteRequestId) quoteLoading.value = false;
    }
  };

  watch([() => habitacionSeleccionada.value?.id, checkIn, checkOut], fetchQuote);

  const fetchDisabledDates = async (roomId) => {
    disabledDates.value = [];
    try {
      const ranges = await getBookedDates(roomId);
      disabledDates.value = ranges
        .map(({ check_in, check_out }) => {
          const start = fromIsoDate(check_in);
          const end = fromIsoDate(check_out);
          // El día de salida queda libre para una nueva entrada (intervalo semiabierto).
          end.setDate(end.getDate() - 1);
          return end < start ? null : { start, end };
        })
        .filter(Boolean);
    } catch (error) {
      console.error("Error cargando fechas ocupadas:", error);
    }
  };

  /** Abre el formulario de reserva. Conserva las fechas ya elegidas (p. ej. desde el buscador). */
  const openModal = async (habitacion) => {
    clearErrors();
    habitacionSeleccionada.value = { ...habitacion };
    isModalOpen.value = true;
    await fetchDisabledDates(habitacion.id);
  };

  const closeModal = () => {
    isModalOpen.value = false;
    resetForm();
  };

  const clearErrors = () => {
    Object.keys(errors).forEach((key) => (errors[key] = false));
  };

  const removerComprobante = () => {
    if (form.comprobantePreview && form.comprobantePreview !== "pdf-icon") {
      URL.revokeObjectURL(form.comprobantePreview);
    }
    form.comprobante = null;
    form.comprobantePreview = null;
  };

  const handleFileUpload = (event) => {
    const file = event.target?.files?.[0] || event.dataTransfer?.files?.[0];
    if (event.target?.value) event.target.value = "";
    if (!file) return;

    if (!RECEIPT_TYPES.includes(file.type)) {
      Swal.fire({
        icon: "error",
        title: "Formato no permitido",
        text: "El comprobante debe ser una imagen JPG, PNG, WebP o un PDF.",
        confirmButtonColor: COLOR_DANGER,
      });
      return;
    }
    if (file.size > RECEIPT_MAX_MB * 1024 * 1024) {
      Swal.fire({
        icon: "error",
        title: "Archivo muy pesado",
        text: `El comprobante no puede superar ${RECEIPT_MAX_MB} MB.`,
        confirmButtonColor: COLOR_DANGER,
      });
      return;
    }

    removerComprobante();
    form.comprobante = file;
    form.comprobantePreview = file.type === "application/pdf" ? "pdf-icon" : URL.createObjectURL(file);
    errors.comprobante = false;
  };

  const resetForm = () => {
    form.nombreCompleto = "";
    form.correo = "";
    form.telefono = "";
    form.tipoDocumento = "CC";
    form.numeroDocumento = "";
    form.aceptaPolitica = false;
    removerComprobante();

    selectedDateRange.value = null;
    habitacionSeleccionada.value = null;
    disabledDates.value = [];
    clearErrors();
  };

  const validateForm = () => {
    clearErrors();
    if (!checkIn.value || !checkOut.value || checkIn.value === checkOut.value) errors.dates = true;
    if (!form.nombreCompleto.trim()) errors.nombreCompleto = true;
    if (!EMAIL_RE.test(form.correo.trim())) errors.correo = true;
    if (!String(form.telefono).trim()) errors.telefono = true;
    if (!form.comprobante) errors.comprobante = true;
    if (!form.aceptaPolitica) errors.politica = true;
    return !Object.values(errors).some(Boolean);
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      Swal.fire({
        icon: "error",
        title: "Faltan datos",
        text: "Verifica que hayas seleccionado fechas, llenado tus datos, subido el comprobante y aceptado la política de datos.",
        confirmButtonColor: COLOR_FOREST,
      });
      return false;
    }

    isSubmitting.value = true;
    Swal.fire({
      title: "Enviando reserva y comprobante...",
      allowOutsideClick: false,
      didOpen: () => Swal.showLoading(),
    });

    try {
      const booking = await createWebBooking(
        {
          room_id: habitacionSeleccionada.value.id,
          check_in: checkIn.value,
          check_out: checkOut.value,
          full_name: form.nombreCompleto.trim(),
          email: form.correo.trim(),
          phone: String(form.telefono).trim(),
          document_type: form.numeroDocumento.trim() ? form.tipoDocumento : null,
          document_number: form.numeroDocumento.trim() || null,
          accept_privacy_policy: true,
        },
        form.comprobante,
      );

      await Swal.fire({
        icon: "success",
        title: "¡Reserva solicitada!",
        html: `
          <p class="mb-1">Tu código de reserva es</p>
          <p class="fs-3 fw-bold mb-3">${escapeHtml(booking.code)}</p>
          <p class="mb-0">Estado: <strong>${escapeHtml(statusLabel(booking.status))}</strong>.
          El hotel revisará tu comprobante y te confirmará la reserva.</p>`,
        confirmButtonColor: COLOR_FOREST,
      });

      closeModal();
      return true;
    } catch (error) {
      Swal.fire({
        icon: "error",
        title: "Ups, algo salió mal",
        text: errorMessage(error, "No pudimos enviar tu reserva ni el comprobante. Intenta de nuevo."),
        confirmButtonColor: COLOR_DANGER,
      });
      return false;
    } finally {
      isSubmitting.value = false;
    }
  };

  return {
    isModalOpen, isSubmitting, form, errors, selectedDateRange, disabledDates, minDate,
    habitacionSeleccionada, quote, quoteLoading, quoteError, resumen,
    openModal, closeModal, handleSubmit, resetForm, handleFileUpload, removerComprobante,
  };
});
