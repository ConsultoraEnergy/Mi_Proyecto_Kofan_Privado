<script setup>
/** Compromisos ambientales y métricas de impacto. */
defineProps({
  label: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  /** [{ icon, text }] */
  commitments: { type: Array, required: true },
  /** [{ value, label }] */
  metrics: { type: Array, required: true },
});
</script>

<template>
  <section class="impacto-local">
    <div class="container">
      <div class="row align-items-center">
        <div class="col-lg-6 mb-5 mb-lg-0">
          <span class="etiqueta-verde">{{ label }}</span>
          <h2 class="titulo-impacto">{{ title }}</h2>
          <p class="descripcion-impacto">{{ description }}</p>

          <ul class="lista-compromisos list-unstyled mb-0">
            <li v-for="item in commitments" :key="item.text" class="compromiso-item">
              <font-awesome-icon :icon="item.icon" class="icon-check" />
              <span>{{ item.text }}</span>
            </li>
          </ul>
        </div>

        <div class="col-lg-6">
          <div class="row g-4">
            <div v-for="metric in metrics" :key="metric.label" class="col-6">
              <div class="card-metrica">
                <p class="numero">{{ metric.value }}</p>
                <p class="concepto">{{ metric.label }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.impacto-local {
  background-color: var(--k-forest-soft);
  padding: 100px 20px;
  color: var(--k-cream);
}

.etiqueta-verde {
  color: var(--k-apple-light);
  text-transform: uppercase;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 2px;
}

.titulo-impacto {
  font-family: "Handlee", cursive;
  font-size: 3rem;
  margin: 15px 0 25px;
}

.descripcion-impacto {
  font-size: 1.1rem;
  line-height: 1.7;
  opacity: 0.9;
  margin-bottom: 30px;
}

.lista-compromisos {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.compromiso-item {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 1rem;
}

.icon-check {
  color: var(--k-apple-light);
  font-size: 1.2rem;
}

.card-metrica {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 30px 20px;
  border-radius: 25px;
  text-align: center;
  transition: all 0.3s ease;
  height: 100%;
}

.card-metrica:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-5px);
  border-color: var(--k-apple-light);
}

.numero {
  font-family: "Handlee", cursive;
  font-size: 2.5rem;
  font-weight: 500;
  line-height: 1.2;
  color: var(--k-apple-light);
  margin-bottom: 5px;
}

.concepto {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.8;
  margin: 0;
}

@media (max-width: 768px) {
  .titulo-impacto {
    font-size: 2.2rem;
  }
  .card-metrica {
    padding: 20px 10px;
  }
  .numero {
    font-size: 1.8rem;
  }
}
</style>
