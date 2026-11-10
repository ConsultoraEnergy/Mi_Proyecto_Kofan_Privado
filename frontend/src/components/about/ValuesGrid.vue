<script setup>
/** values: [{ icon, title, text }] */
defineProps({
  values: { type: Array, required: true },
});
</script>

<template>
  <section id="nuestroValores">
    <div class="container mt-5 pt-4">
      <div class="text-center mb-5">
        <h2 class="titulo-valores">Nuestros Valores</h2>
      </div>
      <div class="grid-valores">
        <div v-for="value in values" :key="value.title" class="valor-item">
          <div class="valor-icon-sm"><font-awesome-icon :icon="value.icon" /></div>
          <h4>{{ value.title }}</h4>
          <p>{{ value.text }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.titulo-valores {
  font-family: "Handlee", cursive;
  font-size: 2.2rem;
  color: var(--k-forest);
  position: relative;
  display: inline-block;
}

.titulo-valores::after {
  content: "";
  position: absolute;
  width: 50%;
  height: 3px;
  background: var(--k-apple-light);
  bottom: -10px;
  left: 25%;
  border-radius: 2px;
}

.grid-valores {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
  padding-bottom: 40px;
}

.valor-item {
  text-align: center;
  padding: 20px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.valor-item:hover {
  background: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  transform: translateY(-5px);
}

.valor-icon-sm {
  font-size: 1.8rem;
  color: var(--k-forest-soft);
  margin-bottom: 15px;
}

.valor-item h4 {
  font-family: "Handlee", cursive;
  font-size: 1.4rem;
  color: var(--k-forest);
  margin-bottom: 10px;
}

.valor-item p {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .grid-valores {
    grid-template-columns: 1fr 1fr; /* Dos columnas en móvil */
    gap: 15px;
  }
}
</style>
