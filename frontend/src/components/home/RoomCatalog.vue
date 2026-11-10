<script setup>
/** Catálogo público agrupado por tipo de habitación. */
import { onMounted } from "vue";
import { useRoomCatalog } from "@/composables/useRoomCatalog";
import RoomCard from "@/components/RoomCard.vue";

const { sections, loading, error, load } = useRoomCatalog();

// Tarjetas renderizadas (por id de habitación) para abrir sus detalles desde el buscador.
const cards = new Map();
const registerCard = (id, el) => {
  if (el) cards.set(id, el);
  else cards.delete(id);
};

/** Abre el detalle de la habitación si está en el catálogo visible. Devuelve false si no está. */
function openRoomDetails(roomId) {
  const card = cards.get(roomId);
  if (!card) return false;
  card.abrirDetalles();
  return true;
}

defineExpose({ openRoomDetails });

onMounted(load);
</script>

<template>
  <section id="catalogo" class="catalogo-section py-5">
    <div v-if="loading" class="container pb-5 text-center">
      <div class="empty-state" role="status">Cargando alojamientos disponibles...</div>
    </div>

    <div v-else-if="error" class="container pb-5 text-center">
      <div class="empty-state empty-state--warning">
        <p class="mb-3">{{ error }}</p>
        <button type="button" class="btn btn-primary px-4" @click="load">Reintentar</button>
      </div>
    </div>

    <div v-else-if="sections.length === 0" class="container pb-5 text-center">
      <div class="empty-state">Aún no hay alojamientos disponibles para mostrar.</div>
    </div>

    <template v-else>
      <div
        v-for="(section, idx) in sections"
        :key="section.code"
        class="container"
        :class="idx === sections.length - 1 ? 'pb-5' : 'mb-5'"
      >
        <div class="d-flex align-items-center mb-4">
          <div class="linea-verde"></div>
          <h3 class="mx-3 fw-bold verde-brand titulo-categoria">{{ section.name }}</h3>
        </div>
        <div class="rooms-grid">
          <RoomCard
            v-for="room in section.rooms"
            :key="room.id"
            :ref="(el) => registerCard(room.id, el)"
            :habitacion="room"
          />
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.catalogo-section {
  background-color: var(--k-cream);
}

.btn {
  font-family: "Handlee", cursive;
}

.linea-verde {
  height: 4px;
  width: 50px;
  background-color: var(--k-apple);
  border-radius: 2px;
}

.titulo-categoria {
  font-size: 2.5rem;
  font-family: "Handlee", cursive;
  letter-spacing: 1px;
}

@media (max-width: 768px) {
  .titulo-categoria {
    font-size: 1.8rem;
  }
}

.rooms-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 30px;
  width: 100%;
}

@media (min-width: 768px) {
  .rooms-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .rooms-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.empty-state {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--k-border, #e1d7cc);
  border-radius: 1rem;
  padding: 2rem;
  color: var(--k-muted, #5f6f65);
}

.empty-state--warning {
  color: var(--k-forest);
}
</style>
