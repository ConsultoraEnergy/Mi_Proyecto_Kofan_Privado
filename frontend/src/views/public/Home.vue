<script setup>
import { ref, computed, onMounted } from "vue";
import { useReservaStore } from "@/stores/reserva";
import { useConfigStore } from "@/stores/config";
import { listRooms, listRoomTypes } from "@/api/rooms";
import { listGallery } from "@/api/content";
import { assetUrl } from "@/config/env";
import RoomCard from "@/components/RoomCard.vue";
import SearchAvailability from "@/components/SearchAvailability.vue";

const resStore = useReservaStore();
const configStore = useConfigStore();

// Estados
const fotosPreview = ref([]);
const roomTypes = ref([]);
const allAccommodations = ref([]);
const loadingRooms = ref(false);
const errorRooms = ref("");

// Tarjetas renderizadas (por id de habitación) para abrir sus detalles desde el buscador
const tarjetas = new Map();
const registrarTarjeta = (id, el) => {
  if (el) tarjetas.set(id, el);
  else tarjetas.delete(id);
};

const procesarBusqueda = ({ habitacion, fechas }) => {
  if (fechas?.start && fechas?.end) {
    resStore.selectedDateRange = { start: new Date(fechas.start), end: new Date(fechas.end) };
  }

  const tarjeta = tarjetas.get(habitacion.id);
  if (tarjeta) {
    tarjeta.abrirDetalles();
    window.scrollTo({ top: 500, behavior: "smooth" });
  } else {
    // La habitación no está en el catálogo visible: se abre directamente la reserva.
    resStore.openModal(habitacion);
  }
};

// --- GALERÍA ---
const cargarGaleria = async () => {
  try {
    fotosPreview.value = (await listGallery()).slice(0, 6);
  } catch {
    fotosPreview.value = [];
  }
};

// --- CATÁLOGO ---
const cargarCatalogo = async () => {
  loadingRooms.value = true;
  errorRooms.value = "";
  try {
    const [page, types] = await Promise.all([listRooms({ limit: 100 }), listRoomTypes()]);
    allAccommodations.value = page.items;
    roomTypes.value = types;
  } catch (error) {
    console.error("Error al cargar los alojamientos:", error);
    errorRooms.value = "No fue posible cargar las habitaciones en este momento.";
    allAccommodations.value = [];
  } finally {
    loadingRooms.value = false;
  }
};

/** Secciones del catálogo agrupadas por tipo de habitación (orden del catálogo de tipos). */
const secciones = computed(() => {
  const grupos = new Map(roomTypes.value.map((t) => [t.code, { code: t.code, name: t.name, rooms: [] }]));
  const otros = { code: "otros", name: "Otros alojamientos", rooms: [] };
  for (const room of allAccommodations.value) {
    const code = room.room_type?.code;
    if (code && !grupos.has(code)) grupos.set(code, { code, name: room.room_type.name, rooms: [] });
    (code ? grupos.get(code) : otros).rooms.push(room);
  }
  return [...grupos.values(), otros].filter((g) => g.rooms.length > 0);
});

// Ubicación y mapa a partir de la dirección configurada (solo si hay dirección o ciudad).
const tieneUbicacion = computed(() => !!(configStore.data.address || configStore.data.city));
const ubicacionTexto = computed(() =>
  [configStore.data.address, configStore.data.city, configStore.data.country].filter(Boolean).join(", "),
);
const mapaUrl = computed(
  () => `https://www.google.com/maps?q=${encodeURIComponent(ubicacionTexto.value)}&output=embed`,
);

onMounted(() => {
  cargarGaleria();
  cargarCatalogo();
});
</script>

<template>
  <main>
    <section id="hero-brand" class="position-relative">
      <h1 class="visually-hidden">{{ configStore.hotelName }}</h1>
      <div class="hero-overlay"></div>

      <!-- CONTENEDOR DEL BUSCADOR FLOTANTE EN EL CENTRO -->
      <!-- 'top-50 start-50 translate-middle' lo centra perfectamente -->
      <div class="position-absolute start-50 translate-middle w-100 px-3 search-wrapper" style="top: 60%">
        <SearchAvailability @habitacion-encontrada="procesarBusqueda" />
      </div>
    </section>

    <!-- 2. CATÁLOGO DE HABITACIONES -->
    <!-- Quitamos mt-5 ya que el buscador ahora está en el centro del hero y no choca con esta sección -->
    <section id="catalogo" class="catalogo-section py-5">
      <div v-if="loadingRooms" class="container pb-5 text-center">
        <div class="empty-state">Cargando alojamientos disponibles...</div>
      </div>

      <div v-else-if="errorRooms" class="container pb-5 text-center">
        <div class="empty-state empty-state--warning">
          <p class="mb-3">{{ errorRooms }}</p>
          <button class="btn btn-primary px-4" @click="cargarCatalogo">Reintentar</button>
        </div>
      </div>

      <div v-else-if="secciones.length === 0" class="container pb-5 text-center">
        <div class="empty-state">Aún no hay alojamientos disponibles para mostrar.</div>
      </div>

      <template v-else>
        <div
          v-for="(seccion, idx) in secciones"
          :key="seccion.code"
          class="container"
          :class="idx === secciones.length - 1 ? 'pb-5' : 'mb-5'"
        >
          <div class="d-flex align-items-center mb-4">
            <div class="linea-verde"></div>
            <h3 class="mx-3 fw-bold verde-brand titulo-categoria">{{ seccion.name }}</h3>
          </div>
          <div class="rooms-grid">
            <RoomCard
              v-for="room in seccion.rooms"
              :key="room.id"
              :ref="(el) => registrarTarjeta(room.id, el)"
              :habitacion="room"
            />
          </div>
        </div>
      </template>
    </section>

    <!-- 3. EXPERIENCIAS -->
    <section id="experiencias" class="experiencias">
      <div class="container">
        <div class="text-center mb-5">
          <span class="subtitulo">Vive lo Auténtico</span>
          <h2 class="titulo-seccion">Descubre la magia en cada detalle</h2>
        </div>
        <div class="grid-actividades">
          <div class="card-actividad">
            <div class="icono-wrapper"><font-awesome-icon icon="fa-solid fa-leaf" /></div>
            <h3>Senderismo</h3>
            <p>Camina por senderos sagrados y descubre la biodiversidad amazónica.</p>
          </div>
          <div class="card-actividad">
            <div class="icono-wrapper"><font-awesome-icon icon="fa-solid fa-hands-holding" /></div>
            <h3>Cultura Viva</h3>
            <p>Conéctate con las tradiciones y saberes de la región.</p>
          </div>
          <div class="card-actividad">
            <div class="icono-wrapper"><font-awesome-icon icon="fa-solid fa-moon" /></div>
            <h3>Descanso Pleno</h3>
            <p>Habitaciones diseñadas para el bienestar físico y espiritual.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. GALERÍA PREVIEW -->
    <section v-if="fotosPreview.length > 0" class="galeria-preview py-5">
      <div class="container">
        <div class="text-center mb-4">
          <span class="subtitulo">Momentos {{ configStore.hotelName }}</span>
          <h2 class="titulo-seccion">Un vistazo a nuestro paraíso</h2>
        </div>
        <div class="preview-grid">
          <div
            v-for="foto in fotosPreview"
            :key="foto.id"
            class="preview-item"
            @click="$router.push({ name: 'gallery' })"
          >
            <img
              :src="assetUrl(foto.url)"
              :alt="foto.title || configStore.hotelName"
              loading="lazy"
              @error="$event.target.style.display = 'none'"
            />
          </div>
          <div class="preview-item preview-item-cta" @click="$router.push({ name: 'gallery' })">
            <div class="cta-content">
              <font-awesome-icon :icon="['fas', 'images']" class="fs-2 mb-2" />
              <p class="fw-bold mb-0">Ver galería completa</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 5. UBICACIÓN -->
    <section v-if="tieneUbicacion" id="donde-estamos" class="ubicacion">
      <div class="divisor-entrada-verde">
        <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
          <path d="M0,0V120H1200V0c-150,80-350,120-600,120S150,80,0,0Z" fill="var(--k-forest-soft)"></path>
        </svg>
      </div>
      <div class="container mt-5">
        <div class="text-center mb-5">
          <span class="subtitulo-blanco">¿Cómo llegar?</span>
          <h2 class="titulo-seccion-blanco">
            Nuestra ubicación<template v-if="configStore.data.city"> en {{ configStore.data.city }}</template>
          </h2>
          <p class="parrafo-ubicacion">
            Nos encontramos en <strong>{{ ubicacionTexto }}</strong
            >.
          </p>
        </div>
        <div class="mapa-wrapper shadow-soft">
          <iframe
            :src="mapaUrl"
            :title="`Mapa de ${configStore.hotelName}`"
            width="100%"
            height="450"
            style="border: 0"
            loading="lazy"
          ></iframe>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
/* --- GLOBALES COMPONENTE HOME --- */
main {
  background: var(--k-cream);
  color: var(--k-forest-soft);
  font-family: "Forum", serif;
}

button,
.btn,
.subtitulo,
.subtitulo-blanco,
h3 {
  font-family: "Handlee", cursive;
}

/* ==========================================
   NUEVO HERO SECTION (Fondo + Buscador)
========================================== */
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
  margin-top: -80px; /* Sube la imagen debajo del Navbar si tu navbar es transparente */
  padding-top: 80px;
}

.hero-overlay {
  position: absolute;
  top: 9%; /* Margen superior */
  left: 3%; /* Margen izquierdo */
  right: 3%; /* Margen derecho */
  bottom: 20%; /* Margen inferior */
  /* Eliminamos width: 100% y height: 100% para que los márgenes definan el tamaño */
  background: linear-gradient(to bottom, rgba(15, 59, 42, 0.7) 0%, rgba(15, 59, 42, 0.4) 100%);
  z-index: 0;
  /* Opcional: añade bordes redondeados para un aspecto más moderno, como en el ejemplo */
  border-radius: 20px;
}

.hero-title {
  font-size: 4rem;
  font-family: "Forum", serif;
  color: #ffffff;
  text-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  line-height: 1.1;
}

.hero-subtitle {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  max-width: 700px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

/* ==========================================
   ESTILOS DEL BUSCADOR UNIVERSAL
========================================== */
.booking-widget-container {
  max-width: 900px;
  width: 100%;
  margin-top: 40px;
}

.booking-widget {
  border-radius: 50px;
}

.input-group-custom {
  flex: 1;
  min-width: 150px;
}

.uppercase-label {
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.75rem;
  color: #6c757d !important;
}

.form-control-plaintext {
  outline: none;
  color: #0f3b2a;
  cursor: pointer;
}
.form-control-plaintext:focus {
  outline: none;
}

.btn-buscar-hero {
  background-color: #114232;
  color: white;
  border-radius: 40px;
  padding: 15px 40px;
  font-size: 1.1rem;
  transition: all 0.3s ease;
}
.btn-buscar-hero:hover {
  background-color: #1a5c46;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(17, 66, 50, 0.4);
}

@media (min-width: 768px) {
  .border-end-md {
    border-right: 1px solid #e9ecef;
  }
}

@media (max-width: 767px) {
  .hero-title {
    font-size: 2.5rem;
  }
  .booking-widget {
    border-radius: 20px;
    padding: 15px !important;
  }
  .input-group-custom {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e9ecef;
    margin-bottom: 10px;
    padding-bottom: 10px;
  }
  .input-group-custom:last-of-type {
    border-bottom: none;
  }
}

.search-wrapper {
  max-width: 1150px; /* Evita que el buscador se estire demasiado en pantallas gigantes */
  z-index: 20; /* Asegura que el calendario y sus popovers queden por encima de todo */
}

/* --- CATÁLOGO INTEGRADO (GRID DE 3) --- */
.catalogo-section {
  background-color: var(--k-cream);
}

.verde-brand {
  color: var(--k-forest);
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

/* --- EXPERIENCIAS --- */
.experiencias {
  padding: 80px 20px 120px 20px;
  background: #fffdfc;
}

.titulo-seccion {
  font-family: "Handlee", cursive;
  font-size: 2.8rem;
  color: var(--k-forest);
  margin: 15px 0;
}

.subtitulo {
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--k-forest-soft);
  font-weight: 700;
}

.grid-actividades {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  max-width: 1100px;
  margin: 0 auto;
}

.card-actividad {
  text-align: center;
  padding: 30px;
}

.icono-wrapper {
  width: 80px;
  height: 80px;
  background-color: var(--k-apple-soft);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: var(--k-forest-soft);
  font-size: 2rem;
}

/* --- GALERÍA PREVIEW --- */
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
}

.cta-content {
  color: var(--k-apple-soft);
  text-align: center;
}

/* --- UBICACIÓN --- */
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
