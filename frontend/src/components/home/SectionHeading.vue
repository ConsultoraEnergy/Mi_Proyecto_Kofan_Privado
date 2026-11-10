<script setup>
/** Encabezado centrado de sección pública: antetítulo + título. `light` para fondos oscuros. */
defineProps({
  eyebrow: { type: String, default: "" },
  title: { type: String, required: true },
  light: { type: Boolean, default: false },
});
</script>

<template>
  <div class="text-center section-heading">
    <span v-if="eyebrow" :class="light ? 'eyebrow-light' : 'eyebrow'">{{ eyebrow }}</span>
    <h2 :class="light ? 'title-light' : 'title'">
      <slot>{{ title }}</slot>
    </h2>
    <slot name="after" />
  </div>
</template>

<style scoped>
.eyebrow,
.eyebrow-light {
  font-family: "Handlee", cursive;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--k-forest-soft);
  font-weight: 700;
}

.title {
  font-family: "Handlee", cursive;
  font-size: 2.8rem;
  color: var(--k-forest);
  margin: 15px 0;
}
</style>
