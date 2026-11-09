<script setup>
import { ref, computed, reactive, watch, onMounted, onUnmounted } from 'vue';
import Swal from 'sweetalert2';
import apiClient from "@/api/apiClient";
import { DatePicker as VDatePicker } from 'v-calendar';
import 'v-calendar/style.css';

const getBrandColor = (token, fallback) =>
  typeof window !== 'undefined'
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_FOREST = getBrandColor('--k-forest', '#0f3b2a');

const props = defineProps({
  show: Boolean,
  habitacion: Object
});

const emit = defineEmits(['close', 'reservaCreada']);

const pasoActual = ref(1);
const guardando = ref(false);
const reservasOcupadas = ref([]); // Aquí guardaremos las reservas reales de la BD
const minDate = ref(new Date());
const columnasCalendario = ref(window.innerWidth >= 768 ? 2 : 1);

const actualizarColumnas = () => {
  columnasCalendario.value = window.innerWidth >= 768 ? 2 : 1;
};

onMounted(() => window.addEventListener('resize', actualizarColumnas));
onUnmounted(() => window.removeEventListener('resize', actualizarColumnas));

// Objeto reactivo para el rango seleccionado en el calendario
const range = ref({
  start: null,
  end: null,
});

// El formulario para enviar a la base de datos
const formularioAdmin = reactive({
  cliente_nombre: '',
  cliente_email: '',
  cliente_celular: '',
  monto_total: null,
  observaciones: ''
  
});

// Calculadora automática de precio basada en tu base de datos
watch(range, (newRange) => {
  if (newRange && newRange.start && newRange.end) {
    // 1. Calculamos la diferencia en días (Noches)
    const noches = Math.ceil(Math.abs(newRange.end - newRange.start) / (1000 * 60 * 60 * 24));
    
    // 2. Tomamos el valor exacto de 'price' de tu MongoDB
    const precioPorNoche = props.habitacion.price || 0; 
    
    // 3. Multiplicamos y asignamos al formulario
    formularioAdmin.monto_total = noches * precioPorNoche;
  } else {
    // Si borran las fechas, limpiamos el precio
    formularioAdmin.monto_total = null;
  }
});

// Cargar fechas ocupadas cuando se abre el modal para una habitación
watch(() => props.show, (newVal) => {
  if (newVal && props.habitacion) {
    cargarFechasOcupadas();
  }

  if (!newVal) {
    range.value = { start: null, end: null };
    reservasOcupadas.value = [];
  }
});

watch(() => props.habitacion, (newHabitacion) => {
  if (props.show && newHabitacion) {
    cargarFechasOcupadas();
  }
});

const cargarFechasOcupadas = async () => {
  try {
    const idSeguro = props.habitacion?._id || props.habitacion?.id;
    if (!idSeguro) return;

    const response = await apiClient.get(`/rooms/${idSeguro}/booked-dates`);
    
    // 🔍 TRAMPA 1: ¿Qué nos envió FastAPI realmente?
    console.log("FastAPI respondió con:", response.data);

    // Mapeamos las fechas con un filtro de seguridad
    const fechasFormateadas = response.data.map(res => {
      // 1. Validamos que las variables existan
      if (!res.fecha_entrada || !res.fecha_salida) return null;

      // 2. Extraemos solo la parte "YYYY-MM-DD", ignorando las horas o la letra "T"
      const fEntradaStr = res.fecha_entrada.toString().split('T')[0];
      const fSalidaStr = res.fecha_salida.toString().split('T')[0];

      // 3. Separamos año, mes y día limpios
      const [inYear, inMonth, inDay] = fEntradaStr.split('-');
      const [outYear, outMonth, outDay] = fSalidaStr.split('-');
      
      return {
        start: new Date(inYear, inMonth - 1, inDay),
        end: new Date(outYear, outMonth - 1, outDay)
      };
    });

    // 4. Filtramos los nulos (por si alguna reserva venía dañada)
    reservasOcupadas.value = fechasFormateadas.filter(r => r !== null);
    
    // 🔍 TRAMPA 2: ¿Cómo las entendió el calendario?
    console.log("Fechas listas para el calendario:", reservasOcupadas.value);
    
  } catch (error) {
    console.error("Error loading booked dates:", error);
    reservasOcupadas.value = []; 
  }
};

// Configuración de atributos visuales para el calendario
const attributes = computed(() => [
  // Atributo 1: Días Ocupados (Rojo)
  {
    key: 'ocupado',
    highlight: {
      color: 'red',
      fillMode: 'light',
    },
    dates: reservasOcupadas.value,
    popover: {
      label: 'Reservado',
      visibility: 'hover',
    },
  },
  // v-calendar maneja automáticamente el resaltado de la selección (range)
]);

// Verifica si el rango está completo (entrada y salida seleccionadas)
const rangeComplete = computed(() => {
  return range.value && range.value.start && range.value.end;
});

// Formateo de fechas para mostrar en pantalla
const fechasSeleccionadasHTML = computed(() => {
  if (!rangeComplete.value) return null;
  const start = range.value.start.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
  const end = range.value.end.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
  
  // Calculamos noches
  const noches = Math.ceil(Math.abs(range.value.end - range.value.start) / (1000 * 60 * 60 * 24));

  return `<strong class="text-success">${start}</strong> al <strong class="text-success">${end}</strong> <span class="badge bg-success rounded-pill ms-2">${noches} noches</span>`;
});

const fechaEntradaFormateada = computed(() => range.value.start?.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' }));
const fechaSalidaFormateada = computed(() => range.value.end?.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' }));


// Lógica al hacer clic en un día
const onDayClick = (day) => {
  // Puedes agregar lógica aquí si necesitas validar algo extra al hacer clic
};

const avanzarPaso = () => {
  if (rangeComplete.value) {
    pasoActual.value = 2;
  }
};

const crearReservaAdmin = async () => {
  guardando.value = true;

  // 1. 🔍 TRAMPA DE DEBUG: Imprimimos en consola qué tiene realmente la habitación
  console.log("Habitación seleccionada (desde Props):", props.habitacion);

  // 2. Extraemos el ID con extrema seguridad
  const idSeguro = props.habitacion?._id || props.habitacion?.id;

  // 3. Si sigue vacío, detenemos todo y avisamos en pantalla
  if (!idSeguro) {
    Swal.fire({
      title: 'Error de Datos',
      text: 'No se pudo detectar el ID de la cabaña. Por favor, presiona F12, ve a la Consola y envíame lo que dice "Habitación seleccionada".',
      icon: 'warning',
      confirmButtonColor: COLOR_FOREST
    });
    guardando.value = false;
    return; // Detenemos la función aquí, no molestamos a FastAPI
  }

  try {
    // Formateamos las fechas localmente
    const fEntrada = new Date(range.value.start.getTime() - (range.value.start.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
    const fSalida = new Date(range.value.end.getTime() - (range.value.end.getTimezoneOffset() * 60000)).toISOString().split('T')[0];

    // Armamos el JSON con el ID seguro.
    // monto_total es opcional: si el admin lo deja vacío, el backend calcula el precio.
    const payload = {
      habitacion_id: idSeguro, 
      fecha_entrada: fEntrada,
      fecha_salida: fSalida,
      monto_total: formularioAdmin.monto_total ? Number(formularioAdmin.monto_total) : null,
      observaciones: formularioAdmin.observaciones || "Reserva manual desde Panel Admin",
      cliente_nombre: formularioAdmin.cliente_nombre,
      cliente_email: formularioAdmin.cliente_email,
      cliente_celular: formularioAdmin.cliente_celular,
    };

    // 🔍 TRAMPA DE DEBUG 2: Imprimimos el JSON exacto que va a viajar a FastAPI
    console.log("JSON a enviar:", payload);

    // Endpoint exclusivo de administrador (la reserva queda confirmada)
    await apiClient.post('/api/reservas/admin', payload);

    Swal.fire({
      title: '¡Reserva Confirmada!',
      text: 'La habitación ha sido bloqueada exitosamente.',
      icon: 'success',
      confirmButtonColor: COLOR_FOREST,
    });
    
    emit('reservaCreada');
    cerrar();
    
  } catch (error) {
    // ... tu bloque catch actual que maneja los errores visuales ...
    console.error("Error al crear reserva:", error.response?.data);
    
    let mensajeError = 'No se pudo crear la reserva. Verifique los datos.';
    const detail = error.response?.data?.detail;

    if (Array.isArray(detail)) {
      mensajeError = detail.map(err => `Problema con el campo: <b>${err.loc[err.loc.length - 1]}</b>`).join('<br>');
    } else if (typeof detail === 'string') {
      mensajeError = detail;
    }

    Swal.fire({
      title: 'Validación Fallida',
      html: mensajeError,
      icon: 'error',
      confirmButtonColor: COLOR_FOREST
    });
  } finally {
    guardando.value = false;
  }
};
const cerrar = () => {
  pasoActual.value = 1;
  range.value = { start: null, end: null };
  reservasOcupadas.value = [];
  Object.assign(formularioAdmin, {
    cliente_nombre: '',
    cliente_email: '',
    cliente_celular: '',
    monto_total: null,
    observaciones: ''
  });
  emit('close');
};
</script>

<template>
  <div v-if="show" class="modal-overlay d-flex justify-content-center align-items-center" @click.self="cerrar">
    <div class="modal-box bg-white rounded-4 shadow-lg overflow-hidden" style="max-width: 750px; width: 95%;">
      
      <div class="bg-dark text-white p-3 d-flex justify-content-between align-items-center border-bottom border-success border-3">
        <h5 class="mb-0 fw-bold d-flex align-items-center">
          <font-awesome-icon icon="fa-solid fa-bed" class="text-success me-3 fs-4" />
          Reservar: Hab. {{ habitacion?.room_number || habitacion?.name }}
        </h5>
        <button @click="cerrar" class="btn btn-sm text-white fs-5 border-0 hover-danger">
          <font-awesome-icon icon="fa-solid fa-times" />
        </button>
      </div>

      <div class="p-0"> <div v-if="pasoActual === 1">
          <div class="p-4 text-center bg-light border-bottom">
            <h5 class="text-success fw-bold mb-1">Paso 1: Seleccione fechas</h5>
            <p class="text-muted small mb-0">Haga clic en el día de entrada y luego en el de salida. Los días en rojo no están disponibles.</p>
          </div>

          <div class="p-3 d-flex justify-content-center calendar-container">
            <VDatePicker
              v-model.range="range"
              is-range
              :min-date="minDate"
              :disabled-dates="reservasOcupadas"
              :attributes="attributes"
              color="green"
              title-position="left"
              :columns="columnasCalendario"
              :trim-weeks="true"
            />
          </div>

          <div class="p-3 bg-light border-top d-flex justify-content-between align-items-center">
            <div class="text-start">
              <span v-if="fechasSeleccionadasHTML" v-html="fechasSeleccionadasHTML"></span>
              <span v-else class="text-muted small">Esperando selección de fechas...</span>
            </div>
            <button @click="avanzarPaso" class="btn btn-success px-5 rounded-pill shadow-sm fw-bold" :disabled="!rangeComplete">
              Continuar <font-awesome-icon icon="fa-solid fa-arrow-right" class="ms-2" />
            </button>
          </div>
        </div>

        <div v-if="pasoActual === 2" class="p-4">
          <button @click="pasoActual = 1" class="btn btn-link text-decoration-none text-secondary p-0 mb-4 hover-dark">
            <font-awesome-icon icon="fa-solid fa-arrow-left" class="me-2" /> Volver a selección de fechas
          </button>
          
          <div class="bg-success-light p-3 rounded-3 border border-success border-opacity-25 mb-4 text-center">
            <h6 class="text-success fw-bold mb-3">Resumen de Estadía</h6>
            <div class="row small fw-bold text-dark">
              <div class="col-6 border-end border-success border-opacity-25">
                <font-awesome-icon icon="fa-solid fa-calendar-check" class="me-2 text-success" /> Entra: {{ fechaEntradaFormateada }}
              </div>
              <div class="col-6">
                <font-awesome-icon icon="fa-solid fa-calendar-minus" class="me-2 text-success" /> Sale: {{ fechaSalidaFormateada }}
              </div>
            </div>
          </div>

          <form @submit.prevent="crearReservaAdmin">
            <div class="row g-3">
              <div class="col-md-7">
                <label class="form-label small fw-bold text-success">Nombre del Huésped</label>
                <input type="text" class="form-control" v-model="formularioAdmin.cliente_nombre" required placeholder="Ej. Juan Invitado">
              </div>
              <div class="col-md-5">
                <label class="form-label small fw-bold text-success">Celular</label>
                <input type="tel" class="form-control" v-model="formularioAdmin.cliente_celular" required placeholder="310 123 4567">
              </div>
              <div class="col-md-7">
                <label class="form-label small fw-bold text-success">Correo Electrónico</label>
                <input type="email" class="form-control" v-model="formularioAdmin.cliente_email" required placeholder="juan@email.com">
              </div>
              <div class="col-md-5">
                <label class="form-label small fw-bold text-success">Monto Total ($)</label>
                <input type="number" class="form-control" v-model="formularioAdmin.monto_total" required placeholder="Ej. 450000">
              </div>
              <div class="col-md-12">
                <label class="form-label small fw-bold text-success">Observaciones (Opcional)</label>
                <textarea class="form-control" v-model="formularioAdmin.observaciones" rows="2" placeholder="Ej. Llegará tarde, requiere cama extra..."></textarea>
              </div>
            </div>

            <div class="text-end mt-4 pt-3 border-top">
              <button type="submit" class="btn btn-dark px-4 rounded-pill shadow-sm" :disabled="guardando">
                <span v-if="guardando" class="spinner-border spinner-border-sm me-2"></span>
                <font-awesome-icon v-else icon="fa-solid fa-save" class="me-2" /> Confirmar Reserva
              </button>
            </div>
          </form>
        </div>

      </div>
    </div>
  </div>
</template>


<style scoped>
/* Estilos del Modal Overlay con Blur moderno */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background-color: rgba(15, 59, 42, 0.5); 
  z-index: 1060; 
  backdrop-filter: blur(6px);
  transition: all 0.3s ease;
}

/* Animación de entrada de la tarjeta */
.modal-box {
  animation: scaleIn 0.3s ease-out forwards;
  border: 1px solid rgba(15, 59, 42, 0.1);
}

@keyframes scaleIn {
  from { transform: scale(0.9) translateY(20px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}

/* Clases de utilidad personalizadas */
.bg-success-light {
  background-color: rgba(139, 207, 91, 0.12);
}

.hover-danger:hover {
  background-color: var(--k-danger) !important;
  color: var(--k-offwhite) !important;
}

.hover-dark:hover {
  color: var(--k-forest) !important;
}

.form-label-kofan {
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

/* Ajustes para el contenedor del calendario */
.calendar-container :deep(.vc-container) {
  width: 100%;
  --vc-accent-green: var(--k-forest); /* Color verde corporativo Kofán */
}

.calendar-container :deep(.vc-pane-container) {
  background-color: white;
}
:deep(.vc-day.is-not-in-month) {
  visibility: hidden !important;
  pointer-events: none !important;
}

/* Opcional: Asegura que el contenedor no genere barras de scroll raras */
:deep(.vc-pane-container) {
  overflow: hidden;
}
</style>




