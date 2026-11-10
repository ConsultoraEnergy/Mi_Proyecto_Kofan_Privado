<script setup>
import { ref } from "vue";
import { forgotPassword } from "@/api/auth";
import { errorMessage } from "@/api/apiClient";
import { useConfigStore } from "@/stores/config";

const configStore = useConfigStore();

const NEUTRAL_MESSAGE = "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.";

const email = ref("");
const isLoading = ref(false);
const sentMessage = ref("");
const error = ref("");

const submit = async () => {
  if (!email.value.trim()) return;
  isLoading.value = true;
  error.value = "";
  try {
    const result = await forgotPassword(email.value.trim());
    sentMessage.value = result?.message || NEUTRAL_MESSAGE;
  } catch (err) {
    error.value = errorMessage(err, "No pudimos procesar tu solicitud. Intenta de nuevo.");
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
        <h3 class="mt-3 mb-2 auth-heading">¿Olvidaste tu contraseña?</h3>
        <p class="helper-text mb-0">Escribe tu correo y te enviaremos un enlace para crear una nueva.</p>
      </div>

      <div v-if="sentMessage" class="text-center">
        <font-awesome-icon icon="fa-solid fa-paper-plane" class="status-icon text-success mb-3" />
        <p class="mb-2">{{ sentMessage }}</p>
        <p class="helper-text small mb-0">Revisa también tu carpeta de correo no deseado.</p>
      </div>

      <form v-else @submit.prevent="submit">
        <div class="mb-4">
          <label class="form-label auth-label" for="forgot-email">Correo Electrónico</label>
          <div class="input-group auth-input-group">
            <span class="input-group-text border-end-0"
              ><font-awesome-icon icon="fa-solid fa-envelope"
            /></span>
            <input
              id="forgot-email"
              v-model="email"
              type="email"
              class="form-control auth-input border-start-0"
              placeholder="tu correo electrónico"
              autocomplete="email"
              required
            />
          </div>
        </div>

        <div v-if="error" class="alert alert-danger small py-2">{{ error }}</div>

        <button type="submit" class="btn btn-brand auth-button w-100 py-2" :disabled="isLoading">
          <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
          {{ isLoading ? "Enviando..." : "Enviar enlace" }}
        </button>
      </form>

      <p class="text-center mt-4 mb-0 helper-text">
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
.auth-input,
.auth-input::placeholder {
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

.auth-input-group .input-group-text,
.auth-input {
  background: var(--k-cream);
  border-color: var(--k-border);
  color: var(--k-forest);
}

.auth-input:focus {
  border-color: var(--k-apple);
  box-shadow: 0 0 0 0.18rem rgba(139, 207, 91, 0.18);
}

.auth-input::placeholder {
  color: rgba(15, 59, 42, 0.58);
  opacity: 1;
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
