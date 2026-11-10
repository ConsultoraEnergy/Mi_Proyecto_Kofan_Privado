<script setup>
defineProps({
  title: { type: String, required: true },
  text: { type: String, required: true },
  image: { type: String, required: true },
  imageAlt: { type: String, default: "" },
});
</script>

<template>
  <section class="sobre-nosotros-detalle pb-5">
    <div class="container">
      <div class="row align-items-center">
        <div class="col-lg-6">
          <img :src="image" :alt="imageAlt" class="img-fluid rounded-4 shadow-lg mb-4 story-image" />
        </div>
        <div class="col-lg-6">
          <h2 class="titulo-seccion">{{ title }}</h2>
          <p class="texto-config">{{ text }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.story-image {
  object-fit: cover;
  width: 100%;
  height: 50%;
}

.titulo-seccion {
  font-family: "Handlee", cursive;
  font-size: 2.5rem;
  color: var(--k-forest);
  margin-bottom: 20px;
}

.texto-config {
  white-space: pre-line;
}
</style>
