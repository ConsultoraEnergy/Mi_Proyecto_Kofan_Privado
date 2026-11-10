<script setup>
defineProps({
  hotelName: { type: String, required: true },
  tagline: { type: String, required: true },
});
</script>

<template>
  <section class="about-hero">
    <div class="container text-center">
      <span class="subtitulo-blanco">Nuestra Esencia</span>
      <h1 class="titulo-hero">Somos {{ hotelName }}</h1>
      <p class="lead-text">{{ tagline }}</p>
    </div>

    <div class="custom-shape-divider-bottom">
      <svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">
        <path
          class="shape-fill"
          d="M421.9,6.5c22.6-2.5,51.5,0.4,75.5,5.3c23.6,4.9,70.9,23.5,100.5,35.7c75.8,32.2,133.7,44.5,192.6,49.7 c23.6,2.1,48.7,3.5,103.4-2.5c54.7-6,106.2-25.6,106.2-25.6V0H0v30.3c0,0,72,32.6,158.4,30.5c39.2-0.7,92.8-6.7,134-22.4 c21.2-8.1,52.2-18.2,79.7-24.2C399.3,7.9,411.6,7.5,421.9,6.5z"
        ></path>
      </svg>
    </div>
  </section>
</template>

<style scoped>
.about-hero {
  position: relative;
  background: linear-gradient(135deg, var(--k-forest) 0%, var(--k-forest-soft) 100%);
  color: var(--k-cream);
  padding: 120px 20px 100px;
  text-align: center;
}

.subtitulo-blanco {
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--k-apple-light);
  font-weight: 700;
}

.titulo-hero {
  font-family: "Handlee", cursive;
  font-size: 3.5rem;
  margin-top: 15px;
}

.lead-text {
  max-width: 700px;
  margin: 20px auto 0;
  font-size: 1.2rem;
  opacity: 0.9;
}

.custom-shape-divider-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  line-height: 0;
  transform: rotate(180deg);
}

.custom-shape-divider-bottom svg {
  display: block;
  width: 100%;
  height: 60px;
}

.shape-fill {
  fill: var(--k-cream); /* Debe coincidir con el fondo de la siguiente sección */
}
</style>
