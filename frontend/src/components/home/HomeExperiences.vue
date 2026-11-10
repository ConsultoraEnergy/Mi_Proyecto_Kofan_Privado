<script setup>
import { HOME_EXPERIENCES } from "@/content/publicContent";
import SectionHeading from "@/components/home/SectionHeading.vue";
</script>

<template>
  <section id="experiencias" class="experiencias">
    <div class="container">
      <SectionHeading class="mb-5" eyebrow="Vive lo Auténtico" title="Descubre la magia en cada detalle" />
      <div class="grid-actividades">
        <div v-for="item in HOME_EXPERIENCES" :key="item.title" class="card-actividad">
          <div class="icono-wrapper"><font-awesome-icon :icon="item.icon" /></div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.text }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.experiencias {
  padding: 80px 20px 120px 20px;
  background: #fffdfc;
}

.grid-actividades {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  max-width: 1100px;
  margin: 0 auto;
}

.card-actividad {
  text-align: center;
  padding: 30px;
}

.card-actividad h3 {
  font-family: "Handlee", cursive;
}

.icono-wrapper {
  width: 80px;
  height: 80px;
  background-color: var(--k-apple-soft);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: var(--k-forest-soft);
  font-size: 2rem;
}
</style>
