<script setup>
import { computed } from "vue";

const props = defineProps({
  summary: { type: Object, required: true },
  inHouseGuests: { type: Number, default: null },
});

/** Se emite con la pestaña a abrir al pulsar una tarjeta con pendientes. */
defineEmits(["select"]);

const cards = computed(() => [
  {
    tab: "pending_verification",
    title: "Pagos por verificar",
    value: props.summary.pending_verification ?? 0,
    hint: "Comprobantes por revisar",
    icon: "fa-solid fa-receipt",
    tone: "tone-sky-box",
  },
  {
    tab: "pending_payment",
    title: "Pendientes de pago",
    value: props.summary.pending_payment ?? 0,
    hint: "Sin comprobante o rechazado",
    icon: "fa-solid fa-clock",
    tone: "tone-apple-box",
  },
  {
    tab: null,
    title: "Huéspedes hoy",
    value: props.inHouseGuests ?? "—",
    hint: "En las instalaciones",
    icon: "fa-solid fa-bed",
    tone: "tone-bed-box",
  },
]);
</script>

<template>
  <div class="row g-3 mb-4">
    <div v-for="card in cards" :key="card.title" class="col-md-4">
      <component
        :is="card.tab ? 'button' : 'div'"
        :type="card.tab ? 'button' : undefined"
        class="eco-card border-0 shadow-sm p-3 rounded-4 stats-card h-100 w-100 text-start"
        :class="{ clickable: card.tab }"
        @click="card.tab && $emit('select', card.tab)"
      >
        <div class="d-flex align-items-center justify-content-between">
          <div>
            <h6 class="text-muted fw-bold mb-2 text-uppercase small-label">{{ card.title }}</h6>
            <h3 class="fw-bold mb-1 text-brand">{{ card.value }}</h3>
            <p class="text-muted small mb-0">{{ card.hint }}</p>
          </div>
          <div class="icon-box" :class="card.tone">
            <font-awesome-icon :icon="card.icon" />
          </div>
        </div>
      </component>
    </div>
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

.clickable {
  cursor: pointer;
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

.small-label {
  font-size: 0.75rem;
  letter-spacing: 0.5px;
}
</style>
