<script setup>
import { ref, computed } from "vue";
import Swal from "sweetalert2";
import draggable from "vuedraggable";

// Definimos las propiedades y v-model
const props = defineProps({
  maxFiles: { type: Number, default: 5 },
  existingCount: { type: Number, default: 0 },
  isEditing: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

const isDragging = ref(false); // Estado para el Drag & Drop externo
const fileInputRef = ref(null);
const newImages = ref([]); // { id: uniqueKey, file: File, previewUrl: string }

// Usamos computed para la cuenta dinámica
const fotosRestantesCount = computed(() => {
  return props.maxFiles - (props.existingCount + newImages.value.length);
});

// Función centralizada para procesar archivos nuevos
const procesarArchivos = (files) => {
  if (!files || !files.length) return;

  if (files.length > fotosRestantesCount.value) {
    Swal.fire("Límite excedido", `Solo puedes subir ${fotosRestantesCount.value} foto(s) más.`, "warning");
    return;
  }

  Array.from(files).forEach((file) => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      Swal.fire("Error", `El archivo '${file.name}' no es una imagen JPG, PNG o WebP.`, "error");
      return;
    }
    // Agregamos un ID único para la key de Vue y vuedraggable
    newImages.value.push({
      id: `${Date.now()}-${Math.random()}`,
      file,
      previewUrl: URL.createObjectURL(file),
    });
  });

  // Avisamos al padre (Gestión de Habitaciones) sobre los archivos reales
  emitirCambios();
};

const triggerFileInput = () => {
  if (fotosRestantesCount.value > 0) fileInputRef.value.click();
};

const quitarFotoNueva = (index) => {
  URL.revokeObjectURL(newImages.value[index].previewUrl);
  newImages.value.splice(index, 1);
  emitirCambios();
};

// Re-sincronizamos el array limpio de archivos reales al padre
const emitirCambios = () => {
  const archivosReales = newImages.value.map((img) => img.file);
  emit("update:modelValue", archivosReales);
};

// Función reset expuesta para el padre
const reset = () => {
  newImages.value.forEach((img) => URL.revokeObjectURL(img.previewUrl));
  newImages.value = [];
  emitirCambios();
};

defineExpose({ reset });
</script>

<template>
  <div class="card bg-light border-0 shadow-sm p-3 rounded-4 image-uploader-container">
    <label class="form-label fw-bold mb-1 text-dark">
      {{ isEditing ? "Añadir Nuevas Fotos" : `Fotos (Hasta ${maxFiles})` }}
    </label>
    <p class="text-muted small mb-3">
      <template v-if="!isEditing">
        La primera foto siempre será la <span class="text-success fw-bold">principal</span>.
      </template>
      <template v-else> Estas fotos se añadirán a la galería. </template>
    </p>
    <div
      v-if="fotosRestantesCount > 0"
      class="border border-2 border-dashed rounded-3 p-4 text-center mb-3 transition-all"
      :class="[isDragging ? 'border-success bg-success-subtle shadow-lg scale-102' : 'border-secondary']"
      style="border-style: dashed !important; cursor: pointer"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="
        isDragging = false;
        procesarArchivos($event.dataTransfer.files);
      "
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        class="d-none"
        accept="image/jpeg,image/png,image/webp"
        multiple
        @change="procesarArchivos($event.target.files)"
      />
      <div class="py-2">
        <font-awesome-icon icon="fa-solid fa-cloud-arrow-up" class="fs-1 text-secondary mb-2" />
        <h6 class="mb-1 fw-bold text-dark">Arrastra fotos aquí o haz clic</h6>
        <p class="text-muted small mb-0">
          Subiendo <strong>{{ props.existingCount + newImages.length }}</strong> de {{ props.maxFiles }}.
        </p>
      </div>
    </div>
    <div v-else class="text-center py-3">
      <font-awesome-icon icon="fa-solid fa-circle-check" class="fs-1 text-success mb-2" />
      <h6 class="text-success fw-bold mb-0">¡Límite de {{ props.maxFiles }} fotos alcanzado!</h6>
    </div>

    <draggable
      v-model="newImages"
      item-key="id"
      class="row g-2 mt-2"
      handle=".photo-card"
      animation="300"
      ghost-class="sortable-ghost"
      chosen-class="sortable-chosen"
      @end="emitirCambios"
    >
      <template #item="{ element, index }">
        <div class="col-4 col-md-3 col-lg-2 draggable-item">
          <div
            class="card photo-card h-100 p-1 position-relative transition-all shadow-sm rounded-3"
            :class="{
              'principal-highlight border border-success border-2 shadow': !isEditing && index === 0,
              border: isEditing || index !== 0,
            }"
          >
            <span
              v-if="!isEditing && index === 0"
              class="position-absolute principal-badge rounded-pill bg-success text-white"
            >
              Principal
            </span>

            <img
              :src="element.previewUrl"
              class="rounded object-fit-cover w-100 photo-preview"
              style="height: 90px"
            />

            <button
              type="button"
              class="btn btn-danger btn-sm rounded-pill position-absolute btn-quitar transition-all shadow-lg"
              title="Quitar foto"
              @click.stop="quitarFotoNueva(index)"
            >
              <font-awesome-icon :icon="['fas', 'trash']" style="font-size: 0.7rem" />
            </button>

            <div class="drag-handle text-muted">
              <font-awesome-icon :icon="['fas', 'grip-vertical']" />
            </div>
          </div>
        </div>
      </template>
    </draggable>
  </div>
</template>

<style scoped>
/* Animación de Entrada Suave (Sustituye a la "barra de carga") */
@keyframes fadeInSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.draggable-item {
  animation: fadeInSlideIn 0.4s ease-out forwards;
}

/* Estilos para el reordenamiento (High Performance) */
.draggable-item {
  cursor: grab;
}
.draggable-item:active {
  cursor: grabbing;
}

.sortable-ghost {
  opacity: 0.3 !important;
  border: 2px dashed #0f3b2a !important;
}
.sortable-chosen {
  transform: scale(1.03);
  shadow: 0 10px 20px rgba(0, 0, 0, 0.15) !important;
}

/* Efectos de Hover para el botón de eliminar */
.btn-quitar {
  bottom: 8px;
  right: 8px;
  opacity: 0;
  transform: scale(0.5);
  width: 28px;
  height: 28px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.photo-card:hover .btn-quitar {
  opacity: 1;
  transform: scale(1);
}

/* Foto principal resaltada */
.principal-highlight {
  background-color: #f0fdf4; /* Un verde súper claro */
}

.principal-badge {
  top: -8px;
  left: -8px;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 4px 10px;
  z-index: 5;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Sutil indicador de arrastre */
.drag-handle {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 0.8rem;
  opacity: 0.4;
  transition: opacity 0.3s;
}
.photo-card:hover .drag-handle {
  opacity: 1;
}

.transition-all {
  transition: all 0.3s ease;
}
.scale-102 {
  transform: scale(1.02);
}
</style>
