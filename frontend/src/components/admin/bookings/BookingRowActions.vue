<script setup>
/**
 * Botones de acción de una reserva. Solo muestra lo que el usuario puede hacer según sus permisos
 * y la máquina de estados; la validación real sigue estando en el backend.
 */
import { computed } from "vue";
import { BOOKING_STATUS as S, canTransition } from "@/constants/booking";

const props = defineProps({
  booking: { type: Object, required: true },
  /** { changeStatus, edit, viewReceipts, viewFolio } */
  can: { type: Object, required: true },
});

defineEmits(["receipt", "transition", "check-in", "edit", "folio"]);

const allows = (target) => props.can.changeStatus && canTransition(props.booking.status, target);
const status = computed(() => props.booking.status);

const show = computed(() => ({
  receipt: props.can.viewReceipts && props.booking.has_receipt && !!props.booking.receipt_url,
  approve: allows(S.CONFIRMED),
  reject: status.value === S.PENDING_VERIFICATION && allows(S.PENDING_PAYMENT),
  checkIn: allows(S.CHECKED_IN),
  edit: props.can.edit && ![S.CHECKED_OUT, S.CANCELLED].includes(status.value),
  checkOut: allows(S.CHECKED_OUT),
  folio: props.can.viewFolio && [S.CHECKED_IN, S.CHECKED_OUT].includes(status.value),
  cancel: allows(S.CANCELLED),
}));
</script>

<template>
  <div class="d-flex justify-content-center flex-wrap gap-2">
    <button
      v-if="show.receipt"
      type="button"
      class="btn btn-sm btn-outline-info rounded-circle action-btn"
      title="Ver comprobante de pago"
      @click="$emit('receipt', booking)"
    >
      <font-awesome-icon icon="fa-solid fa-images" class="fs-6" />
    </button>

    <button
      v-if="show.approve"
      type="button"
      class="btn btn-sm btn-outline-success rounded-circle action-btn"
      title="Aprobar pago"
      @click="$emit('transition', booking, S.CONFIRMED)"
    >
      <font-awesome-icon icon="fa-solid fa-check" class="fs-6" />
    </button>

    <button
      v-if="show.reject"
      type="button"
      class="btn btn-sm btn-outline-warning rounded-circle action-btn"
      title="Rechazar comprobante"
      @click="$emit('transition', booking, S.PENDING_PAYMENT)"
    >
      <font-awesome-icon icon="fa-solid fa-rotate-left" class="fs-6" />
    </button>

    <button
      v-if="show.checkIn"
      type="button"
      class="btn btn-sm btn-outline-primary rounded-circle action-btn"
      title="Hacer check-in"
      @click="$emit('check-in', booking)"
    >
      <font-awesome-icon icon="fa-solid fa-door-open" class="fs-6" />
    </button>

    <button
      v-if="show.edit"
      type="button"
      class="btn btn-sm btn-outline-dark rounded-circle action-btn"
      title="Editar datos de la reserva"
      @click="$emit('edit', booking)"
    >
      <font-awesome-icon icon="fa-regular fa-pen-to-square" class="fs-6" />
    </button>

    <button
      v-if="show.checkOut"
      type="button"
      class="btn btn-sm btn-outline-secondary rounded-circle action-btn"
      title="Hacer check-out"
      @click="$emit('transition', booking, S.CHECKED_OUT)"
    >
      <font-awesome-icon icon="fa-solid fa-right-from-bracket" class="fs-6" />
    </button>

    <button
      v-if="show.folio"
      type="button"
      class="btn btn-sm btn-outline-info rounded-circle action-btn"
      title="Ver folio / cuenta del huésped"
      @click="$emit('folio', booking)"
    >
      <font-awesome-icon icon="fa-solid fa-receipt" class="fs-6" />
    </button>

    <button
      v-if="show.cancel"
      type="button"
      class="btn btn-sm btn-outline-danger rounded-circle action-btn"
      title="Cancelar reserva"
      @click="$emit('transition', booking, S.CANCELLED)"
    >
      <font-awesome-icon icon="fa-solid fa-xmark" class="fs-6" />
    </button>
  </div>
</template>

<style scoped>
.action-btn {
  width: 35px;
  height: 35px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--bs-box-shadow-sm);
}
</style>
