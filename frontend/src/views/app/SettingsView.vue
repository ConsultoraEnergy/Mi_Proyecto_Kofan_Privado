<script setup>
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import Swal from "sweetalert2";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { updateMe, changePassword, deactivateMe } from "@/api/users";
import { errorMessage } from "@/api/apiClient";
import PasswordInput from "@/components/form/PasswordInput.vue";

const MIN_PASSWORD = 8;

const auth = useAuthStore();
const configStore = useConfigStore();
const router = useRouter();

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");
const COLOR_APPLE = getBrandColor("--k-apple", "#8BCF5B");
const COLOR_DANGER = getBrandColor("--k-danger", "#c92a2a");

// --- Datos personales ---
const formData = ref({ full_name: "", phone: "", country: "", city: "" });
const savingProfile = ref(false);

watch(
  () => auth.user,
  (user) => {
    formData.value = {
      full_name: user?.full_name || "",
      phone: user?.phone || "",
      country: user?.country || "",
      city: user?.city || "",
    };
  },
  { immediate: true },
);

const documentLabel = computed(() =>
  auth.user?.document_number
    ? `${auth.user.document_type || ""} ${auth.user.document_number}`.trim()
    : "sin registrar",
);

const optional = (value) => (value || "").trim() || null;

const saveProfile = async () => {
  const result = await Swal.fire({
    title: "¿Confirmar cambios?",
    text: "Se actualizará tu información personal",
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: COLOR_FOREST,
    cancelButtonColor: "#6c757d",
    confirmButtonText: "Sí, guardar",
    cancelButtonText: "Cancelar",
  });
  if (!result.isConfirmed) return;

  savingProfile.value = true;
  try {
    const updated = await updateMe({
      full_name: formData.value.full_name.trim(),
      phone: optional(formData.value.phone),
      country: optional(formData.value.country),
      city: optional(formData.value.city),
    });
    auth.updateUser(updated);
    Swal.fire({
      title: "¡Actualizado!",
      text: "Tus datos se han guardado.",
      icon: "success",
      confirmButtonColor: COLOR_APPLE,
    });
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "Hubo un problema al actualizar los datos."), "error");
  } finally {
    savingProfile.value = false;
  }
};

// --- Cambio de contraseña ---
const passwords = ref({ current: "", next: "", confirm: "" });
const savingPassword = ref(false);

const passwordMismatch = computed(() =>
  passwords.value.confirm && passwords.value.next !== passwords.value.confirm
    ? "Las contraseñas no coinciden"
    : "",
);
const passwordInvalid = computed(
  () =>
    !passwords.value.current ||
    passwords.value.next.length < MIN_PASSWORD ||
    passwords.value.next !== passwords.value.confirm,
);

const savePassword = async () => {
  if (passwordInvalid.value) return;
  savingPassword.value = true;
  const email = auth.user.email;
  const newPassword = passwords.value.next;
  try {
    await changePassword(passwords.value.current, newPassword);
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No pudimos cambiar tu contraseña."), "error");
    savingPassword.value = false;
    return;
  }

  passwords.value = { current: "", next: "", confirm: "" };
  // El backend cierra TODAS las sesiones (incluida esta); se abre una nueva con la contraseña nueva.
  try {
    await auth.login(email, newPassword);
    Swal.fire({
      icon: "success",
      title: "Contraseña actualizada",
      text: "Por seguridad cerramos tu sesión en los demás dispositivos.",
      confirmButtonColor: COLOR_APPLE,
    });
  } catch {
    auth.clear();
    await Swal.fire({
      icon: "info",
      title: "Contraseña actualizada",
      text: "Cerramos todas tus sesiones. Inicia sesión de nuevo con tu nueva contraseña.",
      confirmButtonColor: COLOR_FOREST,
    });
    router.push({ name: "login" });
  } finally {
    savingPassword.value = false;
  }
};

// --- Desactivar cuenta ---
const deactivating = ref(false);

const deactivateAccount = async () => {
  const result = await Swal.fire({
    title: "¿Desactivar tu cuenta?",
    text: `No podrás volver a iniciar sesión en ${configStore.hotelName}. Para reactivarla tendrás que contactar al hotel.`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: COLOR_DANGER,
    cancelButtonColor: "#6c757d",
    confirmButtonText: "Sí, desactivar",
    cancelButtonText: "Cancelar",
  });
  if (!result.isConfirmed) return;

  deactivating.value = true;
  try {
    await deactivateMe();
    // La cuenta ya quedó desactivada: aunque falle el cierre de sesión en el servidor, se limpia localmente.
    await auth.logout().catch(() => {});
    await Swal.fire({ icon: "success", title: "Cuenta desactivada", confirmButtonColor: COLOR_FOREST });
    router.push("/");
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No pudimos desactivar tu cuenta."), "error");
  } finally {
    deactivating.value = false;
  }
};
</script>

<template>
  <div class="settings-container p-1">
    <div class="mb-4">
      <h3 class="fw-bold text-dark mb-1">Configuración</h3>
      <p class="text-muted small mb-0">Actualiza tu información de contacto personal.</p>
    </div>

    <!-- Datos personales -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden mb-4">
      <div class="card-header bg-white p-4 border-bottom d-flex align-items-center">
        <h5 class="fw-bold mb-0 verde-brand">
          <font-awesome-icon icon="fa-solid fa-user-gear" class="me-2" /> Mis Datos
        </h5>
      </div>

      <div class="card-body p-4 p-md-5">
        <form @submit.prevent="saveProfile">
          <div class="row g-4 mb-4">
            <div class="col-md-6">
              <label class="form-label fw-bold text-secondary small">Nombre Completo</label>
              <div class="input-group shadow-sm rounded">
                <span class="input-group-text bg-white text-muted border-end-0"
                  ><font-awesome-icon icon="fa-solid fa-user"
                /></span>
                <input
                  v-model="formData.full_name"
                  type="text"
                  class="form-control border-start-0 ps-0"
                  minlength="2"
                  maxlength="120"
                  required
                />
              </div>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-secondary small">Teléfono</label>
              <div class="input-group shadow-sm rounded">
                <span class="input-group-text bg-white text-muted border-end-0"
                  ><font-awesome-icon icon="fa-solid fa-phone"
                /></span>
                <input
                  v-model="formData.phone"
                  type="tel"
                  class="form-control border-start-0 ps-0"
                  pattern="[0-9+\(\)\s\-]{7,20}"
                  title="Entre 7 y 20 dígitos (se permiten +, (), espacios y guiones)"
                />
              </div>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-secondary small">País</label>
              <div class="input-group shadow-sm rounded">
                <span class="input-group-text bg-white text-muted border-end-0"
                  ><font-awesome-icon icon="fa-solid fa-earth-americas"
                /></span>
                <input
                  v-model="formData.country"
                  type="text"
                  class="form-control border-start-0 ps-0"
                  maxlength="80"
                />
              </div>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-secondary small">Ciudad de Residencia</label>
              <div class="input-group shadow-sm rounded">
                <span class="input-group-text bg-white text-muted border-end-0"
                  ><font-awesome-icon icon="fa-solid fa-location-dot"
                /></span>
                <input
                  v-model="formData.city"
                  type="text"
                  class="form-control border-start-0 ps-0"
                  maxlength="80"
                />
              </div>
            </div>
          </div>

          <div
            class="alert alert-success bg-opacity-10 border border-success-subtle d-flex align-items-center small text-dark rounded-4 p-3"
          >
            <font-awesome-icon icon="fa-solid fa-shield-halved" class="fs-4 me-3 text-success" />
            <div>
              <strong>Datos protegidos:</strong> Tu correo electrónico ({{ auth.user?.email }}) y número de
              documento ({{ documentLabel }}) no pueden modificarse desde aquí. Si necesitas corregirlos,
              contacta al hotel.
            </div>
          </div>

          <div class="mt-4 d-flex justify-content-end">
            <button
              type="submit"
              class="btn btn-brand-save px-5 py-2 shadow-sm rounded-pill fw-medium"
              :disabled="savingProfile"
            >
              <span v-if="savingProfile" class="spinner-border spinner-border-sm me-2"></span>
              <font-awesome-icon v-else icon="fa-solid fa-save" class="me-2" /> Guardar Cambios
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Cambiar contraseña -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden mb-4">
      <div class="card-header bg-white p-4 border-bottom d-flex align-items-center">
        <h5 class="fw-bold mb-0 verde-brand">
          <font-awesome-icon icon="fa-solid fa-key" class="me-2" /> Cambiar Contraseña
        </h5>
      </div>

      <div class="card-body p-4 p-md-5">
        <form @submit.prevent="savePassword">
          <div class="row g-4 mb-3">
            <div class="col-md-4">
              <label class="form-label fw-bold text-secondary small" for="current-password"
                >Contraseña actual</label
              >
              <PasswordInput
                id="current-password"
                v-model="passwords.current"
                autocomplete="current-password"
                required
              />
            </div>
            <div class="col-md-4">
              <label class="form-label fw-bold text-secondary small" for="new-password"
                >Nueva contraseña</label
              >
              <PasswordInput
                id="new-password"
                v-model="passwords.next"
                placeholder="Mínimo 8 caracteres"
                autocomplete="new-password"
                :minlength="MIN_PASSWORD"
                required
              />
            </div>
            <div class="col-md-4">
              <label class="form-label fw-bold text-secondary small" for="confirm-password"
                >Confirmar nueva contraseña</label
              >
              <PasswordInput
                id="confirm-password"
                v-model="passwords.confirm"
                autocomplete="new-password"
                :error="passwordMismatch"
                required
              />
            </div>
          </div>

          <p class="small text-muted mb-0">
            <font-awesome-icon icon="fa-solid fa-circle-info" class="me-1" />
            Al cambiar tu contraseña cerraremos tu sesión en los demás dispositivos.
          </p>

          <div class="mt-4 d-flex justify-content-end">
            <button
              type="submit"
              class="btn btn-brand-save px-5 py-2 shadow-sm rounded-pill fw-medium"
              :disabled="savingPassword || passwordInvalid"
            >
              <span v-if="savingPassword" class="spinner-border spinner-border-sm me-2"></span>
              <font-awesome-icon v-else icon="fa-solid fa-lock" class="me-2" /> Actualizar Contraseña
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Desactivar cuenta -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden danger-zone">
      <div class="card-body p-4 d-flex flex-wrap align-items-center justify-content-between gap-3">
        <div>
          <h6 class="fw-bold text-danger mb-1">
            <font-awesome-icon icon="fa-solid fa-trash-can" class="me-2" /> Desactivar mi cuenta
          </h6>
          <p class="small text-muted mb-0">
            Cerraremos tu sesión y no podrás volver a ingresar con esta cuenta.
          </p>
        </div>
        <button
          type="button"
          class="btn btn-outline-danger rounded-pill px-4"
          :disabled="deactivating"
          @click="deactivateAccount"
        >
          <span v-if="deactivating" class="spinner-border spinner-border-sm me-2"></span>
          Desactivar cuenta
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input-group-text {
  border-color: var(--k-border);
  background-color: var(--k-cream);
}
.form-control {
  border-color: var(--k-border);
}
.form-control:focus {
  border-color: var(--k-apple);
  box-shadow: 0 0 0 0.25rem rgba(139, 207, 91, 0.12);
}
.input-group:focus-within .input-group-text {
  border-color: var(--k-apple);
  color: var(--k-forest);
}
.btn-brand-save {
  background-color: var(--k-forest);
  border: none;
  color: var(--k-cream);
}
.btn-brand-save:hover {
  background-color: var(--k-apple);
  color: var(--k-forest);
}
.danger-zone {
  border: 1px solid var(--k-danger-border) !important;
  background-color: var(--k-danger-soft);
}
</style>
