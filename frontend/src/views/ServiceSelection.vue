<template>
  <div class="service-selection">
    <div class="overlay-brand">
      <div class="container text-center py-5">
        <font-awesome-icon icon="fa-solid fa-leaf" class="text-success mb-3 fs-1" />
        <h1 class="display-4 fw-bold text-white mb-2">Experiencias {{ configStore.hotelName }}</h1>
        <p class="text-light lead mb-5">Elige el tipo de experiencia que deseas vivir</p>

        <div class="row g-4 justify-content-center">
          <div class="col-md-5">
            <div class="card-selection shadow-lg" @click="goToHospedaje">
              <div class="card-image hospedaje-bg"></div>
              <div class="card-content">
                <h2 class="fw-bold">Hospedaje</h2>
                <p>
                  Cabañas privadas y habitaciones diseñadas para el descanso profundo y la conexión con la
                  naturaleza.
                </p>
                <button class="btn btn-success rounded-pill px-4">Explorar Cabañas</button>
              </div>
            </div>
          </div>

          <div class="col-md-5">
            <div class="card-selection shadow-lg inactive-card">
              <div class="card-image eventos-bg"></div>
              <div class="card-content">
                <h2 class="fw-bold">Eventos y Bodas</h2>
                <p>Celebra tus momentos especiales rodeado de la magia ancestral y paisajes inolvidables.</p>
                <span class="badge bg-warning text-dark">Próximamente</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import { useConfigStore } from "@/stores/config";

const router = useRouter();
const configStore = useConfigStore();

const goToHospedaje = () => {
  router.push({ name: "hospedaje-home" });
};
</script>

<style scoped>
.service-selection {
  margin-top: 60px;
  min-height: 100vh;
  background-image: url("https://i0.wp.com/www.lasillavacia.com/wp-content/uploads/2023/10/LaPaya_Portada.jpg?fit=1200%2C700&ssl=1");
  background-size: cover;
  background-position: center;
}

.overlay-brand {
  min-height: 100vh;
  background: rgba(15, 59, 42, 0.8);
  display: flex;
  align-items: center;
}

.card-selection {
  background: white;
  border-radius: 25px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  height: 100%;
}

.card-selection:hover {
  transform: translateY(-15px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
}

.card-image {
  height: 250px;
  background-size: cover;
  background-position: center;
}

/* Imágenes de fondo para las tarjetas */
.hospedaje-bg {
  background-image: url("@/img/habitacion2.jpg");
}
.eventos-bg {
  background-image: url("@/img/eventos3.jpg");
}

.card-content {
  padding: 2.5rem;
  text-align: center;
}

.card-content h2 {
  color: #0f3b2a;
}

.inactive-card {
  filter: grayscale(0.8);
  opacity: 0.9;
  cursor: not-allowed;
}

.inactive-card:hover {
  transform: none;
}
</style>
