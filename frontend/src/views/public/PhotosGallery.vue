<template>
  <main class="galeria-page">

    <!-- Hero -->
    <section class="galeria-hero text-center text-white">
      <div class="container">
        <h1 class="titulo-galeria">Fragmentos de la Selva</h1>
        <p class="lead">Capturando la magia, el color y la vida de {{ configStore.hotelName }}.</p>
      </div>
      <div class="custom-shape-divider-bottom">
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none">
          <path class="shape-fill" d="M421.9,6.5c22.6-2.5,51.5,0.4,75.5,5.3c23.6,4.9,70.9,23.5,100.5,35.7c75.8,32.2,133.7,44.5,192.6,49.7 c23.6,2.1,48.7,3.5,103.4-2.5c54.7-6,106.2-25.6,106.2-25.6V0H0v30.3c0,0,72,32.6,158.4,30.5c39.2-0.7,92.8-6.7,134-22.4 c21.2-8.1,52.2-18.2,79.7-24.2C399.3,7.9,411.6,7.5,421.9,6.5z"></path>
        </svg>
      </div>
    </section>

    <!-- Filtros -->
    <section class="filtros-galeria py-4 text-center">
      <div class="container">
        <div class="d-flex justify-content-center gap-2 flex-wrap">
          <button
            v-for="cat in categorias"
            :key="cat.value"
            class="btn btn-outline-success"
            :class="{ active: filtroActivo === cat.value }"
            @click="cambiarFiltro(cat.value)"
          >
            {{ cat.label }}
          </button>
        </div>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="isLoading" class="text-center py-5">
      <div class="spinner-border text-success" role="status"></div>
      <p class="text-muted mt-3">Cargando galería...</p>
    </div>

    <!-- Sin fotos -->
    <div v-else-if="fotos.length === 0" class="text-center py-5">
      <p class="text-muted">No hay fotos en esta categoría aún.</p>
    </div>

    <!-- Grid Masonry -->
    <section v-else class="grid-fotos pb-5">
      <div class="container">
        <div class="masonry-wrapper">
          <template v-for="foto in fotos">
            
            <div
              v-if="foto && foto.url"
              :key="foto.id"
              class="masonry-item"
              @click="abrirLightbox(foto)"
            >
              <img 
                :src="assetUrl(foto.url)"
                :alt="foto.title || `Momento ${configStore.hotelName}`"
                class="img-fluid rounded-4 shadow-sm" 
                loading="lazy"
                @error="$event.target.style.display='none'"
              />
            </div>

          </template>
        </div>
      </div>
    </section>

    <!-- Lightbox -->
    <teleport to="body">
      <div v-if="lightbox.abierto" class="lightbox-overlay" @click.self="cerrarLightbox">
        <button class="lightbox-close" @click="cerrarLightbox">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <button class="lightbox-nav lightbox-prev" @click="navLightbox(-1)">
          <font-awesome-icon :icon="['fas', 'chevron-left']" />
        </button>
        <div class="lightbox-content">
          <img 
            :src="assetUrl(lightbox.foto.url)"
            :alt="lightbox.foto.title || `Momento ${configStore.hotelName}`"
            class="lightbox-img" 
          />
          </div>
        <button class="lightbox-nav lightbox-next" @click="navLightbox(1)">
          <font-awesome-icon :icon="['fas', 'chevron-right']" />
        </button>
      </div>
    </teleport>

    <!-- CTA -->
    <section class="galeria-cta py-5 bg-light text-center">
      <div class="container">
        <h3>¿Quieres vivirlo en persona?</h3>
        <button class="btn btn-success btn-lg rounded-pill mt-3" @click="$router.push({ name: 'hospedaje-home' })">
          Planea tu visita
        </button>
      </div>
    </section>

  </main>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from "vue";
import { listGallery } from "@/api/content";
import { assetUrl } from "@/config/env";
import { useConfigStore } from "@/stores/config";

const configStore = useConfigStore();

const fotos = ref([]);
const isLoading = ref(false);
const filtroActivo = ref("todos");

const categorias = [
  { value: "todos",         label: "Todos" },
  { value: "naturaleza",    label: "Naturaleza" },
  { value: "experiencias",  label: "Experiencias" },
  { value: "instalaciones", label: "Instalaciones" },
  { value: "eventos",       label: "Eventos" },
];

const lightbox = reactive({ abierto: false, foto: null, index: 0 });

const cargarFotos = async (categoria = "todos") => {
  isLoading.value = true;
  try {
    fotos.value = await listGallery(categoria === "todos" ? null : categoria);
  } catch {
    fotos.value = [];
  } finally {
    isLoading.value = false;
  }
};

const cambiarFiltro = (cat) => {
  filtroActivo.value = cat;
  cargarFotos(cat);
};

const abrirLightbox = (foto) => {
  lightbox.index = fotos.value.findIndex(f => f.id === foto.id);
  lightbox.foto = foto;
  lightbox.abierto = true;
  document.body.style.overflow = "hidden";
};

const cerrarLightbox = () => {
  lightbox.abierto = false;
  lightbox.foto = null;
  document.body.style.overflow = "";
};

const navLightbox = (dir) => {
  const total = fotos.value.length;
  lightbox.index = (lightbox.index + dir + total) % total;
  lightbox.foto = fotos.value[lightbox.index];
};

const onKeydown = (e) => {
  if (!lightbox.abierto) return;
  if (e.key === "Escape") cerrarLightbox();
  if (e.key === "ArrowRight") navLightbox(1);
  if (e.key === "ArrowLeft") navLightbox(-1);
};

onMounted(() => {
  cargarFotos();
  window.addEventListener("keydown", onKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
  document.body.style.overflow = "";
});
</script>

<style scoped>
.galeria-hero {
  background: linear-gradient(rgba(15, 59, 42, 0.8), rgba(15, 59, 42, 0.8)),
    url("@/img/fondo3.png") center/cover;
  padding: 120px 0 80px;
  position: relative;
}

.titulo-galeria {
  font-family: "Handlee", cursive;
  font-size: 3.5rem;
}

.masonry-wrapper {
  column-count: 3;
  column-gap: 20px;
}

.masonry-item {
  position: relative;
  display: inline-block;
  width: 100%;
  margin-bottom: 20px;
  overflow: hidden;
  border-radius: 20px;
  cursor: pointer;
}

.masonry-item img {
  transition: transform 0.5s ease;
  width: 100%;
  display: block;
}

.masonry-item:hover img { transform: scale(1.1); }

.overlay-info {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(15, 59, 42, 0.9));
  color: white;
  padding: 20px;
  opacity: 0;
  transition: opacity 0.3s ease;
  font-weight: 500;
}

.masonry-item:hover .overlay-info { opacity: 1; }

.custom-shape-divider-bottom {
  position: absolute;
  bottom: 0; left: 0;
  width: 100%;
  line-height: 0;
  transform: rotate(180deg);
}

.custom-shape-divider-bottom svg {
  display: block;
  width: calc(100% + 1.3px);
  height: 40px;
}

.shape-fill { fill: #fffdfc; }

/* Lightbox */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.93);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-content {
  max-width: 90vw;
  max-height: 90vh;
  text-align: center;
}

.lightbox-img {
  max-width: 100%;
  max-height: 80vh;
  border-radius: 12px;
  object-fit: contain;
}

.lightbox-titulo {
  color: #e0eee0;
  margin-top: 12px;
  font-size: 1rem;
  font-weight: 500;
}

.lightbox-close {
  position: fixed;
  top: 20px; right: 24px;
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  font-size: 1.4rem;
  width: 44px; height: 44px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
  z-index: 2001;
}

.lightbox-close:hover { background: rgba(255,255,255,0.25); }

.lightbox-nav {
  position: fixed;
  top: 50%; transform: translateY(-50%);
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  font-size: 1.2rem;
  width: 48px; height: 48px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
  z-index: 2001;
}

.lightbox-prev { left: 16px; }
.lightbox-next { right: 16px; }
.lightbox-nav:hover { background: rgba(255,255,255,0.25); }

@media (max-width: 992px) { .masonry-wrapper { column-count: 2; } }
@media (max-width: 576px) {
  .masonry-wrapper { column-count: 1; }
  .titulo-galeria { font-size: 2.5rem; }
}
</style>