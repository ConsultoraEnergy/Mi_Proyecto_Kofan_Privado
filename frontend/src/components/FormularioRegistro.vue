<script setup>
/**
 * Formulario de datos de usuario. Emite `enviar` con los nombres de campo de la API v1:
 *  - Registro público (sin `mostrarRol`, sin `usuarioEditando`):
 *      { email, password, full_name, person_type, document_type, document_number,
 *        phone?, country?, city?, accept_privacy_policy: true }
 *  - Alta por el personal (`mostrarRol`): { email, full_name, role, person_type, document_type?,
 *      document_number?, phone?, country?, city? } (sin contraseña: el usuario recibe un enlace).
 *  - Edición (`usuarioEditando`): { id, full_name, person_type, phone, country, city,
 *      document_type?, document_number?, role? (solo si cambió) }.
 */
import { ref, computed, watch } from "vue";
import PasswordInput from "@/components/form/PasswordInput.vue";
import { DOCUMENT_TYPES, PERMISSIONS, ROLE_LABELS } from "@/constants/booking";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

const props = defineProps({
  mostrarRol: { type: Boolean, default: false },
  cargando: { type: Boolean, default: false },
  usuarioEditando: { type: Object, default: null },
});

const emit = defineEmits(["enviar"]);

const MIN_PASSWORD = 8;

const PERSON_TYPES = [
  { value: "natural", label: "Natural" },
  { value: "legal", label: "Jurídica" },
];

const emptyForm = () => ({
  person_type: "natural",
  full_name: "",
  document_type: "",
  document_number: "",
  email: "",
  phone: "",
  country: "",
  city: "",
  password: "",
  role: "client",
});

const form = ref(emptyForm());
const confirmPassword = ref("");
const acceptPrivacy = ref(false);

const isEditing = computed(() => !!props.usuarioEditando);
const isPublicRegister = computed(() => !isEditing.value && !props.mostrarRol);
// Sin users:manage_staff (recepción) solo se ofrece "Cliente"; el rol actual se muestra para no
// alterar visualmente a un miembro del personal que se esté editando. El backend aplica la regla real.
const roleOptions = computed(() =>
  Object.entries(ROLE_LABELS)
    .filter(([value]) =>
      auth.can(PERMISSIONS.USERS_MANAGE_STAFF) || value === "client" || value === props.usuarioEditando?.role,
    )
    .map(([value, label]) => ({ value, label })),
);

const resetForm = () => {
  form.value = emptyForm();
  confirmPassword.value = "";
  acceptPrivacy.value = false;
};

watch(
  () => props.usuarioEditando,
  (user) => {
    if (user) {
      form.value = {
        ...emptyForm(),
        person_type: user.person_type || "natural",
        full_name: user.full_name || "",
        document_type: user.document_type || "",
        document_number: user.document_number || "",
        email: user.email || "",
        phone: user.phone || "",
        country: user.country || "",
        city: user.city || "",
        role: user.role || "client",
      };
      confirmPassword.value = "";
    } else {
      resetForm();
    }
  },
  { immediate: true },
);

const passwordError = computed(() =>
  confirmPassword.value && form.value.password !== confirmPassword.value ? "Las contraseñas no coinciden" : "",
);

const isFormInvalid = computed(() => {
  const f = form.value;
  if (!f.full_name.trim() || !f.person_type) return true;
  if (!isEditing.value && !f.email.trim()) return true;
  // El documento es obligatorio en el registro público; para el personal es opcional, pero va completo.
  const hasDocType = !!f.document_type;
  const hasDocNumber = !!f.document_number.trim();
  if (isPublicRegister.value && (!hasDocType || !hasDocNumber)) return true;
  if (hasDocType !== hasDocNumber) return true;
  if (isPublicRegister.value) {
    if (f.password.length < MIN_PASSWORD || f.password !== confirmPassword.value) return true;
    if (!acceptPrivacy.value) return true;
  }
  return false;
});

/** Texto opcional: cadena recortada o null si está vacío. */
const optional = (value) => {
  const text = (value || "").trim();
  return text || null;
};

/** Quita las claves con null/"" (en creación los opcionales simplemente no se envían). */
const compact = (obj) => Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== null && v !== ""));

const buildPayload = () => {
  const f = form.value;
  const document = f.document_type
    ? { document_type: f.document_type, document_number: f.document_number.trim() }
    : {};

  if (isEditing.value) {
    const payload = {
      id: props.usuarioEditando.id,
      full_name: f.full_name.trim(),
      person_type: f.person_type,
      phone: optional(f.phone),
      country: optional(f.country),
      city: optional(f.city),
      ...document,
    };
    if (props.mostrarRol && f.role !== props.usuarioEditando.role) payload.role = f.role;
    return payload;
  }

  const base = compact({
    email: f.email.trim(),
    full_name: f.full_name.trim(),
    person_type: f.person_type,
    phone: optional(f.phone),
    country: optional(f.country),
    city: optional(f.city),
    ...document,
  });

  if (props.mostrarRol) return { ...base, role: f.role };
  return { ...base, password: f.password, accept_privacy_policy: true };
};

const procesarFormulario = () => {
  if (isFormInvalid.value) return;
  emit("enviar", buildPayload());
};

defineExpose({ resetForm });
</script>

<template>
  <form @submit.prevent="procesarFormulario" class="row g-3">
    <div class="col-md-6">
      <label class="form-label fw-semibold small mb-1 text-muted">Tipo Persona</label>
      <select v-model="form.person_type" class="form-select custom-input bg-light" required>
        <option v-for="t in PERSON_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
      </select>
    </div>

    <div class="col-md-6">
      <label class="form-label fw-semibold small mb-1 text-muted">
        Nombre Completo <span class="text-danger">*</span>
      </label>
      <input
        v-model="form.full_name"
        type="text"
        class="form-control custom-input"
        placeholder="Ej: Fabián Gómez"
        autocomplete="name"
        minlength="2"
        maxlength="120"
        required
      />
    </div>

    <div class="col-md-6">
      <label class="form-label fw-semibold small mb-1">
        Documento <span v-if="isPublicRegister" class="text-danger">*</span>
      </label>
      <div class="input-group">
        <select
          v-model="form.document_type"
          class="form-select custom-input"
          style="max-width: 150px"
          :required="isPublicRegister"
        >
          <option value="" :disabled="isPublicRegister">Tipo...</option>
          <option v-for="d in DOCUMENT_TYPES" :key="d.value" :value="d.value" :title="d.label">
            {{ d.value === "PASSPORT" ? "Pasaporte" : d.value }}
          </option>
        </select>
        <input
          v-model="form.document_number"
          type="text"
          class="form-control custom-input"
          placeholder="Ej: 12345678"
          pattern="[A-Za-z0-9\-]{3,20}"
          title="Entre 3 y 20 letras, números o guiones"
          :required="isPublicRegister || !!form.document_type"
        />
      </div>
    </div>

    <div class="col-md-6">
      <label class="form-label fw-semibold small mb-1 text-muted">
        Correo Electrónico <span v-if="!isEditing" class="text-danger">*</span>
      </label>
      <input
        v-model="form.email"
        type="email"
        class="form-control custom-input bg-light"
        autocomplete="email"
        :disabled="isEditing"
        :required="!isEditing"
      />
    </div>

    <div class="col-md-6">
      <label class="form-label fw-semibold small mb-1">Teléfono</label>
      <input
        v-model="form.phone"
        type="tel"
        class="form-control custom-input"
        placeholder="+57 3xx..."
        autocomplete="tel"
        pattern="[0-9+\(\)\s\-]{7,20}"
        title="Entre 7 y 20 dígitos (se permiten +, (), espacios y guiones)"
      />
    </div>

    <div class="col-md-3">
      <label class="form-label fw-semibold small mb-1">País</label>
      <input v-model="form.country" type="text" class="form-control custom-input" maxlength="80" autocomplete="country-name" />
    </div>

    <div class="col-md-3">
      <label class="form-label fw-semibold small mb-1">Ciudad</label>
      <input v-model="form.city" type="text" class="form-control custom-input" maxlength="80" autocomplete="address-level2" />
    </div>

    <template v-if="isPublicRegister">
      <div class="col-md-6">
        <label class="form-label fw-semibold small mb-1">Contraseña <span class="text-danger">*</span></label>
        <PasswordInput
          v-model="form.password"
          placeholder="Mínimo 8 caracteres"
          autocomplete="new-password"
          :minlength="MIN_PASSWORD"
          required
        />
      </div>
      <div class="col-md-6">
        <label class="form-label fw-semibold small mb-1">Confirmar Contraseña <span class="text-danger">*</span></label>
        <PasswordInput
          v-model="confirmPassword"
          placeholder="Repite la clave"
          autocomplete="new-password"
          :error="passwordError"
          required
        />
      </div>

      <div class="col-12">
        <div class="form-check">
          <input id="accept-privacy" v-model="acceptPrivacy" class="form-check-input" type="checkbox" required />
          <label class="form-check-label small" for="accept-privacy">
            Autorizo el tratamiento de mis datos personales conforme a la política de tratamiento de datos
            (Ley 1581 de 2012). <span class="text-danger">*</span>
          </label>
        </div>
      </div>
    </template>

    <div v-if="mostrarRol" class="col-12 mt-2">
      <label class="form-label fw-semibold small mb-1 text-primary">Rol en el Sistema</label>
      <select v-model="form.role" class="form-select custom-input border-primary">
        <option v-for="r in roleOptions" :key="r.value" :value="r.value">{{ r.label }}</option>
      </select>
      <p v-if="!isEditing" class="small text-muted mt-2 mb-0">
        El usuario recibirá un correo con un enlace para definir su contraseña.
      </p>
    </div>

    <div class="col-12 mt-4 d-flex justify-content-center">
      <button type="submit" class="btn btn-brand px-5 py-2 shadow-sm w-100" :disabled="props.cargando || isFormInvalid">
        <span v-if="props.cargando" class="spinner-border spinner-border-sm me-2"></span>
        {{ props.cargando ? "Procesando..." : isEditing ? "Guardar Cambios" : "Registrar Usuario" }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.custom-input:disabled {
  background-color: #f8f9fa !important;
  cursor: not-allowed;
  border-color: #e9ecef;
  color: #6c757d;
}
.btn-brand {
  border-radius: 10px;
}
</style>
