<script setup>
/** Selector de amenidades (v-model: lista de nombres seleccionados). */
defineProps({
  options: { type: Array, required: true },
});

const selected = defineModel({ type: Array, default: () => [] });
</script>

<template>
  <div class="row g-2">
    <div v-for="(amenity, index) in options" :key="amenity" class="col-md-4 col-sm-6">
      <div
        class="form-check form-switch p-2 rounded bg-light border border-light-subtle"
        :class="{ 'border-success bg-success-subtle': selected.includes(amenity) }"
      >
        <input
          :id="`amenity-${index}`"
          v-model="selected"
          class="form-check-input ms-1 me-2"
          type="checkbox"
          role="switch"
          :value="amenity"
        />
        <label class="form-check-label text-dark" :for="`amenity-${index}`" style="cursor: pointer">
          {{ amenity }}
        </label>
      </div>
    </div>
  </div>
</template>
