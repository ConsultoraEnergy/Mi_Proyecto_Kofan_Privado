<script setup>
defineProps({
  mission: { type: String, required: true },
  vision: { type: String, required: true },
});
</script>

<template>
  <section class="mision-vision py-5">
    <div class="container">
      <div class="row g-5 align-items-stretch">
        <div class="col-md-6">
          <div class="about-card h-100 shadow-soft">
            <div class="icon-circle"><font-awesome-icon icon="fa-solid fa-seedling" /></div>
            <h3>Nuestra Misión</h3>
            <p class="texto-config">{{ mission }}</p>
          </div>
        </div>
        <div class="col-md-6">
          <div class="about-card h-100 shadow-soft">
            <div class="icon-circle"><font-awesome-icon icon="fa-solid fa-eye" /></div>
            <h3>Nuestra Visión</h3>
            <p class="texto-config">{{ vision }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.mision-vision {
  background-color: var(--k-cream);
}

.texto-config {
  white-space: pre-line;
}

.about-card {
  background: white;
  padding: 40px;
  border-radius: 30px;
  text-align: center;
  border-bottom: 5px solid var(--k-forest-soft);
  transition: transform 0.3s ease;
}

.about-card:hover {
  transform: translateY(-10px);
}

.icon-circle {
  width: 70px;
  height: 70px;
  background-color: var(--k-apple-soft);
  color: var(--k-forest-soft);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 2rem;
}

.about-card h3 {
  font-family: "Handlee", cursive;
  color: var(--k-forest);
  margin-bottom: 15px;
}
</style>
