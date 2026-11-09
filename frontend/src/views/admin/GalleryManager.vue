<script setup>
import { ref, onMounted } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { listGallery, uploadGalleryImage, deleteGalleryImage } from "@/api/content";
import { assetUrl } from "@/config/env";
import ImageUploader from "@/components/ImageUploader.vue";

const fotos = ref([]);
const isLoading = ref(false);
const isUploading = ref(false);
const eliminando = ref(null);
const mostrarFormulario = ref(false);
const filtroActivo = ref("todos");

const archivosParaSubir = ref([]);
const uploaderRef = ref(null);
const tituloFotos = ref("");

// Categorías = slugs en minúscula (los mismos que filtra la galería pública).
const categorias = [
  { value: "naturaleza",    label: "Naturaleza" },
  { value: "experiencias",  label: "Experiencias" },
  { value: "instalaciones", label: "Habitaciones e Instalaciones" },
  { value: "eventos",       label: "Eventos" },
];
const categoriaSeleccionada = ref("instalaciones");

const etiquetaCategoria = (valor) => categorias.find((c) => c.value === valor)?.label || "General";

const cargarFotos = async (categoria = "todos") => {
  isLoading.value = true;
  try {
    fotos.value = await listGallery(categoria === "todos" ? null : categoria);
  } catch (error) {
    Swal.fire({ icon: "error", title: "Error", text: errorMessage(error, "No se pudieron cargar las fotos."), confirmButtonColor: "#0f3b2a" });
  } finally {
    isLoading.value = false;
  }
};

const cancelarUpload = () => {
  mostrarFormulario.value = false;
  if (uploaderRef.value) uploaderRef.value.reset();
  archivosParaSubir.value = [];
  tituloFotos.value = "";
};

const subirFotosBatch = async () => {
  if (archivosParaSubir.value.length === 0) return;
  isUploading.value = true;

  try {
    const resultados = await Promise.allSettled(
      archivosParaSubir.value.map((file) =>
        uploadGalleryImage(file, categoriaSeleccionada.value, tituloFotos.value.trim()),
      ),
    );
    const fallidas = resultados.filter((r) => r.status === "rejected");
    const subidas = resultados.length - fallidas.length;

    if (fallidas.length) {
      await Swal.fire({
        icon: subidas ? "warning" : "error",
        title: subidas ? `Se subieron ${subidas} de ${resultados.length} fotos` : "Error al subir",
        text: errorMessage(fallidas[0].reason, "Hubo un problema con una o más fotos."),
        confirmButtonColor: "#0f3b2a",
      });
    } else {
      await Swal.fire({
        icon: "success",
        title: `¡${subidas} foto(s) subida(s) correctamente!`,
        timer: 2000,
        showConfirmButton: false
      });
    }

    cancelarUpload();
    cargarFotos(filtroActivo.value);
  } finally {
    isUploading.value = false;
  }
};

const confirmarEliminar = async (foto) => {
  const result = await Swal.fire({
    title: "¿Eliminar foto?",
    text: `Se eliminará permanentemente.`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#dc3545",
    cancelButtonColor: "#6c757d",
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
  });

  if (!result.isConfirmed) return;

  eliminando.value = foto.id;
  try {
    await deleteGalleryImage(foto.id);
    fotos.value = fotos.value.filter(f => f.id !== foto.id);
    Swal.fire({ icon: "success", title: "Foto eliminada", timer: 1500, showConfirmButton: false });
  } catch (error) {
    Swal.fire({ icon: "error", title: "Error", text: errorMessage(error, "No se pudo eliminar la foto."), confirmButtonColor: "#0f3b2a" });
  } finally {
    eliminando.value = null;
  }
};

const cambiarFiltro = (cat) => {
  filtroActivo.value = cat;
  cargarFotos(cat);
};

const SIN_ARCHIVO = "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22400%22%20height%3D%22220%22%3E%3Crect%20width%3D%22400%22%20height%3D%22220%22%20fill%3D%22%23f8d7da%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%22115%22%20text-anchor%3D%22middle%22%20fill%3D%22%23842029%22%20font-family%3D%22Arial%22%20font-size%3D%2218%22%3EArchivo%20faltante%3C%2Ftext%3E%3C%2Fsvg%3E";
const onImagenError = (event) => {
  event.target.onerror = null;
  event.target.src = SIN_ARCHIVO;
};

onMounted(() => cargarFotos());
</script>

<template>
  <div class="gallery-manager">

    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h3 class="fw-bold verde-brand mb-0">Gestión de Galería</h3>
        <p class="text-muted small mb-0">Administra las fotos públicas del hotel</p>
      </div>
      <button class="btn btn-brand px-4" @click="mostrarFormulario = true" v-if="!mostrarFormulario">
        <font-awesome-icon icon="fa-solid fa-plus" class="me-2" />
        Subir Fotos
      </button>
    </div>

    <div class="d-flex gap-2 flex-wrap mb-4" v-if="!mostrarFormulario">
      <button
        v-for="cat in [{ value: 'todos', label: 'Todos' }, ...categorias]"
        :key="cat.value"
        class="btn px-4 rounded-pill transition-all"
        :class="filtroActivo === cat.value ? 'btn-brand text-white shadow-sm' : 'btn-outline-success'"
        @click="cambiarFiltro(cat.value)"
      >
        {{ cat.label }}
        <span v-if="filtroActivo === cat.value && cat.value !== 'todos'" class="ms-1 badge bg-white text-success rounded-circle">
          {{ fotos.length }}
        </span>
      </button>
    </div>

    <div v-if="mostrarFormulario" class="upload-card mb-4 p-4 shadow-sm bg-white rounded-4 border">
      <h5 class="fw-bold verde-brand mb-4">Agregar Nuevas Fotos</h5>

      <div class="row g-3 mb-4">
        <div class="col-md-6" style="max-width: 400px;">
          <label class="form-label fw-bold text-dark">¿A qué categoría pertenecen estas fotos?</label>
          <select v-model="categoriaSeleccionada" class="form-select form-select-lg border-success-subtle shadow-sm">
            <option v-for="cat in categorias" :key="cat.value" :value="cat.value">
              {{ cat.label }}
            </option>
          </select>
        </div>
        <div class="col-md-6" style="max-width: 400px;">
          <label class="form-label fw-bold text-dark">Título (opcional)</label>
          <input v-model="tituloFotos" type="text" class="form-control form-control-lg brand-input" maxlength="120"
                 placeholder="Ej: Atardecer en el río" />
        </div>
      </div>

      <ImageUploader
        ref="uploaderRef"
        v-model="archivosParaSubir"
        :maxFiles="10"
        :existingCount="0"
        :isEditing="true"
      />

      <div class="d-flex gap-2 mt-4 justify-content-end border-top pt-3">
        <button class="btn btn-outline-secondary px-4" @click="cancelarUpload">Cancelar</button>
        <button class="btn btn-brand px-5 fw-bold" @click="subirFotosBatch" :disabled="isUploading || archivosParaSubir.length === 0">
          <span v-if="isUploading" class="spinner-border spinner-border-sm me-2"></span>
          {{ isUploading ? 'Subiendo...' : 'Guardar Fotos' }}
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="text-center py-5">
      <div class="spinner-border text-success" role="status"></div>
      <p class="text-muted mt-2 small fw-bold">Cargando galería...</p>
    </div>

    <div v-else-if="fotos.length === 0 && !mostrarFormulario" class="empty-state text-center py-5 bg-light rounded-4 border border-dashed mt-3">
      <font-awesome-icon icon="fa-solid fa-images" class="fs-1 text-muted mb-3 d-block mx-auto opacity-50" />
      <h5 class="text-muted fw-bold">No hay fotos aquí</h5>
      <p class="text-muted small">Selecciona otra categoría o sube nuevas imágenes.</p>
    </div>

    <div v-else-if="!mostrarFormulario" class="row g-3 mt-2">
      <div v-for="foto in fotos" :key="foto.id" class="col-12 col-sm-6 col-md-4 col-lg-3">
        <div class="gallery-item position-relative mb-2 h-100">

          <img
            :src="assetUrl(foto.url)"
            :alt="foto.title || etiquetaCategoria(foto.category)"
            class="img-fluid rounded-4 shadow-sm w-100 object-fit-cover"
            style="height: 220px;"
            @error="onImagenError"
          />

          <div class="acciones-flotantes position-absolute top-0 w-100 p-2 d-flex justify-content-between align-items-start" style="left: 0;">
            <span class="badge bg-dark bg-opacity-75 text-white border border-secondary shadow-sm">
              {{ etiquetaCategoria(foto.category) }}
            </span>

            <button class="btn btn-danger btn-sm rounded-circle shadow transition-all hover-scale" @click="confirmarEliminar(foto)" :disabled="eliminando === foto.id" title="Eliminar foto">
              <span v-if="eliminando === foto.id" class="spinner-border spinner-border-sm"></span>
              <font-awesome-icon v-else icon="fa-solid fa-trash" />
            </button>
          </div>

          <div class="mt-2 text-truncate small fw-semibold text-secondary text-center px-2">
            {{ foto.title }}
          </div>

        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.gallery-manager {
  width: 100%;
  min-width: 0;
  max-width: none;
}

.upload-card,
.empty-state {
  width: 100%;
}


.upload-card {
  background: #fff;
  border-radius: 20px;
  border: 1px solid #e0e0e0;
}

.brand-input {
  border-radius: 10px;
  border: 1px solid #e0e0e0;
  padding: 10px 15px;
  background: #fdfdfd;
}

.brand-input:focus {
  border-color: #0f3b2a;
  box-shadow: 0 0 0 0.2rem rgba(15, 59, 42, 0.1);
}

.drop-zone {
  border: 2px dashed #c8e6c9;
  border-radius: 16px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f9fdf9;
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.drop-zone.drag-over {
  border-color: #0f3b2a;
  background: #f0fdf4;
}

.preview-img {
  max-height: 160px;
  border-radius: 10px;
  object-fit: cover;
}

.btn-brand {
  background-color: #0f3b2a;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-brand:hover:not(:disabled) {
  background-color: #1a5c43;
  transform: translateY(-1px);
}

.btn-brand:disabled { opacity: 0.7; cursor: not-allowed; }

.btn-outline-brand {
  border: 1px solid #0f3b2a;
  color: #0f3b2a;
  background: transparent;
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-outline-brand:hover {
  background: #f0fdf4;
}

/* Grid de fotos */
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.gallery-item {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  aspect-ratio: 4/3;
  background: #f0f0f0;
  cursor: pointer;
}

.gallery-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.gallery-item:hover .gallery-img {
  transform: scale(1.08);
}

.gallery-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(transparent 30%, rgba(15, 59, 42, 0.92));
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 14px;
  opacity: 0;
  transition: opacity 0.3s;
}

.gallery-item:hover .gallery-overlay {
  opacity: 1;
}

.foto-titulo {
  color: white;
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.2;
}

.badge-cat {
  background: rgba(255,255,255,0.2);
  color: #c8e6c9;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 20px;
  margin-top: 4px;
  display: inline-block;
}

.empty-state .fa-images { color: #ccc; }
.acciones-flotantes {
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
  /* Fondo oscuro degradado para que el texto blanco se lea bien incluso en fotos claras */
  background: linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 100%);
  border-radius: 1rem 1rem 0 0; 
}

/* Mostramos los botones cuando el mouse pasa por encima de la tarjeta (.gallery-item) */
.gallery-item:hover .acciones-flotantes {
  opacity: 1;
}

</style>