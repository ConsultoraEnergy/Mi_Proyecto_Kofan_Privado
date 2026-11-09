<template>
  <div>
    <div class="input-group">
      <input
        :id="id || undefined"
        :type="inputType"
        class="form-control custom-input border-end-0 shadow-none"
        :class="{ 'is-invalid': error }"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :required="required"
        :minlength="minlength || undefined"
        v-model="model"
      />

      <button
        type="button"
        class="input-group-text bg-white border-start-0 custom-icon-container"
        :class="{ 'border-danger': error }"
        @click="toggle"
        :title="visible ? 'Ocultar contraseña' : 'Mostrar contraseña'"
        :aria-label="visible ? 'Ocultar contraseña' : 'Mostrar contraseña'"
      >
        <font-awesome-icon :icon="icon" class="text-muted" />
      </button>
    </div>

    <div v-if="error" class="invalid-feedback d-block text-start">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "" },
  error: { type: String, default: "" },
  id: { type: String, default: "" },
  autocomplete: { type: String, default: "current-password" },
  required: { type: Boolean, default: false },
  minlength: { type: Number, default: 0 },
});

const emit = defineEmits(["update:modelValue"]);

const visible = ref(false);

const inputType = computed(() => (visible.value ? "text" : "password"));
const icon = computed(() => (visible.value ? ["fas", "eye-slash"] : ["fas", "eye"]));

const toggle = () => {
  visible.value = !visible.value;
};

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});
</script>

<style scoped>
/* El ojito tiene puntero de clic y coincide con el borde de custom-input */
.custom-icon-container {
  cursor: pointer;
  border-color: #dee2e6;
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

/* Si el input está en error (is-invalid), el borde del ojito también se pone rojo */
.border-danger {
  border-color: #dc3545 !important;
}
</style>
