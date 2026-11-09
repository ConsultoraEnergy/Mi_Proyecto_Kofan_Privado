<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { listNotifications } from "@/api/operations";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const configStore = useConfigStore();

const avisosSinLeer = ref(0);

const revisarNotificaciones = async () => {
  if (!auth.isLogged) return;
  try {
    const avisos = await listNotifications();
    avisosSinLeer.value = avisos.filter((aviso) => !aviso.read).length;
  } catch {
    // El contador es informativo: si falla, simplemente no se muestra.
  }
};

const handleLogout = async () => {
  // Si falla el cierre en el servidor, el store igual limpia la sesión local.
  await auth.logout().catch(() => {});
  router.push("/");
};

onMounted(() => {
  revisarNotificaciones();
  // NotificationsView avisa cuando el usuario marca todo como leído.
  window.addEventListener("notificaciones-leidas", revisarNotificaciones);
});

onUnmounted(() => {
  window.removeEventListener("notificaciones-leidas", revisarNotificaciones);
});

watch(() => route.name, revisarNotificaciones);
</script>

<template>
  <aside class="sidebar-brand shadow-sm">
    <div class="text-center mb-4 mt-2">
      <h6 class="fw-bold text-muted text-uppercase tracking-wider">Menú {{ configStore.hotelName }}</h6>
      <hr class="opacity-10 mx-3">
    </div>

    <nav class="nav flex-column gap-2">
      <router-link :to="{ name: 'account-profile' }" class="nav-link-brand">
        <font-awesome-icon icon="fa-solid fa-id-card" class="me-3 fs-5 icon-brand" /> Mi Panel
      </router-link>

      <router-link :to="{ name: 'account-bookings' }" class="nav-link-brand">
        <font-awesome-icon icon="fa-solid fa-calendar-check" class="me-3 fs-5 icon-brand" /> Mis Reservas
      </router-link>

      <router-link :to="{ name: 'account-notifications' }" class="nav-link-brand d-flex justify-content-between align-items-center">
        <div>
          <font-awesome-icon icon="fa-solid fa-bell" class="me-3 fs-5 icon-brand transition-all" :class="avisosSinLeer > 0 ? 'text-warning' : ''" />
          Todos los Avisos
        </div>
        <span v-if="avisosSinLeer > 0" class="badge bg-warning text-dark rounded-pill shadow-sm">
          {{ avisosSinLeer }}
        </span>
      </router-link>

      <router-link v-if="auth.isStaff" :to="{ name: 'admin-dashboard' }" class="nav-link-brand">
        <font-awesome-icon icon="fa-solid fa-user-shield" class="me-3 fs-5 icon-brand" /> Panel Administrativo
      </router-link>

      <hr class="my-3 opacity-10">

      <router-link to="/" class="nav-link-brand">
        <font-awesome-icon icon="fa-solid fa-house-chimney" class="me-3 fs-5 icon-brand text-success" /> Continuar Navegando
      </router-link>

      <router-link :to="{ name: 'account-settings' }" class="nav-link-brand">
        <font-awesome-icon icon="fa-solid fa-user-gear" class="me-3 fs-5 icon-brand" /> Configuración
      </router-link>

      <a href="#" @click.prevent="handleLogout" class="nav-link-brand logout-link">
        <font-awesome-icon icon="fa-solid fa-right-from-bracket" class="me-3 fs-5 text-danger" /> Salir
      </a>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar-brand {
  background-color: var(--k-offwhite);
  border-radius: 20px;
  padding: 20px;
  border: 1px solid var(--k-border);
  min-height: 50vh;
}

.tracking-wider {
  letter-spacing: 1px;
}

.nav-link-brand {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  text-decoration: none;
  color: #555;
  border-radius: 12px;
  transition: all 0.3s ease;
  font-weight: 600;
}

.nav-link-brand:hover {
  background-color: var(--k-apple-soft);
  color: var(--k-forest);
}

/* Ruta activa */
.router-link-active {
  background-color: rgba(139, 207, 91, 0.16) !important;
  color: var(--k-forest) !important;
  font-weight: 700;
}

.logout-link:hover {
  background-color: var(--k-danger-soft);
  color: var(--k-danger);
}

.transition-all {
  transition: all 0.3s ease;
}
</style>
