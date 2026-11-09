<script setup>
import { useRouter, useRoute } from "vue-router";
import { computed, ref, onMounted, onUnmounted, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import { Collapse } from "bootstrap";
import { useConfigStore } from '@/stores/config';

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const configStore = useConfigStore();
const isScrolled = ref(false);
const handleScroll = () => { isScrolled.value = window.scrollY > 50; };

let bsCollapse = null;
onMounted(() => {
  window.addEventListener("scroll", handleScroll);
  const menuElement = document.getElementById("navbarBrand");
  if (menuElement) bsCollapse = new Collapse(menuElement, { toggle: false });
});

onUnmounted(() => { window.removeEventListener("scroll", handleScroll); });

watch(() => route.path, () => { if (bsCollapse) bsCollapse.hide(); });

const logout = async () => {
  await auth.logout();
  router.push({ name: 'hospedaje-home' });
};

const isAuthRoute = computed(() => {
  return ["login", "register"].includes(String(route.name)) || ["/login", "/register", "/auth/login", "/auth/register", "/hospedaje/rooms"].includes(route.path);
});

const isPublicHospedajeRoute = computed(() => route.path.startsWith("/hospedaje"));

const navbarSolid = computed(() => {
  if (isAuthRoute.value || route.path.startsWith("/app") || route.path.startsWith("/admin")) {
    return true;
  }

  if (isPublicHospedajeRoute.value) {
    return isScrolled.value;
  }

  return isScrolled.value;
});

const navbarClasses = computed(() => {
  if (isAuthRoute.value) return "navbar-dark navbar-solid navbar-auth shadow-sm";
  return navbarSolid.value
    ? "navbar-dark navbar-solid shadow-sm"
    : "navbar-dark bg-transparent";
});
</script>

<template>
  <header
    class="navbar navbar-expand-lg fixed-top transition-navbar"
    :class="navbarClasses"
  >
    <div class="container-fluid px-lg-5">
      <router-link :to="{ name: 'hospedaje-home' }" class="navbar-brand d-flex align-items-center">
      <img
        v-if="configStore.logoUrl"
        :src="configStore.logoUrl"
        :alt="`Logo ${configStore.hotelName}`"
        style="max-height: 50px; object-fit: contain;"
      />
      <span v-else class="brand-name fw-bold fs-4 ms-2 handlee-font">
        {{ configStore.hotelName }}
      </span>
      </router-link>

      <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarBrand">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarBrand">
        <ul class="navbar-nav me-auto ms-4 mb-2 mb-lg-0 fw-medium">
          <li class="nav-item">
            <router-link :to="{ name: 'hospedaje-home' }" class="nav-link" exact-active-class="active-link">Hospedaje</router-link>
          </li>

          <li class="nav-item">
            <router-link :to="{ name: 'about' }" class="nav-link" active-class="active-link">Nosotros</router-link>
          </li>
          <li class="nav-item">
            <router-link :to="{ name: 'gallery' }" class="nav-link" active-class="active-link">Galería</router-link>
          </li>
        </ul>

        <div class="d-lg-flex align-items-center gap-3">
          <div v-if="!auth.isLogged" class="d-flex align-items-center gap-2">
            <router-link :to="{ name: 'login' }" class="nav-link bg-transparent border-0 shadow-none text-white px-3">
            Ingresar
          </router-link>
            <router-link :to="{ name: 'register' }" class="nav-link bg-transparent border-0 shadow-none text-white px-3">
              Registrarse
            </router-link>
          </div>

          <div v-else class="dropdown">
            <button class="btn btn-success dropdown-toggle d-flex align-items-center gap-2 rounded-pill px-3" data-bs-toggle="dropdown">
               <font-awesome-icon :icon="['fas', 'user-circle']" />
               <span>{{ auth.user?.full_name }}</span>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow border-0 mt-2">
              <li>
                <router-link class="dropdown-item" :to="{ name: 'account-profile' }">
                  <font-awesome-icon :icon="['fas', 'id-card']" class="me-2" /> Mi Perfil
                </router-link>
              </li>
              <li v-if="auth.isStaff">
                <router-link class="dropdown-item text-success fw-bold" :to="{ name: 'admin-dashboard' }">
                  <font-awesome-icon :icon="['fas', 'chart-line']" class="me-2" /> Panel Admin
                </router-link>
              </li>
              <li><hr class="dropdown-divider"></li>
              <li><a class="dropdown-item text-danger" href="#" @click.prevent="logout">
                <font-awesome-icon :icon="['fas', 'sign-out-alt']" class="me-2" /> Cerrar Sesión
              </a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.transition-navbar {
  transition: all 0.4s ease-in-out;
  padding: 1rem 0;
}

.navbar-solid,
.bg-brand {
  background-color: var(--k-forest) !important;
}

.bg-transparent {
  background-color: transparent !important;
  box-shadow: none !important;
}

.navbar-auth {
  background-color: var(--k-forest) !important;
  box-shadow: 0 4px 16px rgba(15, 59, 42, 0.18);
}

.navbar-solid {
  padding: 0.5rem 0;
  box-shadow: 0 4px 16px rgba(15, 59, 42, 0.18);
}

.navbar {
  font-family: "Forum", serif;
}

.brand-name,
.handlee-font,
.navbar .btn {
  font-family: "Handlee", cursive;
}

.brand-name,
.nav-link {
  color: var(--k-cream) !important;
}

.nav-link,
.dropdown-item {
  margin: 0 10px;
  position: relative;
  text-decoration: none;
}

.dropdown-menu {
  background: var(--k-cream);
  border: 1px solid rgba(15, 59, 42, 0.12);
}

.dropdown-item {
  color: var(--k-forest-soft) !important;
}

.dropdown-item:hover {
  background: var(--k-sky-soft);
  color: var(--k-forest) !important;
}

.nav-link::after {
  content: '';
  position: absolute;
  width: 0;
  height: 2px;
  bottom: -2px;
  left: 50%;
  background: var(--k-apple);
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.navbar .btn-success,
.navbar .dropdown-toggle {
  background: var(--k-apple);
  border-color: var(--k-apple);
  color: var(--k-forest);
  border-radius: 999px;
  box-shadow: none;
  font-weight: 700;
}

.navbar .btn-success:hover,
.navbar .dropdown-toggle:hover {
  background: var(--k-apple-light);
  border-color: var(--k-apple-light);
}

.nav-link:hover::after { width: 60%; }
.active-link::after { width: 80% !important; }
.active-link { color: var(--k-apple) !important; }

</style>