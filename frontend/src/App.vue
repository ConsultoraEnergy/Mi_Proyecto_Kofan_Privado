<script setup>
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import Navbar from "@/components/Navbar.vue";
import Footer from "@/components/Footer.vue";
import ReservaModal from "@/components/ReservaModal.vue";
import { useConfigStore } from "@/stores/config";

const route = useRoute();
const configStore = useConfigStore();
const showPublicChrome = computed(() => !route.meta.hideNav);

// Ajustes del sitio (marca, contacto, textos): se cargan una sola vez para toda la app.
onMounted(() => configStore.fetchSiteConfig());
</script>

<template>
  <main id="page">
    <Navbar v-if="showPublicChrome" />
    <router-view />
    <ReservaModal />
    <Footer v-if="showPublicChrome" />
  </main>
</template>
