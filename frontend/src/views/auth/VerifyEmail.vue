<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { verifyEmail } from "@/api/auth";
import { errorMessage } from "@/api/apiClient";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";

const route = useRoute();
const auth = useAuthStore();
const configStore = useConfigStore();

const status = ref("loading"); // loading | success | error
const message = ref("");
const linkedBookings = ref(0);

onMounted(async () => {
  const token = typeof route.query.token === "string" ? route.query.token : "";
  if (!token) {
    status.value = "error";
    message.value = "El enlace de verificación no es válido. Revisa que lo hayas copiado completo.";
    return;
  }
  try {
    const result = await verifyEmail(token);
    linkedBookings.value = result.linked_bookings || 0;
    message.value = result.message || "¡Correo verificado!";
    status.value = "success";
    if (auth.isLogged) auth.updateUser({ email_verified: true });
  } catch (error) {
    message.value = errorMessage(error, "No pudimos verificar tu correo. El enlace puede haber vencido.");
    status.value = "error";
  }
});
</script>

<template>
  <section class="auth-section d-flex align-items-center justify-content-center">
    <div class="auth-card p-4 p-lg-5">
      <div class="text-center mb-4">
        <img v-if="configStore.logoUrl" :src="configStore.logoUrl" width="90" :alt="configStore.hotelName" class="auth-logo" />
        <font-awesome-icon v-else icon="fa-solid fa-leaf" class="auth-logo-icon" />
        <h3 class="mt-3 mb-2 auth-heading">Verificación de correo</h3>
        <p class="helper-text mb-0">Confirmamos que este correo te pertenece.</p>
      </div>

      <div v-if="status === 'loading'" class="text-center py-4">
        <span class="spinner-border text-success" role="status"></span>
        <p class="helper-text mt-3 mb-0">Verificando tu correo...</p>
      </div>

      <div v-else-if="status === 'success'" class="text-center">
        <font-awesome-icon icon="fa-solid fa-circle-check" class="status-icon text-success mb-3" />
        <h5 class="fw-bold mb-2">{{ message }}</h5>
        <p v-if="linkedBookings > 0" class="helper-text mb-0">
          Vinculamos {{ linkedBookings }} {{ linkedBookings === 1 ? "reserva" : "reservas" }} que habías hecho como
          invitado a tu cuenta.
        </p>
      </div>

      <div v-else class="text-center">
        <font-awesome-icon icon="fa-solid fa-circle-info" class="status-icon text-danger mb-3" />
        <h5 class="fw-bold mb-2">No pudimos verificar tu correo</h5>
        <p class="helper-text mb-0">{{ message }}</p>
        <p v-if="auth.isLogged" class="helper-text mt-2 mb-0">
          Puedes solicitar un nuevo enlace desde tu cuenta.
        </p>
      </div>

      <div v-if="status !== 'loading'" class="d-grid gap-2 mt-4">
        <router-link v-if="auth.isLogged" :to="auth.homeRoute()" class="btn btn-brand auth-button py-2">
          Ir a mi cuenta
        </router-link>
        <router-link v-else :to="{ name: 'login' }" class="btn btn-brand auth-button py-2">
          Iniciar sesión
        </router-link>
      </div>
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
.auth-button {
  font-family: "Handlee", cursive;
}

.helper-text {
  color: var(--k-muted);
}

.auth-heading {
  font-family: "Forum", serif;
  color: var(--k-forest);
  font-size: 2rem;
}

.auth-button {
  border-radius: 999px !important;
  font-weight: 700;
}

.status-icon {
  font-size: 3.5rem;
}
</style>
