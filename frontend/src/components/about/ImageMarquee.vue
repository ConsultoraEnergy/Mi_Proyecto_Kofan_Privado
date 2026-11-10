<script setup>
/**
 * Carrusel infinito de fotos. La lista se renderiza dos veces y la animación desplaza la mitad
 * del recorrido, así el salto al reiniciar no se nota. images: [{ src, alt }]
 */
import { computed } from "vue";

const props = defineProps({
  images: { type: Array, required: true },
});

const track = computed(() => [...props.images, ...props.images]);
</script>

<template>
  <section class="gallery-carousel py-5">
    <div class="container-fluid p-0">
      <div class="carousel-track" :style="{ '--count': images.length }">
        <div
          v-for="(image, index) in track"
          :key="index"
          class="carousel-item-img"
          :aria-hidden="index >= images.length"
        >
          <img :src="image.src" :alt="index >= images.length ? '' : image.alt" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.gallery-carousel {
  background-color: var(--k-cream);
  padding: 60px 0;
  overflow: hidden;
}

.carousel-track {
  display: flex;
  /* (ancho_foto + margen) * total de fotos renderizadas */
  width: calc(320px * var(--count) * 2);
  animation: scrollInfinito 40s linear infinite;
}

.carousel-track:hover {
  animation-play-state: paused; /* Se detiene para que el usuario aprecie la foto */
}

.carousel-item-img {
  width: 400px;
  height: 320px;
  flex-shrink: 0;
  margin: 0 10px;
  perspective: 1000px;
}

.carousel-item-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 20px;
  filter: grayscale(100%) contrast(110%);
  opacity: 0.7;
  transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  cursor: pointer;
}

.carousel-item-img img:hover {
  filter: grayscale(0%) contrast(100%);
  opacity: 1;
  transform: scale(1.05);
  box-shadow: 0 15px 30px rgba(15, 59, 42, 0.3);
}

@keyframes scrollInfinito {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(calc(-320px * var(--count)));
  }
}

@media (max-width: 768px) {
  .carousel-item-img {
    width: 220px;
    height: 180px;
  }
  .carousel-item-img img {
    filter: grayscale(0%);
    opacity: 1;
  }
  @keyframes scrollInfinito {
    0% {
      transform: translateX(0);
    }
    100% {
      transform: translateX(calc(-240px * var(--count)));
    }
  }
}

@media (prefers-reduced-motion: reduce) {
  .carousel-track {
    animation: none;
  }
}
</style>
