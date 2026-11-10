/**
 * Acciones del personal sobre una reserva: cambiar de estado (con confirmación y motivo cuando
 * la máquina de estados lo exige) y abrir el comprobante privado.
 */
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { changeBookingStatus, openReceipt } from "@/api/bookings";
import { BOOKING_STATUS as S, requiresReason } from "@/constants/booking";
import { brandColors } from "@/utils/brandColors";

export const TRANSITION_COPY = Object.freeze({
  [S.CONFIRMED]: {
    title: "¿Aprobar el pago de esta reserva?",
    text: "El anticipo quedará validado y la reserva pasará a confirmada.",
    confirm: "Sí, aprobar pago",
    success: "Pago aprobado. La reserva quedó confirmada.",
  },
  [S.PENDING_PAYMENT]: {
    title: "Rechazar comprobante",
    text: "Indica al huésped por qué no se pudo validar el pago. Podrá subir un nuevo comprobante.",
    confirm: "Rechazar comprobante",
    success: "Comprobante rechazado. Se notificó al huésped.",
  },
  [S.CHECKED_IN]: {
    title: "¿Registrar la llegada?",
    text: "Se abrirá la cuenta (folio) del huésped.",
    confirm: "Sí, hacer check-in",
    success: "Todo preparado para la llegada de este viajero.",
  },
  [S.CHECKED_OUT]: {
    title: "¿Cerrar la estancia?",
    text: "La salida quedará registrada y el folio del huésped se cerrará.",
    confirm: "Sí, hacer check-out",
    success: "Check-out registrado. El folio quedó cerrado.",
  },
  [S.CANCELLED]: {
    title: "¿Deseas cancelar esta reserva?",
    text: "Las fechas volverán a quedar disponibles. El motivo se mostrará al huésped.",
    confirm: "Sí, cancelar",
    success: "La reserva fue cancelada.",
  },
});

/** `onChanged` se ejecuta tras un cambio de estado exitoso (p. ej. recargar la tabla). */
export function useBookingActions({ onChanged = async () => {} } = {}) {
  async function changeStatus(booking, target) {
    const copy = TRANSITION_COPY[target];
    const withReason = requiresReason(booking.status, target);
    const colors = brandColors();

    const result = await Swal.fire({
      title: copy.title,
      text: `${booking.code} · ${booking.guest?.full_name || ""}. ${copy.text}`,
      icon: withReason ? "warning" : "question",
      ...(withReason && {
        input: "textarea",
        inputLabel: "Motivo (obligatorio)",
        inputPlaceholder: "Ej.: el valor transferido no coincide con el anticipo",
        inputValidator: (value) => (!value || !value.trim() ? "Debes escribir un motivo." : undefined),
      }),
      showCancelButton: true,
      confirmButtonColor: colors.apple,
      cancelButtonColor: colors.forest,
      confirmButtonText: copy.confirm,
      cancelButtonText: "Volver",
    });
    if (!result.isConfirmed) return false;

    try {
      await changeBookingStatus(booking.id, target, withReason ? result.value.trim() : null);
      await onChanged();
      Swal.fire({
        title: "Movimiento actualizado",
        text: copy.success,
        icon: "success",
        timer: 1700,
        showConfirmButton: false,
      });
      return true;
    } catch (error) {
      Swal.fire(
        "No fue posible actualizar esta reserva",
        errorMessage(error, "Inténtalo nuevamente en unos segundos."),
        "error",
      );
      return false;
    }
  }

  // El comprobante es privado: se descarga con el token y se abre en una pestaña nueva.
  // Debe llamarse directo desde el clic para que el navegador no bloquee la pestaña.
  function viewReceipt(booking) {
    openReceipt(booking.receipt_url).catch((error) => {
      Swal.fire("Error", errorMessage(error, "No se pudo cargar el comprobante de pago."), "error");
    });
  }

  return { changeStatus, viewReceipt };
}
