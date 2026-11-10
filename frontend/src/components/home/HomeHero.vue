<script setup>
/** Portada con el buscador de disponibilidad flotando sobre la imagen. */
import { useConfigStore } from "@/stores/config";
import SearchAvailability from "@/components/SearchAvailability.vue";

defineEmits(["room-found"]);

const configStore = useConfigStore();
</script>

<template>
  <section id="hero-brand" class="position-relative">
    <h1 class="visually-hidden">{{ configStore.hotelName }}</h1>
    <div class="hero-overlay"></div>

    <div class="position-absolute start-50 translate-middle w-100 px-3 search-wrapper" style="top: 60%">
      <SearchAvailability @habitacion-encontrada="$emit('room-found', $event)" />
    </div>
  </section>
</template>

<style scoped>
#hero-brand {
  position: relative;
  min-height: 104vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url("@/img/portadaimg.jpg");
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  margin-top: -80px; /* La imagen sube por debajo del navbar transparente */
  padding-top: 80px;
}

.hero-overlay {
  position: absolute;
  top: 9%;
  left: 3%;
  right: 3%;
  bottom: 20%;
  background: linear-gradient(to bottom, rgba(15, 59, 42, 0.7) 0%, rgba(15, 59, 42, 0.4) 100%);
  z-index: 0;
  border-radius: 20px;
}

.search-wrapper {
  max-width: 1150px; /* Evita que el buscador se estire demasiado en pantallas grandes */
  z-index: 20; /* El calendario y sus popovers quedan por encima de todo */
}
</style>
