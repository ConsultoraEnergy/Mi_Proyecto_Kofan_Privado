<script setup>
import { ref, computed, onMounted } from "vue";
import { useReservaStore } from "@/stores/reserva";
import { useConfigStore } from '@/stores/config';
import apiClient from "@/api/apiClient";
import { getRooms } from "@/services/roomService";
import RoomCard from "@/components/RoomCard.vue";
import SearchAvailability from '@/components/SearchAvailability.vue';
import { useRouter } from 'vue-router';

const router = useRouter();
// Stores
const resStore = useReservaStore();
const configStore = useConfigStore();

// Estados
const fotosPreview = ref([]);
const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Estados del Catálogo
const allAccommodations = ref([]);
const loadingRooms = ref(false);
const errorRooms = ref("");


// 1. Agrega esta variable arriba junto a tus otras variables ref()
const tarjetasRef = ref([]);

// 2. Reemplaza tu procesarBusqueda
const procesarBusqueda = (datos) => {
  try {
    // A. Guardamos las fechas (YA DESCOMENTADAS Y CORREGIDAS)
    if (datos.fechas && datos.fechas.start && datos.fechas.end) {
      resStore.selectedDateRange = {
        start: new Date(datos.fechas.start),
        end: new Date(datos.fechas.end)
      };
    }

    // B. Buscamos cuál es la tarjeta que encontró el backend
    // Usamos el nombre para que no haya problemas de _id de MongoDB
    const tarjetaEncontrada = tarjetasRef.value.find(
      (tarjeta) => tarjeta.habitacion?.name === datos.habitacion.name
    );

    // C. Si la encontramos, ¡abrimos su Modal Hermoso a control remoto!
    if (tarjetaEncontrada) {
      tarjetaEncontrada.abrirDetalles();
      
      // Opcional: Hacemos un scroll suave hacia abajo para que el usuario la vea
      window.scrollTo({ top: 500, behavior: 'smooth' });
    } else {
      console.error("No se encontró la tarjeta en la pantalla");
    }

  } catch (error) {
    console.error("Error al abrir los detalles:", error);
  }
};

// --- LÓGICA DE GALERÍA ---
const cargarGaleria = async () => {
  try {
    const { data } = await apiClient.get("/gallery/");
    fotosPreview.value = data.slice(0, 6);
  } catch {
    fotosPreview.value = [];
  }
};

// --- LÓGICA DE CATÁLOGO ---
const obtenerListaHabitaciones = (response) => {
  if (Array.isArray(response?.data)) return response.data;
  if (Array.isArray(response)) return response;
  return [];
};

const obtenerEstadoActivo = (habitacion) => {
  const valor = habitacion?.active;
  if (valor === undefined || valor === null) return true;
  if (typeof valor === "string") return valor.toLowerCase() !== "false";
  return valor !== false;
};

const normalizarTipoAlojamiento = (type = "") => {
  const tipo = String(type).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
  if (!tipo) return "individual";
  if (["cabana", "cabanas", "cabin", "cabins"].includes(tipo) || tipo.includes("cab")) return "cabana";
  if (["family", "familiar", "familiares"].includes(tipo) || tipo.includes("fam")) return "familiar";
  return "individual";
};

const cargarCatalogo = async () => {
  loadingRooms.value = true;
  errorRooms.value = "";
  try {
    const response = await getRooms();
    allAccommodations.value = obtenerListaHabitaciones(response);
  } catch (error) {
    console.error("Error al cargar los alojamientos:", error);
    errorRooms.value = "No fue posible cargar las habitaciones en este momento.";
    allAccommodations.value = [];
  } finally {
    loadingRooms.value = false;
  }
};

// --- COMPUTADOS PARA CATÁLOGO ---
const alojamientosActivos = computed(() =>
  allAccommodations.value.filter((acomodacion) => obtenerEstadoActivo(acomodacion))
);

const filtrarPorTipo = (tipoEsperado) =>
  alojamientosActivos.value.filter(
    (acomodacion) => normalizarTipoAlojamiento(acomodacion?.type) === tipoEsperado
  );

const cabanasIndependientes = computed(() => filtrarPorTipo("cabana"));
const habitacionesFamiliares = computed(() => filtrarPorTipo("familiar"));
const habitacionesIndividuales = computed(() => filtrarPorTipo("individual"));

const hayResultados = computed(
  () =>
    cabanasIndependientes.value.length +
    habitacionesFamiliares.value.length +
    habitacionesIndividuales.value.length > 0
);

onMounted(() => {
  cargarGaleria();
  cargarCatalogo();
});
</script>

<template>
  <main>
    <section id="hero-kofan" class="position-relative">
      <div class="hero-overlay"></div>
      
      <!-- CONTENEDOR DEL BUSCADOR FLOTANTE EN EL CENTRO -->
      <!-- 'top-50 start-50 translate-middle' lo centra perfectamente -->
      <div class="position-absolute start-50 translate-middle w-100 px-3 search-wrapper" style="top: 60%;">
        <SearchAvailability @habitacionEncontrada="procesarBusqueda" />
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

      <div v-else-if="!hayResultados" class="container pb-5 text-center">
        <div class="empty-state">Aún no hay alojamientos disponibles para mostrar.</div>
      </div>

      <template v-else>
        <div v-if="cabanasIndependientes.length > 0" class="container mb-5">
          <div class="d-flex align-items-center mb-4">
            <div class="linea-verde"></div>
            <h3 class="mx-3 fw-bold verde-kofan titulo-categoria">Cabañas Independientes</h3>
          </div>
          <div class="rooms-grid">
            <RoomCard
              v-for="c in cabanasIndependientes"
              :key="c.id || c._id"
              :habitacion="c"
              @reservar="resStore.openModal($event)"
              ref="tarjetasRef"
            />
          </div>
        </div>

        <div v-if="habitacionesFamiliares.length > 0" class="container mb-5">
          <div class="d-flex align-items-center mb-4">
            <div class="linea-verde"></div>
            <h3 class="mx-3 fw-bold verde-kofan titulo-categoria">Habitaciones Familiares</h3>
          </div>
          <div class="rooms-grid">
            <RoomCard
              v-for="h in habitacionesFamiliares"
              :key="h.id || h._id"
              :habitacion="h"
              @reservar="resStore.openModal($event)"
              ref="tarjetasRef"
            />
          </div>
        </div>

        <div v-if="habitacionesIndividuales.length > 0" class="container pb-5">
          <div class="d-flex align-items-center mb-4">
            <div class="linea-verde"></div>
            <h3 class="mx-3 fw-bold verde-kofan titulo-categoria">Habitaciones Individuales</h3>
          </div>
          <div class="rooms-grid">
            <RoomCard
              v-for="h in habitacionesIndividuales"
              :key="h.id || h._id"
              :habitacion="h"
              @reservar="resStore.openModal($event)"
              ref="tarjetasRef"
            />
          </div>
        </div>
      </template>
    </section>

    <!-- 3. EXPERIENCIAS -->
    <section class="experiencias" id="experiencias">
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
            <p>Conéctate con las tradiciones y saberes de la comunidad Kofán.</p>
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
          <span class="subtitulo">Momentos Kofán</span>
          <h2 class="titulo-seccion">Un vistazo a nuestro paraíso</h2>
        </div>
        <div class="preview-grid">
          <div v-for="foto in fotosPreview" :key="foto.id" class="preview-item" @click="$router.push({ name: 'gallery' })">
            <img :src="baseUrl + foto.url" :alt="foto.titulo || 'Kofán'" @error="$event.target.style.display='none'" />
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
    <section class="ubicacion" id="donde-estamos">
      <div class="divisor-entrada-verde">
        <svg viewBox="0 0 1200 120" preserveAspectRatio="none"><path d="M0,0V120H1200V0c-150,80-350,120-600,120S150,80,0,0Z" fill="var(--k-forest-soft)"></path></svg>
      </div>
      <div class="container mt-5">
        <div class="text-center mb-5">
          <span class="subtitulo-blanco">¿Cómo llegar?</span>
          <h2 class="titulo-seccion-blanco">Nuestra ubicación en el Putumayo</h2>
          <p class="parrafo-ubicacion">
            Nos encontramos en <strong>{{ configStore.data.address || 'Puerto Asís, Putumayo' }}</strong>.
          </p>
        </div>
        <div class="mapa-wrapper shadow-soft">
          <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3989.431284566359!2d-76.50537872421477!3d0.5055018994892419!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8e2a1dd0b8ccb649%3A0x6b83f3fc3c2cc0db!2sPuerto%20As%C3%ADs%2C%20Putumayo!5e0!3m2!1ses!2sco!4v1710971000000!5m2!1ses!2sco" width="100%" height="450" style="border: 0" loading="lazy"></iframe>
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

button, .btn, .subtitulo, .subtitulo-blanco, h3 {
  font-family: "Handlee", cursive;
}

/* ==========================================
   NUEVO HERO SECTION (Fondo + Buscador)
========================================== */
#hero-kofan {
  position: relative;
  min-height: 104vh; 
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url('@/img/portadaimg.jpg');  
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

.verde-kofan { color: var(--k-forest); }
.linea-verde { height: 4px; width: 50px; background-color: var(--k-apple); border-radius: 2px; }

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
.empty-state--warning { color: var(--k-forest); }


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
.galeria-preview { background: #fff; }

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

.preview-item:hover img { transform: scale(1.08); }

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
  .preview-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
  .preview-grid { grid-template-columns: 1fr; }
}

</style>