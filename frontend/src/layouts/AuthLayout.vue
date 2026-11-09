<script setup>
import { useConfigStore } from "@/stores/config";

// Nombre y logo del hotel para las pantallas de acceso.
useConfigStore().fetchSiteConfig();
</script>

<template>
  <div class="min-vh-100 bg-light">
    <div class="container-fluid p-3">
      <div class="auth-container">
        <router-view />
      </div>
    </div>
  </div>
</template>
