<script setup>
import { computed, ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";
import Swal from "sweetalert2";
import { ROLE_LABELS } from "@/constants/booking";
import ActivityNotificationsModal from "@/components/ActivityNotificationsModal.vue";
import { brandColor } from "@/utils/brandColors";

const auth = useAuthStore();
const router = useRouter();

const roleLabel = computed(() => ROLE_LABELS[auth.user?.role] || "");
const showNotifications = ref(false);

const COLOR_APPLE = brandColor("--k-apple", "#8BCF5B");
const COLOR_FOREST = brandColor("--k-forest", "#0f3b2a");

const handleLogout = async () => {
  const result = await Swal.fire({
    title: "¿Deseas cerrar tu jornada por ahora?",
    text: "Podrás volver a entrar cuando lo necesites.",
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: COLOR_APPLE,
    cancelButtonColor: COLOR_FOREST,
    confirmButtonText: "Sí, salir por ahora",
    cancelButtonText: "Seguir aquí",
  });
  if (result.isConfirmed) {
    await auth.logout();
    router.push({ name: "hospedaje-home" });
  }
};
</script>

<template>
  <header class="admin-header d-flex align-items-center justify-content-between px-4">
    <div class="header-left d-flex align-items-center gap-3">
      <button class="btn btn-soft-sky d-md-none me-1">
        <font-awesome-icon icon="fa-solid fa-filter" />
      </button>
    </div>
    <div class="header-right d-flex align-items-center gap-3">
      <button
        type="button"
        class="btn btn-sm btn-light rounded-circle shadow-sm"
        title="Mis avisos"
        @click="showNotifications = true"
      >
        <font-awesome-icon icon="fa-solid fa-bell" />
      </button>

      <div class="user-profile d-none d-sm-flex align-items-center">
        <div class="user-info text-end me-2">
          <p class="mb-0 fw-bold lh-1 text-white">{{ auth.user?.full_name }}</p>
          <small class="text-white">{{ roleLabel }}</small>
        </div>
        <div class="avatar-circle">
          {{ auth.user?.full_name?.charAt(0) }}
        </div>
      </div>

      <div class="vertical-divider"></div>

      <button class="btn btn-logout-soft-sm btn-sm px-3 shadow-sm" @click="handleLogout">
        <font-awesome-icon icon="fa-solid fa-right-from-bracket" class="me-1" /> Salir
      </button>
    </div>

    <ActivityNotificationsModal :show="showNotifications" @close="showNotifications = false" />
  </header>
</template>

<style scoped>
.admin-header {
  position: sticky;
  top: 0;
  z-index: 1025;
  min-height: 78px;
  width: 100%;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--k-forest) 0%, var(--k-apple) 62%, var(--k-forest) 100%);
  backdrop-filter: blur(4px);
  box-shadow: 0 10px 24px rgba(15, 59, 42, 0.12);
  border-bottom: 1px solid rgba(255, 252, 248, 0.14);
}

.avatar-circle {
  width: 40px;
  height: 40px;
  background: var(--k-forest);
  color: var(--k-offwhite);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  box-shadow: 0 8px 18px rgba(139, 207, 91, 0.24);
}

.vertical-divider {
  width: 1px;
  height: 30px;
  background-color: rgba(255, 252, 248, 0.4);
  margin: 0 4px;
}

.lh-1 {
  line-height: 1;
}

.btn-logout-soft-sm {
  background-color: var(--k-danger-soft);
  color: var(--k-danger);
  border: 1px solid var(--k-danger-border);
  font-family: "Handlee", cursive;
  font-weight: 600;
  transition: all 0.25s ease;
  display: inline-flex;
  align-items: center;
}

.btn-logout-soft-sm:hover {
  background-color: var(--k-danger-strong);
  color: var(--k-offwhite);
  border-color: var(--k-danger);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(250, 82, 82, 0.2) !important;
}

.btn-logout-soft-sm:hover :deep(svg) {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}
</style>
