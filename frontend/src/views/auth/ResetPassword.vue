<script setup>
/**
 * Restablecer contraseña. También la usan las cuentas creadas por recepción para definir su
 * primera contraseña (el enlace del correo trae el token).
 */
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import { resetPassword } from "@/api/auth";
import { errorMessage } from "@/api/apiClient";
import { useConfigStore } from "@/stores/config";
import PasswordInput from "@/components/form/PasswordInput.vue";

const MIN_PASSWORD = 8;

const route = useRoute();
const configStore = useConfigStore();

const token = computed(() => (typeof route.query.token === "string" ? route.query.token : ""));
const password = ref("");
const confirmPassword = ref("");
const isLoading = ref(false);
const done = ref(false);
const successMessage = ref("");
const error = ref("");

const mismatch = computed(() =>
  confirmPassword.value && password.value !== confirmPassword.value ? "Las contraseñas no coinciden" : "",
);
const isInvalid = computed(
  () => password.value.length < MIN_PASSWORD || password.value !== confirmPassword.value,
);

const submit = async () => {
  if (isInvalid.value) return;
  isLoading.value = true;
  error.value = "";
  try {
    const result = await resetPassword(token.value, password.value);
    successMessage.value = result?.message || "Contraseña actualizada. Ya puedes iniciar sesión.";
    done.value = true;
  } catch (err) {
    error.value = errorMessage(err, "No pudimos actualizar tu contraseña. El enlace puede haber vencido.");
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <section class="auth-section d-flex align-items-center justify-content-center">
    <div class="auth-card p-4 p-lg-5">
      <div class="text-center mb-4">
        <img
          v-if="configStore.logoUrl"
          :src="configStore.logoUrl"
          width="90"
          :alt="configStore.hotelName"
          class="auth-logo"
        />
        <font-awesome-icon v-else icon="fa-solid fa-leaf" class="auth-logo-icon" />
        <h3 class="mt-3 mb-2 auth-heading">Define tu nueva contraseña</h3>
        <p class="helper-text mb-0">Elige una contraseña segura de al menos 8 caracteres.</p>
      </div>

      <div v-if="!token" class="text-center">
        <font-awesome-icon icon="fa-solid fa-circle-info" class="status-icon text-danger mb-3" />
        <p class="mb-3">El enlace no es válido o está incompleto.</p>
        <router-link :to="{ name: 'forgot-password' }" class="btn btn-brand auth-button px-4 py-2">
          Solicitar un nuevo enlace
        </router-link>
      </div>

      <div v-else-if="done" class="text-center">
        <font-awesome-icon icon="fa-solid fa-circle-check" class="status-icon text-success mb-3" />
        <p class="mb-4">{{ successMessage }}</p>
        <router-link :to="{ name: 'login' }" class="btn btn-brand auth-button w-100 py-2"
          >Iniciar sesión</router-link
        >
      </div>

      <form v-else @submit.prevent="submit">
        <div class="mb-3">
          <label class="form-label auth-label" for="reset-password">Nueva contraseña</label>
          <PasswordInput
            id="reset-password"
            v-model="password"
            placeholder="Mínimo 8 caracteres"
            autocomplete="new-password"
            :minlength="MIN_PASSWORD"
            required
          />
        </div>

        <div class="mb-4">
          <label class="form-label auth-label" for="reset-password-confirm">Confirmar contraseña</label>
          <PasswordInput
            id="reset-password-confirm"
            v-model="confirmPassword"
            placeholder="Repite la contraseña"
            autocomplete="new-password"
            :error="mismatch"
            required
          />
        </div>

        <div v-if="error" class="alert alert-danger small py-2">
          {{ error }}
          <router-link :to="{ name: 'forgot-password' }" class="alert-link d-block mt-1">
            Solicitar un nuevo enlace
          </router-link>
        </div>

        <button type="submit" class="btn btn-brand auth-button w-100 py-2" :disabled="isLoading || isInvalid">
          <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
          {{ isLoading ? "Guardando..." : "Guardar contraseña" }}
        </button>
      </form>

      <p v-if="!done" class="text-center mt-4 mb-0 helper-text">
        <router-link :to="{ name: 'login' }" class="auth-link">
          <font-awesome-icon icon="fa-solid fa-arrow-left" class="me-1" /> Volver a iniciar sesión
        </router-link>
      </p>
    </div>
  </section>
</template>

<style scoped>
.auth-section {
  min-height: 100vh;
  background: var(--k-cream);
  padding: 16px;
  color: var(--k-forest);
}

.auth-card {
  width: 100%;
  max-width: 520px;
  border-radius: 22px;
  background: var(--k-cream);
  border: 1px solid var(--k-border);
  box-shadow: 0 12px 30px rgba(15, 59, 42, 0.08);
}

.auth-logo {
  max-height: 90px;
  object-fit: contain;
}

.auth-logo-icon {
  font-size: 3rem;
  color: var(--k-forest);
}

.helper-text,
.auth-button,
.auth-link,
:deep(.custom-input::placeholder) {
  font-family: "Handlee", cursive;
}

.helper-text {
  color: var(--k-muted);
}

.auth-heading,
.auth-label {
  font-family: "Forum", serif;
  color: var(--k-forest);
}

.auth-heading {
  font-size: 2rem;
}

:deep(.custom-input),
:deep(.input-group-text) {
  background: var(--k-cream) !important;
  border-color: var(--k-border) !important;
  color: var(--k-forest);
}

:deep(.custom-input:focus) {
  border-color: var(--k-apple) !important;
}

.auth-button {
  border-radius: 999px !important;
  font-weight: 700;
}

.auth-link {
  color: var(--k-forest);
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}

.status-icon {
  font-size: 3.5rem;
}
</style>
