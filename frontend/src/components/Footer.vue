<script setup>
import { computed } from "vue";
import { useConfigStore } from "@/stores/config";

const configStore = useConfigStore();
const lugar = computed(() => configStore.data.city || configStore.data.country);
const direccion = computed(() =>
  [configStore.data.address, configStore.data.city].filter(Boolean).join(", "),
);
</script>

<template>
  <footer class="brand-footer mt-auto">
    <div class="container footer-grid">
      <div class="footer-brand">
        <h2 class="footer-logo mb-3">{{ configStore.hotelName }}</h2>
        <p>
          {{ configStore.data.tagline || "Un refugio de paz, cultura y naturaleza." }}
        </p>

        <div class="social-links mt-4">
          <a
            v-if="configStore.data.social_instagram"
            :href="configStore.data.social_instagram"
            target="_blank"
            rel="noopener"
            class="social-icon"
          >
            <font-awesome-icon :icon="['fab', 'instagram']" style="font-size: 1.3rem" />
          </a>

          <a
            v-if="configStore.data.social_facebook"
            :href="configStore.data.social_facebook"
            target="_blank"
            rel="noopener"
            class="social-icon"
          >
            <font-awesome-icon :icon="['fab', 'facebook']" style="font-size: 1.3rem" />
          </a>

          <a
            v-if="configStore.data.social_tiktok"
            :href="configStore.data.social_tiktok"
            target="_blank"
            rel="noopener"
            class="social-icon"
          >
            <font-awesome-icon :icon="['fab', 'tiktok']" style="font-size: 1.3rem" />
          </a>

          <a
            v-if="configStore.whatsappLink"
            :href="configStore.whatsappLink"
            target="_blank"
            rel="noopener"
            class="social-icon whatsapp-icon"
          >
            <font-awesome-icon :icon="['fab', 'whatsapp']" style="font-size: 1.4rem" />
          </a>
        </div>
      </div>

      <div class="footer-links d-flex justify-content-md-center">
        <div>
          <h3 class="mb-4 text-white">Navegación</h3>
          <ul class="list-unstyled">
            <li class="mb-2"><a href="#home">Inicio</a></li>
            <li class="mb-2"><a href="#experiencias">Experiencias</a></li>
            <li class="mb-2"><a href="#servicios">Hospedaje</a></li>
            <li class="mb-2"><a href="#donde-estamos">Ubicación</a></li>
          </ul>
        </div>
      </div>

      <div class="footer-contact text-center text-md-start">
        <h3 class="mb-4 text-white">Contacto</h3>

        <p
          v-if="direccion"
          class="mb-3 d-flex align-items-center justify-content-center justify-content-md-start"
        >
          <font-awesome-icon :icon="['fas', 'location-dot']" class="me-3 text-white fs-5" />
          <span>{{ direccion }}</span>
        </p>
        <p
          v-if="configStore.data.phone"
          class="mb-3 d-flex align-items-center justify-content-center justify-content-md-start"
        >
          <font-awesome-icon :icon="['fas', 'phone']" class="me-3 text-white fs-5" />
          <span>{{ configStore.data.phone }}</span>
        </p>
        <p
          v-if="configStore.data.contact_email"
          class="mb-0 d-flex align-items-center justify-content-center justify-content-md-start"
        >
          <font-awesome-icon :icon="['fas', 'envelope']" class="me-3 text-white fs-5" />
          <span>{{ configStore.data.contact_email }}</span>
        </p>
      </div>
    </div>

    <div class="footer-bottom mt-5">
      <div class="container">
        <hr class="footer-line" />
        <div class="bottom-flex">
          <p class="mb-0">
            &copy; {{ new Date().getFullYear() }} {{ configStore.hotelName }}. Todos los derechos reservados.
          </p>
          <router-link :to="{ name: 'privacy-policy' }" class="policy-link"
            >Política de tratamiento de datos</router-link
          >
          <p v-if="lugar" class="mb-0">Hecho con ❤️ en {{ lugar }}</p>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.brand-footer {
  background-color: var(--k-forest) !important;
  color: rgba(255, 252, 248, 0.88);
  padding: 80px 20px 20px 20px;
}

.brand-footer,
.brand-footer p,
.brand-footer span,
.brand-footer a {
  color: rgba(255, 252, 248, 0.88);
}

.brand-footer .text-white {
  color: var(--k-cream) !important;
}

.footer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 50px;
  max-width: 1100px;
  margin: 0 auto;
}

.footer-logo {
  font-family: "Handlee", cursive;
  font-size: 2.5rem;
  color: var(--k-cream);
  margin-bottom: 20px;
}

.footer-brand p {
  font-size: 0.95rem;
  line-height: 1.6;
  opacity: 0.8;
}

.social-links {
  display: flex;
  gap: 15px;
  margin-top: 25px;
}

.social-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: white;
  text-decoration: none;
  transition: all 0.3s ease;
}

.social-icon:hover {
  background: var(--k-forest-soft);
  color: var(--k-cream);
  transform: translateY(-5px);
}

.footer-links h3,
.footer-contact h3 {
  color: #fff;
  font-size: 1.2rem;
  margin-bottom: 25px;
  position: relative;
}

.footer-links h3::after,
.footer-contact h3::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -8px;
  width: 40px;
  height: 2px;
  background: var(--k-apple);
}

.footer-links ul {
  list-style: none;
  padding: 0;
}

.footer-links li {
  margin-bottom: 12px;
}

.footer-links a {
  color: #e0eee0;
  text-decoration: none;
  opacity: 0.85;
  transition: 0.3s;
}

.footer-links a:hover {
  opacity: 1;
  padding-left: 5px;
  color: var(--k-apple);
}

.footer-contact p {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  font-size: 0.95rem;
  opacity: 0.9;
}

.social-icon.whatsapp-icon:hover {
  background: #25d366;
  color: white;
  transform: translateY(-5px);
}

.footer-line {
  border: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  margin: 40px 0 20px 0;
}

.bottom-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  opacity: 0.8;
  flex-wrap: wrap;
  gap: 10px;
}

.policy-link {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.policy-link:hover {
  color: var(--k-apple) !important;
}

@media (max-width: 768px) {
  .footer-grid {
    text-align: center;
    gap: 40px;
  }
  .social-links {
    justify-content: center;
  }
  .footer-links h3::after,
  .footer-contact h3::after {
    left: 50%;
    transform: translateX(-50%);
  }
  .footer-contact p {
    justify-content: center;
  }
  .bottom-flex {
    justify-content: center;
    flex-direction: column;
  }
}
</style>
