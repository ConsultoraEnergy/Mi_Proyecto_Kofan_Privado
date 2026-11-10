<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { PERMISSIONS } from "@/constants/booking";
import AdminHeader from "@/views/admin/AdminHeader.vue";

const auth = useAuthStore();
const configStore = useConfigStore();
const router = useRouter();

const operationLinks = [
  {
    name: "admin-dashboard",
    label: "Inicio",
    icon: "fa-solid fa-seedling",
    permission: PERMISSIONS.DASHBOARD_READ,
  },
  {
    name: "admin-bookings",
    label: "Reservas",
    icon: "fa-solid fa-calendar-check",
    permission: PERMISSIONS.BOOKINGS_READ_ALL,
  },
  {
    name: "admin-rooms",
    label: "Habitaciones",
    icon: "fa-solid fa-bed",
    permission: PERMISSIONS.ROOMS_READ_ALL,
  },
  { name: "admin-users", label: "Usuarios", icon: "fa-solid fa-users", permission: PERMISSIONS.USERS_READ },
];

const supportLinks = [
  {
    name: "admin-gallery",
    label: "Galería",
    icon: "fa-solid fa-images",
    permission: PERMISSIONS.GALLERY_WRITE,
  },
  {
    name: "admin-config",
    label: "Configuración",
    icon: "fa-solid fa-hotel",
    permission: PERMISSIONS.SETTINGS_WRITE,
  },
];

const visibleOperation = computed(() => operationLinks.filter((l) => auth.can(l.permission)));
const visibleSupport = computed(() => supportLinks.filter((l) => auth.can(l.permission)));

const handleLogout = async () => {
  await auth.logout();
  router.push({ name: "hospedaje-home" });
};

onMounted(() => {
  configStore.fetchSiteConfig();
});
</script>

<template>
  <div class="admin-wrapper d-flex">
    <aside class="admin-sidebar p-3 shadow-sm">
      <div class="text-center mb-4 sidebar-brand">
        <img
          v-if="configStore.logoUrl"
          :src="configStore.logoUrl"
          width="150"
          alt="Logo"
          class="brand-logo"
        />
        <p class="brand-handmade mt-2 mb-1 text-white">Hospitalidad Serena</p>
        <h5 class="section-title mb-0 text-white">{{ configStore.hotelName }} Admin</h5>
      </div>

      <nav class="nav flex-column gap-2">
        <small v-if="visibleOperation.length" class="nav-group-label">Operación diaria</small>

        <router-link
          v-for="link in visibleOperation"
          :key="link.name"
          :to="{ name: link.name }"
          class="nav-link-admin"
        >
          <font-awesome-icon :icon="link.icon" class="me-2" /> <span>{{ link.label }}</span>
        </router-link>

        <small v-if="visibleSupport.length" class="nav-group-label mt-3">Apoyo y ajustes</small>

        <router-link
          v-for="link in visibleSupport"
          :key="link.name"
          :to="{ name: link.name }"
          class="nav-link-admin"
        >
          <font-awesome-icon :icon="link.icon" class="me-2" /> <span>{{ link.label }}</span>
        </router-link>

        <button class="btn btn-logout-soft w-100 mt-3 shadow-sm" @click="handleLogout">
          <font-awesome-icon icon="fa-solid fa-right-from-bracket" class="me-2" /> <span>Salir</span>
        </button>
      </nav>
    </aside>

    <div class="main-container flex-grow-1">
      <AdminHeader />

      <main class="admin-main-content p-4 p-lg-4">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-wrapper {
  min-height: 100vh;
  background-color: var(--k-cream);
  overflow-x: hidden;
}

.admin-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 272px;
  height: 100vh;
  overflow-y: auto;
  z-index: 1030;
  background: linear-gradient(180deg, var(--k-forest) 0%, var(--k-forest-soft) 100%);
  border-right: 1px solid rgba(255, 252, 248, 0.08);
}

.brand-logo {
  filter: drop-shadow(0 8px 18px rgba(15, 59, 42, 0.18));
}

/* Evita que el contenido quede bajo la barra lateral */
.main-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0;
  margin-left: 272px;
  width: calc(100% - 272px);
  background: var(--k-offwhite);
  scrollbar-gutter: stable;
}

.admin-main-content {
  flex: 1;
  width: 100%;
  min-width: 0;
}

.nav {
  color: var(--k-cream);
}

.nav-group-label {
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 252, 248, 0.7);
  padding: 0 0.45rem;
}

.nav-link-admin {
  color: rgba(255, 252, 248, 0.92);
  text-decoration: none;
  padding: 12px 15px;
  border-radius: 14px;
  transition: all 0.3s ease;
  font-weight: 500;
  border: 1px solid transparent;
}

.nav-link-admin:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--k-cream);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 10px 22px rgba(15, 59, 42, 0.12);
  transform: translateX(2px);
}

.router-link-active {
  background: var(--k-apple-soft) !important;
  color: var(--k-forest) !important;
  border-color: rgba(139, 207, 91, 0.55);
  box-shadow: 0 8px 20px rgba(139, 207, 91, 0.18);
}

.page-intro {
  padding-left: 0.25rem;
}

.btn-logout-soft {
  background-color: var(--k-danger-soft);
  color: var(--k-danger);
  border: 1px solid var(--k-danger-border);
  font-family: "Handlee", cursive;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-logout-soft:hover {
  background-color: var(--k-danger-strong);
  color: var(--k-offwhite);
  border-color: var(--k-danger);
  box-shadow: 0 4px 12px rgba(224, 49, 49, 0.25) !important;
}

.btn-logout-soft:hover :deep(svg) {
  transform: translateX(3px);
  transition: transform 0.2s ease;
}

@media (max-width: 768px) {
  .admin-sidebar {
    width: 88px;
  }

  .main-container {
    margin-left: 88px;
    width: calc(100% - 88px);
  }

  .admin-sidebar span,
  .admin-sidebar h5,
  .admin-sidebar .brand-handmade,
  .nav-group-label {
    display: none;
  }

  .nav-link-admin {
    text-align: center;
    padding: 15px;
  }

  .nav-link-admin :deep(svg) {
    margin: 0 !important;
    font-size: 1.2rem;
  }
}
</style>
