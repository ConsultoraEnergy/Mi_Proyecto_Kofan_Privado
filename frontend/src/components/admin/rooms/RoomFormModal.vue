<script setup>
/**
 * Modal Bootstrap para registrar o editar una habitación. Se abre con data-bs-toggle desde los
 * botones del padre (que llaman antes a `openCreate` / `openEdit` mediante la ref del componente).
 */
import { ref } from "vue";
import { MAX_ROOM_PHOTOS, OPERATIONAL_STATUS } from "@/constants/rooms";
import { useRoomForm } from "@/composables/useRoomForm";
import ImageUploader from "@/components/ImageUploader.vue";
import RoomAmenitiesPicker from "@/components/admin/rooms/RoomAmenitiesPicker.vue";
import RoomPhotosEditor from "@/components/admin/rooms/RoomPhotosEditor.vue";

defineProps({
  modalId: { type: String, required: true },
  roomTypes: { type: Array, required: true },
});

/** `changed`: el inventario debe recargarse (se guardó algo o se borró una foto). */
const emit = defineEmits(["changed"]);

const {
  form,
  isEditing,
  pendingFiles,
  submitting,
  amenityOptions,
  reset,
  startEdit,
  save,
  removeImage,
  setMainImage,
} = useRoomForm();

const uploaderRef = ref(null);
const closeBtnRef = ref(null);

function resetAll() {
  reset();
  uploaderRef.value?.reset();
}

function openCreate() {
  resetAll();
}

function openEdit(room) {
  uploaderRef.value?.reset();
  startEdit(room);
}

async function submit() {
  const done = await save();
  emit("changed");
  // El botón "Cancelar" cierra el modal (data-bs-dismiss) y limpia el formulario.
  if (done) closeBtnRef.value?.click();
}

async function onRemoveImage(url) {
  if (await removeImage(url)) emit("changed");
}

defineExpose({ openCreate, openEdit });
</script>

<template>
  <div
    :id="modalId"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
    :aria-labelledby="`${modalId}-title`"
  >
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content border-0 shadow-lg eco-card">
        <div class="modal-header modal-soft-header border-0">
          <h5 :id="`${modalId}-title`" class="modal-title section-title mb-0">
            <font-awesome-icon :icon="isEditing ? 'fa-solid fa-bed' : 'fa-solid fa-leaf'" class="me-2" />
            {{ isEditing ? "Editar Habitación" : "Registrar Habitación" }}
          </h5>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Cerrar"
            @click="resetAll"
          ></button>
        </div>

        <form @submit.prevent="submit">
          <div class="modal-body p-4">
            <div class="row g-3">
              <div class="col-md-4">
                <label class="form-label fw-bold" for="room-number">N° Habitación</label>
                <input
                  id="room-number"
                  v-model="form.number"
                  type="text"
                  class="form-control"
                  required
                  maxlength="20"
                />
              </div>

              <div class="col-md-8">
                <label class="form-label fw-bold" for="room-name">Nombre</label>
                <input
                  id="room-name"
                  v-model="form.name"
                  type="text"
                  class="form-control"
                  required
                  minlength="2"
                  maxlength="120"
                />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold" for="room-price">Precio por noche</label>
                <input
                  id="room-price"
                  v-model="form.price_per_night"
                  type="number"
                  min="1"
                  step="any"
                  class="form-control"
                  required
                />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold" for="room-capacity">Capacidad Total (Pers.)</label>
                <input
                  id="room-capacity"
                  v-model="form.capacity"
                  type="number"
                  min="1"
                  max="50"
                  class="form-control"
                  required
                />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold" for="room-type">Tipo de Alojamiento</label>
                <select id="room-type" v-model="form.room_type_id" class="form-select" required>
                  <option value="" disabled>Selecciona una opción...</option>
                  <option v-for="type in roomTypes" :key="type.id" :value="type.id">
                    {{ type.name }}{{ type.is_active ? "" : " (inactivo)" }}
                  </option>
                </select>
                <small v-if="!roomTypes.length" class="text-muted"
                  >Primero crea un tipo en "Tipos de habitación".</small
                >
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold" for="room-bedrooms">N° de Habitaciones (Cuartos)</label>
                <input
                  id="room-bedrooms"
                  v-model="form.bedrooms"
                  type="number"
                  min="1"
                  max="20"
                  class="form-control"
                  required
                />
              </div>

              <div class="col-12 mt-3">
                <label class="form-label fw-bold" for="room-beds">Distribución de Camas</label>
                <input
                  id="room-beds"
                  v-model="form.beds"
                  type="text"
                  class="form-control"
                  maxlength="200"
                  placeholder="Ej: 1 Cama Doble, 2 Sencillas"
                />
                <small class="text-muted"
                  >Este texto es el que verá el cliente en la tarjeta principal.</small
                >
              </div>

              <div class="col-md-6 mt-3">
                <label class="form-label fw-bold" for="room-status">Estado Operativo</label>
                <select id="room-status" v-model="form.operational_status" class="form-select">
                  <option v-for="(meta, value) in OPERATIONAL_STATUS" :key="value" :value="value">
                    {{ meta.label }}
                  </option>
                </select>
              </div>

              <div class="col-md-6 mt-3 d-flex align-items-end">
                <div class="form-check form-switch mb-2">
                  <input
                    id="room-is-active"
                    v-model="form.is_active"
                    class="form-check-input"
                    type="checkbox"
                    role="switch"
                  />
                  <label class="form-check-label fw-bold" for="room-is-active"
                    >Habilitada para la venta</label
                  >
                </div>
              </div>

              <div class="col-12 mt-3">
                <label class="form-label fw-bold" for="room-description">Descripción de la Habitación</label>
                <textarea
                  id="room-description"
                  v-model="form.description"
                  class="form-control border-light-subtle shadow-sm"
                  rows="2"
                  maxlength="3000"
                  placeholder="Ej: Cabaña romántica ideal para parejas..."
                ></textarea>
              </div>

              <div class="col-12 mt-4">
                <p class="form-label fw-bold mb-3 border-bottom pb-2 w-100">
                  ¿Qué incluye la habitación? (Amenidades)
                </p>
                <RoomAmenitiesPicker v-model="form.amenities" :options="amenityOptions" />
              </div>

              <div v-if="isEditing && form.images.length" class="col-12 mt-4">
                <RoomPhotosEditor
                  :images="form.images"
                  :main-image="form.main_image"
                  @set-main="setMainImage"
                  @remove="onRemoveImage"
                />
              </div>

              <div class="col-12 mt-3">
                <ImageUploader
                  ref="uploaderRef"
                  v-model="pendingFiles"
                  :max-files="MAX_ROOM_PHOTOS"
                  :existing-count="form.images.length"
                  :is-editing="isEditing"
                />
              </div>
            </div>
          </div>

          <div class="modal-footer border-0 p-4 pt-0">
            <button
              ref="closeBtnRef"
              type="button"
              class="btn btn-light border px-4 rounded-pill"
              data-bs-dismiss="modal"
              @click="resetAll"
            >
              Cancelar
            </button>
            <button type="submit" class="btn btn-brand px-4 rounded-pill shadow-sm" :disabled="submitting">
              {{ submitting ? "Guardando..." : isEditing ? "Guardar cambios" : "Guardar habitación" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-soft-header {
  background: linear-gradient(135deg, var(--k-sky-soft) 0%, var(--k-offwhite) 100%);
}
</style>
