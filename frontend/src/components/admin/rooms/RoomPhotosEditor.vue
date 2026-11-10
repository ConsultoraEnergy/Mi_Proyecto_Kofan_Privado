<script setup>
/** Fotos ya guardadas de una habitación: elegir la principal o borrar una. */
import { fallbackToFullImage, thumbUrl } from "@/config/env";

defineProps({
  images: { type: Array, required: true },
  mainImage: { type: String, default: null },
});

defineEmits(["set-main", "remove"]);
</script>

<template>
  <div>
    <label class="form-label fw-bold mb-1">Fotos Actuales de la Habitación</label>
    <p class="text-muted small mb-3">
      Haz clic en la <font-awesome-icon icon="fa-solid fa-star" class="tone-sand" /> para elegir la foto
      principal (se guarda con "Guardar cambios").
    </p>

    <div class="row g-2">
      <div v-for="url in images" :key="url" class="col-4 col-md-3">
        <div
          class="card h-100 p-1 position-relative border photo-card"
          :class="{ 'border-success border-2 shadow principal-highlight': url === mainImage }"
        >
          <span
            v-if="url === mainImage"
            class="position-absolute principal-badge rounded-pill bg-success text-white shadow-sm px-2"
          >
            Principal
          </span>

          <img
            :src="thumbUrl(url)"
            class="rounded object-fit-cover w-100"
            style="height: 90px"
            alt=""
            @error="fallbackToFullImage($event, url)"
          />

          <button
            type="button"
            class="btn btn-danger btn-sm position-absolute rounded-circle photo-btn shadow"
            style="right: 5px"
            title="Eliminar foto"
            @click.stop="$emit('remove', url)"
          >
            <font-awesome-icon icon="fa-solid fa-trash" class="image-action-icon" />
          </button>

          <button
            v-if="url !== mainImage"
            type="button"
            class="btn btn-light btn-sm position-absolute rounded-circle photo-btn shadow"
            style="left: 5px"
            title="Hacer foto principal"
            @click.stop="$emit('set-main', url)"
          >
            <font-awesome-icon icon="fa-solid fa-star" class="image-action-icon tone-sand" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tone-sand {
  color: var(--k-sand);
}

.photo-card {
  overflow: hidden;
}

.principal-highlight {
  background-color: rgba(139, 207, 91, 0.12);
}

.principal-badge {
  top: -5px;
  left: -5px;
  font-size: 0.75rem;
  z-index: 2;
}

.photo-btn {
  width: 28px;
  height: 28px;
  bottom: 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.image-action-icon {
  font-size: 0.8rem;
}
</style>
