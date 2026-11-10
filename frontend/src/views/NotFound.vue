<template>
  <div class="not-found-wrapper d-flex align-items-center justify-content-center">
    <div class="overlay"></div>

    <div class="content-card text-center p-5 shadow-lg">
      <div class="icon-container mb-4">
        <font-awesome-icon icon="compass" class="compass-icon fa-spin-slow" />
      </div>

      <h1 class="display-1 fw-bold text-white mb-0">404</h1>
      <h2 class="fw-bold verde-esmeralda mb-3">¡Ruta no encontrada!</h2>

      <p class="text-light mb-4">
        Parece que te has adentrado demasiado en la espesura de la selva. El sendero que buscas no existe o ha
        sido movido.
      </p>

      <div class="d-flex flex-column flex-md-row gap-3 justify-content-center">
        <button class="btn btn-outline-light px-4" @click="$router.back()">
          <font-awesome-icon icon="arrow-left" class="me-2" /> Volver atrás
        </button>
        <router-link :to="{ name: 'hospedaje-home' }" class="btn btn-brand-primary px-4">
          Ir a {{ configStore.hotelName }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useConfigStore } from "@/stores/config";

const configStore = useConfigStore();
</script>

<style scoped>
.not-found-wrapper {
  min-height: 100vh;
  width: 100%;
  position: relative;
  /* Imagen de fondo de selva/naturaleza */
  background-image: url("https://wallpapers.com/images/hd/green-jungle-pathway-lk8i82i3bt5pl282.jpg");
  background-size: cover;
  background-position: center;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 59, 42, 0.7);
  backdrop-filter: blur(4px);
}

.content-card {
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  backdrop-filter: blur(10px);
  max-width: 600px;
}

.verde-esmeralda {
  color: #2ecc71;
}

.compass-icon {
  font-size: 5rem;
  color: #2ecc71;
  filter: drop-shadow(0 0 15px rgba(46, 204, 113, 0.5));
}

.fa-spin-slow {
  animation: spin 10s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.btn-brand-primary {
  background-color: #2ecc71;
  color: #0f3b2a;
  border: none;
  font-weight: 700;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.btn-brand-primary:hover {
  background-color: #27ae60;
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(46, 204, 113, 0.3);
}

.btn-outline-light {
  border-radius: 12px;
  border-width: 2px;
  font-weight: 600;
}
</style>
