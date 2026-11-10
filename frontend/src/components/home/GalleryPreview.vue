<script setup>
/** Muestra las primeras fotos de la galería; no se renderiza si la galería está vacía. */
import { onMounted, ref } from "vue";
import { listGallery } from "@/api/content";
import { fallbackToFullImage, thumbUrl } from "@/config/env";
import { useConfigStore } from "@/stores/config";
import SectionHeading from "@/components/home/SectionHeading.vue";

const props = defineProps({
  limit: { type: Number, default: 6 },
});

const configStore = useConfigStore();
const photos = ref([]);

onMounted(async () => {
  try {
    photos.value = (await listGallery()).slice(0, props.limit);
  } catch {
    photos.value = [];
  }
});
</script>

<template>
  <section v-if="photos.length > 0" class="galeria-preview py-5">
    <div class="container">
      <SectionHeading
        class="mb-4"
        :eyebrow="`Momentos ${configStore.hotelName}`"
        title="Un vistazo a nuestro paraíso"
      />
      <div class="preview-grid">
        <RouterLink v-for="photo in photos" :key="photo.id" :to="{ name: 'gallery' }" class="preview-item">
          <img
            :src="thumbUrl(photo.url)"
            :alt="photo.title || configStore.hotelName"
            loading="lazy"
            @error="fallbackToFullImage($event, photo.url) || ($event.target.style.display = 'none')"
          />
        </RouterLink>
        <RouterLink :to="{ name: 'gallery' }" class="preview-item preview-item-cta">
          <div class="cta-content">
            <font-awesome-icon :icon="['fas', 'images']" class="fs-2 mb-2" />
            <p class="fw-bold mb-0">Ver galería completa</p>
          </div>
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.galeria-preview {
  background: #fff;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-width: 1000px;
  margin: 0 auto;
}

.preview-item {
  display: block;
  border-radius: 16px;
  overflow: hidden;
  aspect-ratio: 4/3;
  cursor: pointer;
  background: #f0f0f0;
}

.preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.preview-item:hover img {
  transform: scale(1.08);
}

.preview-item-cta {
  background: var(--k-forest);
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.cta-content {
  color: var(--k-apple-soft);
  text-align: center;
}

@media (max-width: 768px) {
  .preview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .preview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
