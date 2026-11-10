<script setup>
/** Preguntas frecuentes con el acordeón de Bootstrap. faqs: [{ question, answer: string }] */
import { useId } from "vue";

defineProps({
  faqs: { type: Array, required: true },
});

const accordionId = `faq-${useId()}`;
</script>

<template>
  <section class="faq-section py-5">
    <div class="container">
      <div class="text-center mb-5">
        <span class="subtitulo-verde">Dudas comunes</span>
        <h2 class="titulo-seccion">Preguntas Frecuentes</h2>
      </div>

      <div class="row justify-content-center">
        <div class="col-lg-8">
          <div :id="accordionId" class="accordion accordion-flush custom-accordion">
            <div v-for="(faq, index) in faqs" :key="faq.question" class="accordion-item shadow-sm mb-3">
              <h3 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-toggle="collapse"
                  :data-bs-target="`#${accordionId}-${index}`"
                  aria-expanded="false"
                  :aria-controls="`${accordionId}-${index}`"
                >
                  {{ faq.question }}
                </button>
              </h3>
              <div
                :id="`${accordionId}-${index}`"
                class="accordion-collapse collapse"
                :data-bs-parent="`#${accordionId}`"
              >
                <div class="accordion-body">{{ faq.answer }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.faq-section {
  background-color: rgba(15, 59, 42, 0.04);
}

.subtitulo-verde {
  color: var(--k-forest-soft);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-size: 0.9rem;
}

.titulo-seccion {
  font-family: "Handlee", cursive;
  font-size: 2.5rem;
  color: var(--k-forest);
  margin-bottom: 20px;
}

.accordion-header {
  font-size: 1rem;
}

.custom-accordion .accordion-item {
  border: none;
  border-radius: 15px !important;
  overflow: hidden;
}

.custom-accordion .accordion-button {
  font-weight: 600;
  color: var(--k-forest);
  padding: 20px;
  background-color: white;
  box-shadow: none;
}

.custom-accordion .accordion-button:not(.collapsed) {
  color: var(--k-forest-soft);
  background-color: var(--k-apple-soft);
}

.custom-accordion .accordion-button::after {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%231a5c43'%3e%3cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3e%3c/svg%3e");
}

.custom-accordion .accordion-body {
  font-size: 0.95rem;
  color: #555;
  line-height: 1.6;
  background-color: #f0f7f4;
}
</style>
