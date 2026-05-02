<script setup>
import { ref, computed } from 'vue';
import { useReservaStore } from "@/stores/reserva";

const props = defineProps({
  habitacion: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['reservar']);
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Estado para el hover y el modal
const isHovered = ref(false);
const mostrarDetalles = ref(false); 
const indiceFotoActiva = ref(0);

// --- LÓGICA DE IMÁGENES ---
const imagenes = computed(() => {
  if (props.habitacion.images && props.habitacion.images.length > 0) {
    return props.habitacion.images.slice(0, 5).map(img => `${API_BASE_URL}${img}`);
  }
  if (props.habitacion.main_image) {
    return [`${API_BASE_URL}${props.habitacion.main_image}`];
  }
  return ['https://via.placeholder.com/800x500?text=Kofan+Hospedaje'];
});

const fotoPrincipal = computed(() => imagenes.value[indiceFotoActiva.value]);

const siguienteFoto = () => {
  if (imagenes.value.length > 1) {
    indiceFotoActiva.value = (indiceFotoActiva.value + 1) % imagenes.value.length;
  }
};

const anteriorFoto = () => {
  if (imagenes.value.length > 1) {
    indiceFotoActiva.value = (indiceFotoActiva.value - 1 + imagenes.value.length) % imagenes.value.length;
  }
};

// --- DATOS Y FORMATEO ---
const mapaIconos = {
  "Aire Acondicionado": ["fas", "snowflake"],
  "Ventilador": ["fas", "fan"],
  "Televisión": ["fas", "tv"],
  "Wifi": ["fas", "wifi"],
  "Baño Privado": ["fas", "droplet"],
  "Nevera / Minibar": ["fas", "martini-glass"],
  "Zonas Verdes": ["fas", "tree"],
  "Vista a la Selva": ["fas", "binoculars"],
  "Malla Catamarán": ["fas", "table-cells-large"],
  "Tina / Jacuzzi": ["fas", "hot-tub-person"],
  "Balcón": ["fas", "door-open"]
};

const amenidadesSeguras = computed(() => props.habitacion.amenities || []);

const formatPrice = (v) => {
  return (v || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
};

// --- ACCIONES ---
const handleReservar = () => { 
  cerrarDetalles(); // 🟢 ¡Esto cierra el modal visualmente Y devuelve el scroll!
  
  resStore.habitacionSeleccionada = props.habitacion; 
  resStore.isModalOpen = true; 
};

const abrirDetalles = () => { 
  mostrarDetalles.value = true; 
  document.body.style.overflow = 'hidden'; 
};

const cerrarDetalles = () => { 
  mostrarDetalles.value = false; 
  document.body.style.overflow = 'auto'; 
};
const resStore = useReservaStore();
// Agrega esto al final de tu <script setup> en RoomCard.vue
  defineExpose({ 
  abrirDetalles, 
  habitacion: props.habitacion 
});
</script>

<template>
  <div>
    <div 
      class="minimalist-item h-100 d-flex flex-column"
      @mouseenter="isHovered = true" 
      @mouseleave="isHovered = false"
    >
      <div class="image-square position-relative bg-dark shadow-sm">
        <img :src="imagenes[0]" class="w-100 h-100 foto-cover" :alt="habitacion.name">
        
        <div class="hover-overlay position-absolute top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center" :class="{ 'show-overlay': isHovered }">
          <button @click="abrirDetalles" class="btn btn-light rounded-0 px-4 py-2 fw-bold shadow-sm btn-explorar">
            <font-awesome-icon :icon="['fas', 'eye']" class="me-2 text-success" /> Ver Detalles
          </button>
        </div>
      </div>

      <div class="info-block mt-3 d-flex flex-column flex-grow-1">
        <h3 class="titulo-minimalista fw-bold mb-3 text-truncate">{{ habitacion.name }}</h3>
        
        <div class="mt-auto d-flex justify-content-between align-items-end">
          <div>
            <span class="precio-destacado fw-bold">{{ formatPrice(habitacion.price) }}</span>
            <span class="text-muted small"> /noche</span>
          </div>
          <button @click="handleReservar" class="btn btn-link p-0 btn-reservar-link text-decoration-none fw-bold">
            Reservar <font-awesome-icon :icon="['fas', 'arrow-right']" class="ms-1 small" />
          </button>
        </div>
      </div>
    </div>

    <div v-if="mostrarDetalles" class="modal-overlay d-flex justify-content-center align-items-center" @click.self="cerrarDetalles">
      <div class="modal-kofan bg-white rounded-0 overflow-hidden shadow-lg d-flex flex-column flex-lg-row position-relative">
        
        <button class="btn-close-modal position-absolute top-0 end-0 m-3 z-3 bg-white rounded-circle shadow-sm" @click="cerrarDetalles">
          <font-awesome-icon :icon="['fas', 'xmark']" class="fs-5 text-dark" />
        </button>

        <div class="modal-gallery col-12 col-lg-6 position-relative bg-dark">
          <img :src="fotoPrincipal" class="w-100 h-100 foto-cover" :alt="habitacion.name">
          
          <button v-if="imagenes.length > 1" @click="anteriorFoto" class="btn-nav-modal position-absolute top-50 start-0 translate-middle-y ms-3">
            <font-awesome-icon :icon="['fas', 'chevron-left']" class="fs-3 text-white drop-shadow" />
          </button>
          <button v-if="imagenes.length > 1" @click="siguienteFoto" class="btn-nav-modal position-absolute top-50 end-0 translate-middle-y me-3">
            <font-awesome-icon :icon="['fas', 'chevron-right']" class="fs-3 text-white drop-shadow" />
          </button>
        </div>

        <div class="modal-info col-12 col-lg-6 p-4 p-lg-5 d-flex flex-column overflow-y-auto">
          <h2 class="titulo-modal fw-bold mb-3">{{ habitacion.name }}</h2>
          
          <div class="d-flex flex-wrap gap-3 mb-4 text-muted small">
            <span class="badge bg-success bg-opacity-10 text-success px-3 py-2 rounded-0">
              <font-awesome-icon :icon="['fas', 'user-group']" class="me-1" /> Hasta {{ habitacion.capacity }} personas
            </span>
            <span v-if="habitacion.num_cuartos" class="d-flex align-items-center">
              <font-awesome-icon :icon="['fas', 'door-open']" class="me-1" /> {{ habitacion.num_cuartos }} Hab.
            </span>
            <span v-if="habitacion.tipo_camas" class="d-flex align-items-center">
              <font-awesome-icon :icon="['fas', 'moon']" class="me-1" /> {{ habitacion.tipo_camas }}
            </span>
          </div>

          <p class="descripcion-modal text-muted mb-4">{{ habitacion.description }}</p>

          <h5 class="fw-bold mb-3">Servicios incluidos</h5>
          <div class="row row-cols-2 g-3 mb-4 flex-grow-1">
            <template v-if="amenidadesSeguras.length > 0">
              <div v-for="(amenidad, index) in amenidadesSeguras" :key="index" class="col d-flex align-items-center text-muted small">
                <font-awesome-icon :icon="mapaIconos[amenidad] || ['fas', 'check']" class="text-success me-2 fs-6" />
                {{ amenidad }}
              </div>
            </template>
            <template v-else>
              <div class="col-12 text-muted fst-italic small">Detalles básicos incluidos. Consulta en recepción.</div>
            </template>
          </div>

          <div class="mt-auto pt-4 border-top d-flex justify-content-between align-items-center">
            <div>
              <p class="mb-0 text-muted small text-uppercase" style="letter-spacing: 1px;">Precio por noche</p>
              <span class="fs-3 fw-bold text-success-kofan">{{ formatPrice(habitacion.price) }}</span>
            </div>
            <button @click="handleReservar" class="btn btn-reservar-modal px-4 py-2 rounded-0 shadow-sm fw-bold">
              Reservar ahora <font-awesome-icon :icon="['fas', 'arrow-right']" class="ms-2" />
            </button>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<style scoped>
/* ================================
   ESTILOS ITEM MINIMALISTA (Libre de marco)
================================ */
.minimalist-item {
  transition: transform 0.3s ease;
}
.minimalist-item:hover {
  transform: translateY(-4px); 
}

.image-square {
  aspect-ratio: 4/3; /* ESTO HACE QUE EL CONTENEDOR SEA UN CUADRADO PERFECTO */
  overflow: hidden;
  border-radius: 0 !important; /* BORDES TOTALMENTE RECTOS */
}
.foto-cover {
  object-fit: cover;
}

.info-block {
  background: transparent; 
  padding: 0 4px; 
}

.hover-overlay {
  background: rgba(15, 59, 42, 0.4); 
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none; 
}
.show-overlay {
  opacity: 1;
  pointer-events: auto;
}

.btn-explorar {
  transform: translateY(15px);
  transition: transform 0.3s ease, background-color 0.2s;
  color: #0f3b2a;
  border-radius: 0 !important; 
}
.show-overlay .btn-explorar {
  transform: translateY(0);
}
.btn-explorar:hover {
  background-color: #f8f9fa;
}

.titulo-minimalista {
  font-size: 1.2rem;
  color: #0f3b2a;
  text-transform: uppercase; 
  font-weight: 600;
  letter-spacing: 0.5px;
}

.precio-destacado {
  color: #0f3b2a;
  font-size: 1.15rem;
}

.btn-reservar-link {
  color: #114232;
  transition: color 0.2s ease, transform 0.2s ease;
}
.btn-reservar-link:hover {
  color: #1a5c46;
  transform: translateX(3px); 
}

/* ================================
   ESTILOS DEL MODAL DE DETALLES
================================ */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(3px);
  z-index: 9999;
  padding: 20px;
}

.modal-kofan {
  width: 100%;
  max-width: 1000px;
  max-height: 90vh;
  animation: modalFadeIn 0.3s ease-out forwards;
}

.modal-gallery {
  min-height: 300px;
}

.modal-info {
  background-color: #fafaf9; 
  max-height: 90vh;
}

.titulo-modal {
  color: #0f3b2a;
  font-family: 'Handlee', cursive;
  font-size: 2rem;
}

.descripcion-modal {
  line-height: 1.6;
  font-size: 1rem;
}

.text-success-kofan {
  color: #114232;
}

.btn-reservar-modal {
  background-color: #114232;
  color: white;
  border: none;
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.btn-reservar-modal:hover {
  background-color: #1a5c46;
  transform: translateY(-2px);
}

.btn-nav-modal {
  border: none;
  background: transparent;
  padding: 10px;
  transition: transform 0.2s;
}
.btn-nav-modal:hover {
  transform: scale(1.2);
}
.drop-shadow {
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8));
}

.btn-close-modal {
  border: none;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}
.btn-close-modal:hover {
  transform: rotate(90deg) scale(1.1);
  background-color: #f8d7da !important;
  color: #dc3545 !important;
}

@keyframes modalFadeIn {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@media (max-width: 991px) {
  .modal-kofan { flex-direction: column; max-height: 95vh; }
  .modal-gallery { height: 250px; min-height: 250px; flex-shrink: 0; }
  .modal-info { flex-grow: 1; overflow-y: auto; }
}
</style>