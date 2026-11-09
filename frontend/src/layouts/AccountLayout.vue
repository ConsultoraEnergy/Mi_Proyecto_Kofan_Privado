<script setup>
import SidebarAccount from "@/views/app/SidebarView.vue";
</script>

<template>
  <div class="account-bg">
    <div class="container account-container">
      <div class="row g-4">
        <div class="col-lg-3 col-md-4">
          <SidebarAccount />
        </div>

        <div class="col-lg-9 col-md-8">
          <div class="content-wrapper shadow-sm">
            <router-view></router-view>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.account-bg {
  background-color: #f4f7f6; /* Un gris verdoso muy suave */
  min-height: 100vh;
}

.account-container {
  padding-top: 120px; /* Espacio para que el Navbar no lo tape */
  padding-bottom: 50px;
}

.content-wrapper {
  background: white;
  border-radius: 20px;
  padding: 30px;
  min-height: 500px;
}

/* En móviles, el sidebar va arriba y el contenido abajo */
@media (max-width: 767px) {
  .account-container {
    padding-top: 100px;
  }
}
</style>
