<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import Swal from "sweetalert2";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { register } from "@/api/auth";
import { errorMessage } from "@/api/apiClient";
import FormularioRegistro from "@/components/FormularioRegistro.vue";

const auth = useAuthStore();
const configStore = useConfigStore();
const router = useRouter();
const isLoading = ref(false);

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");

/** Recibe el formulario (ya con los nombres de la API) y crea la cuenta. */
const registrarCliente = async (datos) => {
  isLoading.value = true;

  try {
    await register({
      email: datos.email,
      password: datos.password,
      full_name: datos.full_name,
      person_type: datos.person_type,
      document_type: datos.document_type,
      document_number: datos.document_number,
      phone: datos.phone,
      country: datos.country,
      city: datos.city,
      accept_privacy_policy: datos.accept_privacy_policy === true,
    });
  } catch (error) {
    const duplicated = error.response?.status === 409;
    Swal.fire({
      icon: duplicated ? "warning" : "error",
      title: duplicated ? "Datos ya registrados" : "Error al registrarse",
      text: errorMessage(error, "No pudimos crear tu cuenta. Por favor intenta de nuevo."),
      confirmButtonColor: COLOR_FOREST,
    });
    isLoading.value = false;
    return;
  }

  try {
    await auth.login(datos.email, datos.password);
    await Swal.fire({
      icon: "success",
      title: `¡Bienvenido a ${configStore.hotelName}!`,
      html:
        `Hola ${escapeHtml(datos.full_name)}, tu cuenta ha sido creada con éxito.<br><br>` +
        "Te enviamos un enlace para verificar tu correo; al verificarlo vincularemos las reservas que hayas hecho como invitado.",
      confirmButtonColor: COLOR_FOREST,
    });
    router.push(auth.homeRoute());
  } catch (error) {
    // La cuenta existe, pero no se pudo iniciar sesión automáticamente.
    await Swal.fire({
      icon: "info",
      title: "Cuenta creada",
      text: "Revisa tu correo para verificar tu cuenta e inicia sesión para continuar.",
      confirmButtonColor: COLOR_FOREST,
    });
    router.push({ name: "login" });
  } finally {
    isLoading.value = false;
  }
};

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
</script>

<template>
  <main class="auth-page py-5 mt-3">
    <div class="container d-flex justify-content-center">
      <div class="register-card row g-0">

        <div class="col-lg-4 d-none d-lg-flex flex-column justify-content-between p-4 p-xl-5 sidebar-brand">
          <div>
            <p class="sidebar-kicker mb-2">Comunidad {{ configStore.hotelName }}</p>
            <h2 class="sidebar-title">Únete a nuestra comunidad y gestiona con armonía</h2>
            <p class="sidebar-copy mb-0">Crea tu cuenta para organizar cada experiencia con calma y claridad.</p>
          </div>

          <div class="text-center mt-auto pb-3">
            <img
              v-if="configStore.logoUrl"
              :src="configStore.logoUrl"
              :alt="`Logo ${configStore.hotelName}`"
              class="img-fluid opacity-75 brand-logo-sidebar"
            />
            <font-awesome-icon v-else icon="fa-solid fa-leaf" class="brand-icon-sidebar" />
          </div>
        </div>

        <div class="col-lg-8 p-4 p-md-5 form-panel">
          <div class="text-center mb-4">
            <h2 class="register-title mb-2">Crear Cuenta</h2>
            <p class="register-copy mb-0">Tu acceso a {{ configStore.hotelName }} comienza aquí.</p>
          </div>

          <FormularioRegistro
            :mostrarRol="false"
            :cargando="isLoading"
            @enviar="registrarCliente"
          />

          <div class="col-12 text-center mt-3">
            <p class="helper-copy mb-0">
              ¿Ya tienes una cuenta?
              <router-link :to="{ name: 'login' }" class="auth-link text-decoration-none">Inicia Sesión</router-link>
            </p>
          </div>

        </div>

      </div>
    </div>
  </main>
</template>

<style scoped>
.auth-page {
  background-color: var(--k-cream);
  min-height: 100vh;
  color: var(--k-forest);
}

.register-card {
  border-radius: 22px;
  overflow: hidden;
  max-width: 950px;
  width: 100%;
  background: var(--k-cream) !important;
  border: 1px solid var(--k-border);
  box-shadow: 0 12px 30px rgba(15, 59, 42, 0.08);
}

.sidebar-brand {
  background-color: var(--k-sky-soft);
  color: var(--k-forest);
  border-right: 1px solid rgba(52, 152, 219, 0.16);
}

.sidebar-title,
.register-title,
:deep(.form-label) {
  font-family: "Forum", serif;
  color: var(--k-forest) !important;
}

.sidebar-kicker,
.sidebar-copy,
.register-copy,
.helper-copy,
.auth-link,
:deep(.custom-input),
:deep(.custom-input::placeholder),
:deep(.form-control::placeholder),
:deep(.form-select),
:deep(.invalid-feedback),
:deep(.btn-brand),
:deep(.input-group-text) {
  font-family: "Handlee", cursive;
}

.brand-logo-sidebar {
  max-height: 220px;
  object-fit: contain;
}

.brand-icon-sidebar {
  font-size: 6rem;
  color: var(--k-forest);
  opacity: 0.5;
}

.form-panel {
  background: var(--k-cream);
}

.sidebar-title {
  font-size: 2rem;
  line-height: 1.15;
}

.register-title {
  font-size: 2.1rem;
}

.sidebar-copy,
.register-copy,
.helper-copy {
  color: var(--k-muted);
}

.auth-link {
  color: var(--k-forest);
}

:deep(.custom-input),
:deep(.form-control),
:deep(.form-select),
:deep(.input-group-text) {
  background-color: var(--k-cream) !important;
  border-color: var(--k-border) !important;
  color: var(--k-forest) !important;
  border-radius: 18px !important;
}

:deep(.form-control:focus),
:deep(.form-select:focus) {
  border-color: var(--k-apple) !important;
  box-shadow: 0 0 0 0.18rem rgba(139, 207, 91, 0.18) !important;
}

:deep(.custom-input::placeholder),
:deep(.form-control::placeholder) {
  color: rgba(15, 59, 42, 0.58) !important;
  opacity: 1;
}

:deep(.btn-brand) {
  background-color: var(--k-forest) !important;
  border-color: var(--k-forest) !important;
  color: var(--k-cream) !important;
  border-radius: 999px !important;
  box-shadow: none !important;
  font-weight: 700;
}

:deep(.btn-brand:hover) {
  background-color: var(--k-apple) !important;
  border-color: var(--k-apple) !important;
  color: var(--k-forest) !important;
}

:deep(.btn-brand:disabled) {
  background-color: rgba(139, 207, 91, 0.65) !important;
  border-color: rgba(139, 207, 91, 0.65) !important;
  opacity: 1;
}

:deep(.invalid-feedback) {
  font-size: 0.85rem;
}

:deep(.custom-input-p .input-group) {
  border-radius: 18px !important;
  overflow: hidden !important;
}

:deep(.custom-input-p .form-control) {
  border-radius: 18px 0 0 18px !important;
}

:deep(.custom-input-p .input-group-text) {
  border-radius: 0 18px 18px 0 !important;
}
</style>