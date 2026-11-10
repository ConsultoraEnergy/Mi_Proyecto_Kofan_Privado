<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { listNotifications } from "@/api/operations";
import { ROLE_LABELS } from "@/constants/booking";
import { formatDateTime } from "@/utils/format";

const auth = useAuthStore();
const configStore = useConfigStore();

const user = computed(() => auth.user || {});
const roleLabel = computed(() =>
  user.value.role === "client"
    ? `Cliente ${configStore.hotelName}`
    : ROLE_LABELS[user.value.role] || "Cliente",
);
const documentLabel = computed(() =>
  user.value.document_number ? `${user.value.document_type || ""} ${user.value.document_number}`.trim() : "",
);
const location = computed(() => [user.value.city, user.value.country].filter(Boolean).join(", "));

// Los 2 avisos más recientes
const avisosRecientes = ref([]);

const cargarAvisosRecientes = async () => {
  try {
    avisosRecientes.value = (await listNotifications()).slice(0, 2);
  } catch {
    avisosRecientes.value = [];
  }
};

/** El backend envía nombres de Bootstrap Icons (bi-...); aquí se traducen a FontAwesome. */
const resolverIconoAviso = (icono) => {
  const valor = String(icono || "").toLowerCase();
  if (valor.includes("check")) return "fa-solid fa-circle-check";
  if (valor.includes("exclamation") || valor.includes("info")) return "fa-solid fa-circle-info";
  if (valor.includes("house") || valor.includes("door")) return "fa-solid fa-house-chimney";
  if (valor.includes("x-circle") || valor.includes("ban") || valor.includes("cancel"))
    return "fa-solid fa-ban";
  return "fa-solid fa-bell";
};

const theme = (aviso) => aviso.theme || "primary";

onMounted(cargarAvisosRecientes);
</script>

<template>
  <div class="perfil-section">
    <div class="mb-4">
      <h3 class="fw-bold text-dark mb-1">Mi Panel</h3>
      <p class="text-muted small mb-0">Resumen de tu cuenta y alertas recientes</p>
    </div>

    <div class="card border-0 shadow-sm rounded-4 mb-4 overflow-hidden position-relative tarjeta-brand-suave">
      <div class="card-body p-4 p-md-5 position-relative z-1">
        <span
          class="badge bg-white text-success rounded-pill mb-3 px-3 py-2 shadow-sm border border-success-subtle"
        >
          <font-awesome-icon icon="fa-solid fa-star" class="text-warning me-1" /> {{ roleLabel }}
        </span>
        <h3 class="fw-bold mb-2 verde-brand">{{ user.full_name || "Mi cuenta" }}</h3>

        <div class="d-flex flex-wrap gap-4 mt-3 verde-brand opacity-75 fw-medium">
          <span>
            <font-awesome-icon icon="fa-solid fa-envelope" class="me-2" /> {{ user.email }}
            <span v-if="user.email_verified" class="badge bg-success-subtle text-success ms-1"
              >Verificado</span
            >
            <span v-else class="badge bg-warning-subtle text-warning-emphasis ms-1">Sin verificar</span>
          </span>
          <span v-if="documentLabel"
            ><font-awesome-icon icon="fa-solid fa-id-card" class="me-2" /> {{ documentLabel }}</span
          >
          <span v-if="user.phone"
            ><font-awesome-icon icon="fa-solid fa-phone" class="me-2" /> {{ user.phone }}</span
          >
          <span v-if="location"
            ><font-awesome-icon icon="fa-solid fa-location-dot" class="me-2" /> {{ location }}</span
          >
        </div>
      </div>
    </div>

    <div class="mt-5">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="fw-bold text-dark">
          <font-awesome-icon icon="fa-solid fa-bell" class="text-muted me-2" /> Avisos Recientes
        </h5>
        <router-link
          :to="{ name: 'account-notifications' }"
          class="btn btn-sm btn-link text-decoration-none text-success fw-bold"
        >
          Ver todos
        </router-link>
      </div>

      <div class="d-flex flex-column gap-3">
        <div v-if="avisosRecientes.length === 0" class="text-center py-4 bg-white rounded-4 shadow-sm border">
          <font-awesome-icon icon="fa-solid fa-bell-slash" class="text-muted fs-1 mb-2 d-block mx-auto" />
          <p class="text-muted small mb-0">No tienes alertas nuevas.</p>
        </div>

        <div
          v-for="aviso in avisosRecientes"
          :key="aviso.id"
          class="card border-0 shadow-sm rounded-4 aviso-card"
          :class="`border-start border-4 border-${theme(aviso)}`"
        >
          <div class="card-body p-3 d-flex align-items-center gap-3">
            <div
              class="rounded-3 d-flex align-items-center justify-content-center flex-shrink-0"
              :class="`bg-${theme(aviso)} bg-opacity-10 text-${theme(aviso)}`"
              style="width: 45px; height: 45px"
            >
              <font-awesome-icon :icon="resolverIconoAviso(aviso.icon)" class="fs-5" />
            </div>
            <div class="flex-grow-1">
              <div class="d-flex justify-content-between align-items-center gap-2">
                <h6 class="fw-bold mb-0 text-dark">{{ aviso.title }}</h6>
                <small class="text-muted text-nowrap">{{ formatDateTime(aviso.created_at) }}</small>
              </div>
              <p class="mb-0 text-secondary small">{{ aviso.message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Fondo verde suave de la tarjeta de perfil */
.tarjeta-brand-suave {
  background-color: rgba(139, 207, 91, 0.12);
  border: 1px solid var(--k-border) !important;
}

.aviso-card {
  transition: transform 0.2s ease;
  background-color: white;
}
.aviso-card:hover {
  transform: translateX(4px);
}
</style>
