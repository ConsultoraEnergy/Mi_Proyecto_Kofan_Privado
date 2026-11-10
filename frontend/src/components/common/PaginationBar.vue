<script setup>
defineProps({
  page: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  /** Si se indica, se muestra "· {total} {itemLabel}" junto a la página. */
  total: { type: Number, default: null },
  itemLabel: { type: String, default: "" },
});

defineEmits(["change"]);
</script>

<template>
  <div
    v-if="totalPages > 1"
    class="d-flex flex-column flex-md-row justify-content-between align-items-center gap-2 p-3 bg-light border-top"
  >
    <span class="text-muted small fw-bold">
      Página {{ page }} de {{ totalPages }}
      <template v-if="itemLabel && total !== null"> · {{ total }} {{ itemLabel }}</template>
    </span>
    <div class="btn-group shadow-sm">
      <button
        type="button"
        class="btn btn-sm btn-white border"
        :disabled="page <= 1"
        @click="$emit('change', page - 1)"
      >
        <font-awesome-icon icon="fa-solid fa-chevron-left" class="me-1" /> Anterior
      </button>
      <button
        type="button"
        class="btn btn-sm btn-white border"
        :disabled="page >= totalPages"
        @click="$emit('change', page + 1)"
      >
        Siguiente <font-awesome-icon icon="fa-solid fa-chevron-right" class="ms-1" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.btn-group .btn:hover {
  background-color: #f8f9fa;
}
</style>
