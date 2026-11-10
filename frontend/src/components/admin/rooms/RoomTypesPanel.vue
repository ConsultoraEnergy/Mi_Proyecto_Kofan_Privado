<script setup>
/** Catálogo de tipos de habitación: listado + formulario de alta/edición. */
import { ref } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { createRoomType, updateRoomType } from "@/api/rooms";

defineProps({
  types: { type: Array, required: true },
});

const emit = defineEmits(["saved"]);

const emptyType = () => ({ id: null, code: "", name: "", description: "", is_active: true, sort_order: 0 });
const typeForm = ref(emptyType());
const saving = ref(false);

const clear = () => {
  typeForm.value = emptyType();
};

const edit = (type) => {
  typeForm.value = { ...type };
};

async function save() {
  saving.value = true;
  try {
    const { id, code, name, description, is_active, sort_order } = typeForm.value;
    const data = {
      name: name.trim(),
      description: (description || "").trim(),
      is_active,
      sort_order: Number(sort_order) || 0,
    };
    if (id) await updateRoomType(id, data);
    else await createRoomType({ code: code.trim().toLowerCase(), ...data });
    clear();
    emit("saved");
    Swal.fire({
      icon: "success",
      title: "Tipo de habitación guardado",
      timer: 1400,
      showConfirmButton: false,
    });
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo guardar el tipo de habitación."), "error");
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="card eco-card border-0 shadow-sm rounded-4 p-3 mb-4">
    <h6 class="fw-bold mb-3">Tipos de habitación</h6>
    <div class="table-responsive mb-3">
      <table class="table table-sm align-middle mb-0">
        <thead class="table-soft">
          <tr>
            <th class="small text-muted">Código</th>
            <th class="small text-muted">Nombre</th>
            <th class="small text-muted">Orden</th>
            <th class="small text-muted">Estado</th>
            <th><span class="visually-hidden">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!types.length">
            <td colspan="5" class="text-muted small text-center py-3">Aún no hay tipos registrados.</td>
          </tr>
          <tr v-for="type in types" :key="type.id">
            <td>
              <code>{{ type.code }}</code>
            </td>
            <td>{{ type.name }}</td>
            <td>{{ type.sort_order }}</td>
            <td>
              <span class="badge" :class="type.is_active ? 'bg-success' : 'bg-secondary'">
                {{ type.is_active ? "Activo" : "Inactivo" }}
              </span>
            </td>
            <td class="text-end">
              <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill" @click="edit(type)">
                <font-awesome-icon icon="fa-regular fa-pen-to-square" /> Editar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <form class="row g-2 align-items-end" @submit.prevent="save">
      <div class="col-md-2">
        <label class="form-label small fw-bold mb-1" for="type-code">Código</label>
        <input
          id="type-code"
          v-model="typeForm.code"
          type="text"
          class="form-control form-control-sm"
          placeholder="cabana"
          :disabled="!!typeForm.id"
          required
          pattern="[a-z0-9\-]{2,40}"
          title="Minúsculas, números y guiones"
        />
      </div>
      <div class="col-md-3">
        <label class="form-label small fw-bold mb-1" for="type-name">Nombre</label>
        <input
          id="type-name"
          v-model="typeForm.name"
          type="text"
          class="form-control form-control-sm"
          placeholder="Cabaña"
          required
          minlength="2"
        />
      </div>
      <div class="col-md-3">
        <label class="form-label small fw-bold mb-1" for="type-description">Descripción</label>
        <input
          id="type-description"
          v-model="typeForm.description"
          type="text"
          class="form-control form-control-sm"
        />
      </div>
      <div class="col-md-1">
        <label class="form-label small fw-bold mb-1" for="type-order">Orden</label>
        <input
          id="type-order"
          v-model="typeForm.sort_order"
          type="number"
          class="form-control form-control-sm"
        />
      </div>
      <div class="col-md-1">
        <div class="form-check mb-1">
          <input id="type-active" v-model="typeForm.is_active" class="form-check-input" type="checkbox" />
          <label class="form-check-label small" for="type-active">Activo</label>
        </div>
      </div>
      <div class="col-md-2 d-flex gap-1">
        <button type="submit" class="btn btn-sm btn-brand flex-grow-1" :disabled="saving">
          {{ typeForm.id ? "Actualizar" : "Agregar" }}
        </button>
        <button
          v-if="typeForm.id"
          type="button"
          class="btn btn-sm btn-light border"
          title="Cancelar edición"
          @click="clear"
        >
          <font-awesome-icon icon="fa-solid fa-xmark" />
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.table-soft th {
  background: rgba(52, 152, 219, 0.08) !important;
}
</style>
