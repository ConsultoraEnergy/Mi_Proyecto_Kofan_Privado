<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { DatePicker as VDatePicker } from 'v-calendar';
import 'v-calendar/style.css';
import { searchAvailableRoom } from "@/services/roomService";
import Swal from 'sweetalert2';

const emit = defineEmits(['habitacionEncontrada']);

// 🟢 1. Actualizar Categorías EXACTAS de la base de datos
const categorias = ['Cabañas Independientes', 'Habitaciones Familiares', 'Habitaciones Individuales'];
const tipoSeleccionado = ref(categorias[0]);

const range = ref({
  start: null,
  end: null,
});

const buscando = ref(false);
const minDate = ref(new Date());

// Nuevo: Huéspedes
const totalHuespedes = ref(2); // Valor por defecto

// 🟢 NUEVO: Lógica responsiva manual (Reemplaza a $screens)
const columnasCalendario = ref(window.innerWidth >= 768 ? 2 : 1);

const actualizarColumnas = () => {
  columnasCalendario.value = window.innerWidth >= 768 ? 2 : 1;
};

onMounted(() => window.addEventListener('resize', actualizarColumnas));
onUnmounted(() => window.removeEventListener('resize', actualizarColumnas));
// ---------------------------------------------------------

const formatearFecha = (date) => {
  if (!date) return '';
  const d = new Date(date);
  // Ajuste seguro de zona horaria para enviar YYYY-MM-DD
  return new Date(d.getTime() - (d.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
};

// Nuevo: Formateo de rango de fechas para mostrar (como en la imagen: "29 Abr-30 Abr")
const fechaRangoAMostrar = computed(() => {
  if (!range.value || !range.value.start || !range.value.end) {
    return 'Agregar fechas';
  }
  const opciones = { day: 'numeric', month: 'short' };
  const inicio = range.value.start.toLocaleDateString('es-ES', opciones);
  const fin = range.value.end.toLocaleDateString('es-ES', opciones);
  // Reemplazar el punto en el nombre del mes si existe (ej: Abr.)
  return `${inicio}-${fin}`.replace(/\./g, '');
});

// 🟢 Creamos un "traductor" para que la Base de Datos entienda la categoría
const mapeoCategoriasBD = {
  'Cabañas Independientes': 'Cabins',
  'Habitaciones Familiares': 'Family',
  'Habitaciones Individuales': 'Individual'
};

const buscar = async () => {
  if (!range.value || !range.value.start || !range.value.end) {
    Swal.fire({
      title: 'Selecciona tus fechas',
      text: 'Por favor indica cuándo llegas y cuándo te vas.',
      icon: 'warning',
      confirmButtonColor: '#0f3b2a'
    });
    return;
  }

  buscando.value = true;

  try {
    const entrada = formatearFecha(range.value.start);
    const salida = formatearFecha(range.value.end);

    // 🟢 Usamos el traductor: Si selecciona "Cabañas Independientes", esto guarda "Cabaña"
    const tipoParaBackend = mapeoCategoriasBD[tipoSeleccionado.value] || tipoSeleccionado.value;

    // Llamamos al servicio con el nombre traducido
    // 🟢 Le pasamos el totalHuespedes.value como cuarto parámetro
const response = await searchAvailableRoom(tipoParaBackend, entrada, salida, totalHuespedes.value);

    // ¡Éxito!
    emit('habitacionEncontrada', {
      habitacion: response.data,
      fechas: { start: range.value.start, end: range.value.end },
      huespedes: totalHuespedes.value 
    });

  } catch (error) {
    if (error.response && error.response.status === 404) {
      Swal.fire({
        title: '¡Agotado!',
        text: `No nos quedan habitaciones tipo '${tipoSeleccionado.value}' para esas fechas. ¡Intenta con otra categoría u otros días!`,
        icon: 'info',
        confirmButtonColor: '#0f3b2a'
      });
    } else {
      Swal.fire({
        title: 'Error de conexión',
        text: 'Ocurrió un problema al buscar. Inténtalo nuevamente.',
        icon: 'error',
        confirmButtonColor: '#0f3b2a'
      });
    }
  } finally {
    buscando.value = false;
  }
};
</script>

<template>
  <!-- 1. Redujimos el contenedor a py-2 (antes py-3) para quitar espacio blanco superior/inferior -->
  <div class="search-bar-container bg-white py-2 px-3 px-lg-4 mx-auto rounded-0">
    <div class="row g-3 align-items-end mb-0 m-0 w-100">
      
      <!-- SELECTOR DE CATEGORÍA -->
      <div class="col-12 col-lg-4">
        <!-- 2. Redujimos el borde inferior a pb-1 (antes pb-2) -->
        <div class="d-flex align-items-center w-100 border-custom pb-1 input-group-hover">
          <font-awesome-icon icon="fa-solid fa-hotel" class="text-success me-3 fs-5" />
          <div class="flex-grow-1" style="min-width: 0;">
            <label class="form-label compact-label fw-bold text-success mb-0">¿Qué buscas?</label>
            <!-- 3. Agregamos py-0 y compact-select para aplastar el input -->
            <select v-model="tipoSeleccionado" class="form-select border-0 shadow-none px-0 py-0 fw-semibold text-dark search-input bg-transparent text-truncate compact-select">
              <option v-for="cat in categorias" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- CALENDARIO DE ENTRADA Y SALIDA -->
      <div class="col-12 col-lg-4">
        <VDatePicker v-model.range="range" :min-date="minDate" color="green" :columns="columnasCalendario">
          <template #default="{ inputValue, inputEvents }">
            <div class="d-flex align-items-center w-100 position-relative cursor-pointer border-custom pb-1 input-group-hover" v-on="inputEvents.start">
              <font-awesome-icon icon="fa-solid fa-calendar-days" class="text-success me-3 fs-5" />
              <div class="flex-grow-1" style="min-width: 0;">
                <label class="form-label compact-label fw-bold text-success mb-0 cursor-pointer">Llegada - Salida</label>
                <div class="fw-semibold text-dark search-input-display text-truncate compact-text">{{ fechaRangoAMostrar }}</div>
              </div>
            </div>
          </template>
        </VDatePicker>
      </div>

      <!-- HUÉSPEDES -->
      <div class="col-12 col-lg-2">
        <div class="d-flex align-items-center w-100 border-custom pb-1 input-group-hover">
          <font-awesome-icon icon="fa-solid fa-user-group" class="text-success me-3 fs-5" />
          <div class="flex-grow-1" style="min-width: 0;">
            <label class="form-label compact-label fw-bold text-success mb-0">Huéspedes</label>
            <select v-model="totalHuespedes" class="form-select border-0 shadow-none px-0 py-0 fw-semibold text-dark search-input bg-transparent text-truncate compact-select">
              <option v-for="n in 6" :key="n" :value="n">{{ n }} Huéspedes</option>
            </select>
          </div>
        </div>
      </div>

      <!-- BOTÓN DE BÚSQUEDA -->
      <div class="col-12 col-lg-2 mt-3 mt-lg-0 pb-1">
        <!-- 4. Quitamos el estilo en línea (style="padding...") y usamos py-2 para que sea más bajito -->
        <button @click="buscar" class="btn btn-search rounded-0 w-100 py-2 fw-bold shadow-none d-flex justify-content-center align-items-center" :disabled="buscando">
          <span v-if="buscando" class="spinner-border spinner-border-sm me-2"></span>
          <font-awesome-icon v-else icon="fa-solid fa-magnifying-glass" class="me-2 text-white" />
          <span v-if="!buscando" class="text-white">Buscar</span>
        </button>
      </div>

    </div>
  </div>
</template>


<style scoped>
.search-bar-container {
  max-width: 1150px; 
  position: relative;
  z-index: 10;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15); 
}

/* 🟢 NUEVO: Líneas divisorias suaves que cambian de color al pasar el mouse */
.border-custom {
  border-bottom: 1px solid #d1d5db; /* Un gris suave, no negro */
  transition: border-color 0.3s ease;
}

.input-group-hover:hover {
  border-bottom: 1px solid #0f3b2a; /* Se vuelve verde Kofán al acercar el mouse */
}

/* Ajustes de tipografía para que se vea más limpio */
.search-input, .search-input-display {
  font-size: 1.05rem;
}

.search-input:focus {
  outline: none;
  box-shadow: none;
}

select.search-input {
  cursor: pointer;
}

.cursor-pointer {
  cursor: pointer;
}

/* 🟢 NUEVO: Botón de búsqueda sólido y llamativo */
.btn-search {
  background-color: #0f3b2a !important; /* Verde oscuro corporativo */
  color: #ffffff !important;
  border: none !important;
  transition: all 0.3s ease;
}

.btn-search:hover {
  background-color: #1a5c46 !important; /* Un verde un poco más claro al hacer hover */
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(15, 59, 42, 0.3) !important;
}

/* Adaptación para celulares */
@media (max-width: 991px) {
  .search-bar-container {
    padding: 1.5rem !important;
  }
  .col-12 {
    margin-bottom: 15px; 
  }
  .col-12:last-child {
    margin-bottom: 0; 
  }
}
</style>