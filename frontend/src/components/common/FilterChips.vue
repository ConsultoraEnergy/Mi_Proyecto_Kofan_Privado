<script setup>
/**
 * Grupo de filtros tipo "chip" con v-model.
 * options: [{ key, label, icon?, count?, badgeClass? }]
 *  - con `badgeClass`, el contador solo aparece si es mayor que 0 (alertas: "3 por verificar");
 *  - sin `badgeClass`, el contador se muestra siempre (totales: "Todas 12").
 */
defineProps({
  options: { type: Array, required: true },
});

const model = defineModel({ type: String, required: true });
</script>

<template>
  <div class="filter-chip-group" role="group">
    <button
      v-for="option in options"
      :key="option.key"
      type="button"
      class="filter-chip"
      :class="{ active: model === option.key }"
      :aria-pressed="model === option.key"
      @click="model = option.key"
    >
      <font-awesome-icon v-if="option.icon" :icon="option.icon" class="me-2" />
      {{ option.label }}
      <template v-if="option.count !== undefined && option.count !== null">
        <span
          v-if="option.badgeClass && option.count"
          class="badge rounded-pill ms-1"
          :class="option.badgeClass"
        >
          {{ option.count }}
        </span>
        <span v-else-if="!option.badgeClass" class="chip-count">{{ option.count }}</span>
      </template>
    </button>
  </div>
</template>

<style scoped>
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
</style>
