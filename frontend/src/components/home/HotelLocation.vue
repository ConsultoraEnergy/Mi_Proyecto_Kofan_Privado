<script setup>
/** Ubicación y mapa; solo aparece si los ajustes del sitio tienen dirección o ciudad. */
import { useConfigStore } from "@/stores/config";
import { useHotelLocation } from "@/composables/useHotelLocation";
import SectionHeading from "@/components/home/SectionHeading.vue";

const configStore = useConfigStore();
const { hasLocation, locationText, mapUrl } = useHotelLocation();
</script>

<template>
  <section v-if="hasLocation" id="donde-estamos" class="ubicacion">
    <div class="divisor-entrada-verde">
      <svg viewBox="0 0 1200 120" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0,0V120H1200V0c-150,80-350,120-600,120S150,80,0,0Z" fill="var(--k-forest-soft)"></path>
      </svg>
    </div>
    <div class="container mt-5">
      <SectionHeading class="mb-5" eyebrow="¿Cómo llegar?" title="Nuestra ubicación" light>
        Nuestra ubicación<template v-if="configStore.data.city"> en {{ configStore.data.city }}</template>
        <template #after>
          <p>
            Nos encontramos en <strong>{{ locationText }}</strong
            >.
          </p>
        </template>
      </SectionHeading>
      <div class="mapa-wrapper shadow-soft">
        <iframe
          :src="mapUrl"
          :title="`Mapa de ${configStore.hotelName}`"
          width="100%"
          height="450"
          style="border: 0"
          loading="lazy"
        ></iframe>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ubicacion {
  position: relative;
  background-color: var(--k-forest-soft);
  padding: 100px 20px;
  color: var(--k-cream);
  margin-top: -1px;
}

.divisor-entrada-verde {
  position: absolute;
  top: -1px;
  left: 0;
  width: 100%;
  line-height: 0;
}

.divisor-entrada-verde svg {
  display: block;
  width: 100%;
  height: 60px;
}

.mapa-wrapper {
  max-width: 1000px;
  margin: 0 auto;
  border-radius: 30px;
  overflow: hidden;
  border: 8px solid rgba(255, 255, 255, 0.1);
}
</style>
