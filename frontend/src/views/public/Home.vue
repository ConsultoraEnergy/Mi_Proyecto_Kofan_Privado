<script setup>
import { ref } from "vue";
import { useReservaStore } from "@/stores/reserva";
import HomeHero from "@/components/home/HomeHero.vue";
import RoomCatalog from "@/components/home/RoomCatalog.vue";
import HomeExperiences from "@/components/home/HomeExperiences.vue";
import GalleryPreview from "@/components/home/GalleryPreview.vue";
import HotelLocation from "@/components/home/HotelLocation.vue";

const resStore = useReservaStore();
const catalog = ref(null);

/** El buscador encontró una habitación libre: se muestra su tarjeta o se abre la reserva. */
function onRoomFound({ habitacion, fechas }) {
  if (fechas?.start && fechas?.end) {
    resStore.selectedDateRange = { start: new Date(fechas.start), end: new Date(fechas.end) };
  }

  if (catalog.value?.openRoomDetails(habitacion.id)) {
    window.scrollTo({ top: 500, behavior: "smooth" });
  } else {
    // La habitación no está en el catálogo visible: se abre directamente la reserva.
    resStore.openModal(habitacion);
  }
}
</script>

<template>
  <main>
    <HomeHero @room-found="onRoomFound" />
    <RoomCatalog ref="catalog" />
    <HomeExperiences />
    <GalleryPreview />
    <HotelLocation />
  </main>
</template>

<style scoped>
main {
  background: var(--k-cream);
  color: var(--k-forest-soft);
  font-family: "Forum", serif;
}
</style>
