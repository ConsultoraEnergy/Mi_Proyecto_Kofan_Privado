<template>
  <section class="auth-section d-flex align-items-center justify-content-center">
    <div class="auth-container row g-0">
      <div class="col-md-5 d-none d-md-block auth-image-panel">
        <div class="auth-overlay d-flex flex-column justify-content-end h-100 p-5">
          <p class="eyebrow-text mb-2">{{ configStore.hotelName }}</p>
          <h2 class="titulo-auth mb-2">Bienvenido de vuelta a la calma 🌿</h2>
          <p class="helper-text mb-0">
            Inicia sesión para continuar tu experiencia con serenidad.
          </p>
        </div>
      </div>

      <div class="col-md-7 p-4 p-lg-5 auth-form-panel d-flex flex-column justify-content-center">
        <div class="text-center mb-4">
          <img v-if="configStore.logoUrl" :src="configStore.logoUrl" width="100" :alt="configStore.hotelName" class="auth-logo" />
          <font-awesome-icon v-else icon="fa-solid fa-leaf" class="auth-logo-icon" />
          <h3 class="mt-3 mb-2 auth-heading">Iniciar Sesión</h3>
          <p class="helper-text mb-0">Tu espacio de gestión está listo para recibirte.</p>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label class="form-label auth-label" for="login-email">Correo Electrónico</label>
            <div class="input-group auth-input-group">
              <span class="input-group-text border-end-0"><font-awesome-icon icon="fa-solid fa-envelope" /></span>
              <input
                id="login-email"
                v-model="email"
                type="email"
                class="form-control auth-input border-start-0"
                placeholder="tu correo electrónico"
                autocomplete="email"
                required
              />
            </div>
          </div>

          <div class="mb-2">
            <label class="form-label auth-label" for="login-password">Contraseña</label>
            <div class="input-group auth-input-group">
              <span class="input-group-text border-end-0"><font-awesome-icon icon="fa-solid fa-lock" /></span>
              <input
                id="login-password"
                v-model="password"
                type="password"
                class="form-control auth-input border-start-0"
                placeholder="tu clave serena"
                autocomplete="current-password"
                required
              />
            </div>
          </div>

          <div class="text-end mb-4">
            <router-link :to="{ name: 'forgot-password' }" class="auth-link small">¿Olvidaste tu contraseña?</router-link>
          </div>

          <button
            type="submit"
            class="btn btn-brand auth-button w-100 py-2 mb-3"
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
            {{ isLoading ? "Entrando..." : "Ingresar" }}
          </button>
        </form>

        <p class="text-center mt-3 helper-text">
          ¿No tienes cuenta?
          <router-link :to="{ name: 'register' }" class="auth-link">Regístrate aquí</router-link>
        </p>
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

.auth-container {
  width: 100%;
  max-width: 920px;
  border-radius: 22px;
  overflow: hidden;
  background: var(--k-cream) !important;
  border: 1px solid var(--k-border);
  box-shadow: 0 12px 30px rgba(15, 59, 42, 0.08);
}

.auth-image-panel {
  background: url("@/img/portadaimg2.jpg") center/cover;
  position: relative;
  min-height: 540px;
}

.auth-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 59, 42, 0.48);
  color: var(--k-cream);
}

.eyebrow-text,
.helper-text,
.auth-button,
.auth-link,
.auth-input::placeholder {
  font-family: "Handlee", cursive;
}

.titulo-auth,
.auth-heading,
.auth-label {
  font-family: "Forum", serif;
}

.titulo-auth {
  font-size: 2.3rem;
  color: var(--k-cream);
}

.auth-heading {
  font-size: 2rem;
  color: var(--k-forest);
}

.auth-label {
  color: var(--k-forest);
  font-size: 1rem;
}

.auth-form-panel {
  background: var(--k-cream);
}

.auth-input-group .input-group-text,
.auth-input {
  background: var(--k-cream);
  border-color: var(--k-border);
  color: var(--k-forest);
}

.auth-input {
  font-family: "Handlee", cursive;
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
  background: var(--k-forest) !important;
  border-color: var(--k-forest) !important;
  color: var(--k-cream) !important;
  border-radius: 999px !important;
  box-shadow: none;
  font-weight: 700;
}

.auth-button:hover {
  background: var(--k-apple) !important;
  border-color: var(--k-apple) !important;
  color: var(--k-forest) !important;
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(139, 207, 91, 0.18);
}

.auth-link {
  color: var(--k-forest);
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}

.auth-logo {
  max-height: 100px;
  object-fit: contain;
}

.auth-logo-icon {
  font-size: 3rem;
  color: var(--k-forest);
}
</style>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import Swal from "sweetalert2";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { errorMessage } from "@/api/apiClient";

const auth = useAuthStore();
const configStore = useConfigStore();
const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const isLoading = ref(false);

/** Solo se aceptan rutas internas ("/app/...") para evitar redirecciones abiertas. */
const safeRedirect = () => {
  const target = route.query.redirect;
  return typeof target === "string" && target.startsWith("/") && !target.startsWith("//") ? target : null;
};

const handleLogin = async () => {
  if (!email.value || !password.value) {
    Swal.fire("Atención", "Por favor completa todos los campos", "warning");
    return;
  }

  isLoading.value = true;
  try {
    const user = await auth.login(email.value, password.value);

    Swal.fire({
      icon: "success",
      title: `¡Bienvenido, ${user.full_name}!`,
      text: "Acceso concedido al paraíso.",
      timer: 2000,
      showConfirmButton: false,
    });

    router.push(safeRedirect() || auth.homeRoute());
  } catch (error) {
    Swal.fire("Error de Acceso", errorMessage(error, "Correo o contraseña incorrectos"), "error");
  } finally {
    isLoading.value = false;
  }
};
</script>
