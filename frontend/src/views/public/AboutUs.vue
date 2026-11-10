<template>
  <main class="about-page">
    <section class="about-hero">
      <div class="container text-center">
        <span class="subtitulo-blanco">Nuestra Esencia</span>
        <h1 class="titulo-hero">Somos {{ configStore.hotelName }}</h1>
        <p class="lead-text">
          {{ configStore.data.tagline || "Un refugio pensado para descansar y conectar con la naturaleza." }}
        </p>
      </div>

      <div class="custom-shape-divider-bottom">
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none">
          <path
            class="shape-fill"
            d="M421.9,6.5c22.6-2.5,51.5,0.4,75.5,5.3c23.6,4.9,70.9,23.5,100.5,35.7c75.8,32.2,133.7,44.5,192.6,49.7 c23.6,2.1,48.7,3.5,103.4-2.5c54.7-6,106.2-25.6,106.2-25.6V0H0v30.3c0,0,72,32.6,158.4,30.5c39.2-0.7,92.8-6.7,134-22.4 c21.2-8.1,52.2-18.2,79.7-24.2C399.3,7.9,411.6,7.5,421.9,6.5z"
          ></path>
        </svg>
      </div>
    </section>

    <section class="mision-vision py-5">
      <div class="container">
        <div class="row g-5 align-items-stretch">
          <div class="col-md-6">
            <div class="about-card h-100 shadow-soft">
              <div class="icon-circle">
                <font-awesome-icon icon="fa-solid fa-seedling" />
              </div>
              <h3>Nuestra Misión</h3>
              <p class="texto-config">{{ mision }}</p>
            </div>
          </div>
          <div class="col-md-6">
            <div class="about-card h-100 shadow-soft">
              <div class="icon-circle">
                <font-awesome-icon icon="fa-solid fa-eye" />
              </div>
              <h3>Nuestra Visión</h3>
              <p class="texto-config">{{ vision }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="sobre-nosotros-detalle pb-5">
      <div class="container">
        <div class="row align-items-center">
          <div class="col-lg-6">
            <img
              src="@/img/ancestral.jpg"
              :alt="configStore.hotelName"
              class="img-fluid rounded-4 shadow-lg mb-4"
            />
          </div>
          <div class="col-lg-6">
            <h2 class="titulo-seccion">Más que un hotel, un compromiso</h2>
            <p class="texto-config">{{ descripcion }}</p>
          </div>
        </div>
      </div>
    </section>

    <section id="nuestroValores">
      <div class="container mt-5 pt-4">
        <div class="text-center mb-5">
          <h2 class="titulo-valores">Nuestros Valores</h2>
        </div>
        <div class="grid-valores">
          <div class="valor-item">
            <div class="valor-icon-sm">
              <font-awesome-icon icon="fa-solid fa-heart-pulse" />
            </div>
            <h4>Hospitalidad</h4>
            <p>Servicio desde el corazón, haciendo sentir a cada huésped en su hogar amazónico.</p>
          </div>

          <div class="valor-item">
            <div class="valor-icon-sm">
              <font-awesome-icon icon="fa-solid fa-earth-americas" />
            </div>
            <h4>Sostenibilidad</h4>
            <p>Protegemos la biodiversidad mediante prácticas de bajo impacto ambiental.</p>
          </div>

          <div class="valor-item">
            <div class="valor-icon-sm">
              <font-awesome-icon icon="fa-solid fa-person-praying" />
            </div>
            <h4>Identidad</h4>
            <p>Honramos y difundimos la riqueza cultural de nuestra región.</p>
          </div>

          <div class="valor-item">
            <div class="valor-icon-sm">
              <font-awesome-icon icon="fa-solid fa-handshake-angle" />
            </div>
            <h4>Integridad</h4>
            <p>Actuamos con transparencia y respeto hacia nuestra comunidad y visitantes.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="faq-section py-5">
      <div class="container">
        <div class="text-center mb-5">
          <span class="subtitulo-verde">Dudas comunes</span>
          <h2 class="titulo-seccion">Preguntas Frecuentes</h2>
        </div>

        <div class="row justify-content-center">
          <div class="col-lg-8">
            <div id="accordionBrand" class="accordion accordion-flush custom-accordion">
              <div class="accordion-item shadow-sm mb-3">
                <h2 class="accordion-header">
                  <button
                    class="accordion-button collapsed"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#faq1"
                  >
                    ¿Qué ropa debo llevar para mi visita?
                  </button>
                </h2>
                <div id="faq1" class="accordion-collapse collapse" data-bs-parent="#accordionBrand">
                  <div class="accordion-body">
                    Recomendamos ropa ligera y transpirable, preferiblemente de secado rápido. No olvides
                    botas de trekking o calzado cerrado, repelente para insectos y un impermeable ligero, ya
                    que el clima amazónico es impredecible.
                  </div>
                </div>
              </div>

              <div class="accordion-item shadow-sm mb-3">
                <h2 class="accordion-header">
                  <button
                    class="accordion-button collapsed"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#faq2"
                  >
                    ¿El hotel cuenta con conexión a internet?
                  </button>
                </h2>
                <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#accordionBrand">
                  <div class="accordion-body">
                    Sí, contamos con conexión Wi-Fi de alta velocidad en las zonas comunes y habitaciones,
                    ideal para nómadas digitales que desean trabajar rodeados de naturaleza.
                  </div>
                </div>
              </div>

              <div class="accordion-item shadow-sm mb-3">
                <h2 class="accordion-header">
                  <button
                    class="accordion-button collapsed"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#faq3"
                  >
                    ¿Cómo funciona la política de cancelación?
                  </button>
                </h2>
                <div id="faq3" class="accordion-collapse collapse" data-bs-parent="#accordionBrand">
                  <div class="accordion-body">
                    Puedes cancelar tu reserva con hasta 72 horas de anticipación para recibir un reembolso
                    parcial. El anticipo del {{ configStore.data.deposit_percent }}% no es reembolsable, pero
                    puede ser reprogramado para una fecha futura según disponibilidad.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="impacto-local">
      <div class="container">
        <div class="row align-items-center">
          <div class="col-lg-6 mb-5 mb-lg-0">
            <span class="etiqueta-verde">Turismo Regenerativo</span>
            <h2 class="titulo-impacto">Guardianes de la Selva</h2>
            <p class="descripcion-impacto">
              En {{ configStore.hotelName }}, entendemos que somos huéspedes de la naturaleza. Nuestra
              operación está diseñada para devolverle a la tierra más de lo que tomamos, apoyando directamente
              a la biodiversidad y a las familias de la región.
            </p>

            <div class="lista-compromisos">
              <div class="compromiso-item">
                <font-awesome-icon icon="fa-solid fa-droplet" class="icon-check" />
                <span>Tratamiento biológico de aguas residuales.</span>
              </div>
              <div class="compromiso-item">
                <font-awesome-icon icon="fa-solid fa-sun" class="icon-check" />
                <span>Energía limpia en senderos y zonas comunes.</span>
              </div>
              <div class="compromiso-item">
                <font-awesome-icon icon="fa-solid fa-mound" class="icon-check" />
                <span>Compostaje de residuos orgánicos para nuestra huerta.</span>
              </div>
            </div>
          </div>

          <div class="col-lg-6">
            <div class="row g-4">
              <div class="col-6">
                <div class="card-metrica">
                  <h3 class="numero">+500</h3>
                  <p class="concepto">Árboles Nativos Plantados</p>
                </div>
              </div>
              <div class="col-6">
                <div class="card-metrica">
                  <h3 class="numero">100%</h3>
                  <p class="concepto">Empleo Local Legítimo</p>
                </div>
              </div>
              <div class="col-6">
                <div class="card-metrica">
                  <h3 class="numero">0%</h3>
                  <p class="concepto">Plásticos de un solo uso</p>
                </div>
              </div>
              <div class="col-6">
                <div class="card-metrica">
                  <h3 class="numero">+20</h3>
                  <p class="concepto">Artesanos Apoyados</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="gallery-carousel py-5">
      <div class="container-fluid p-0">
        <div class="carousel-track">
          <div class="carousel-item-img">
            <img src="@/img/eventos1.jpg" alt="Amanecer en el muelle" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/habitacion1.jpg" alt="Detalle de Artesanía Ancestral" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/eventos2.jpg" alt="Paseo en canoa por el río" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/habitacion3.jpg" alt="Senderismo por Bosque Nativo" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/eventos5.jpg" alt="Interior de Habitación Ancestral" />
          </div>

          <div class="carousel-item-img">
            <img src="@/img/eventos1.jpg" alt="Amanecer en el muelle" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/habitacion1.jpg" alt="Detalle de Artesanía Ancestral" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/eventos2.jpg" alt="Paseo en canoa por el río" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/habitacion3.jpg" alt="Senderismo por Bosque Nativo" />
          </div>
          <div class="carousel-item-img">
            <img src="@/img/eventos5.jpg" alt="Interior de Habitación Ancestral" />
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed } from "vue";
import { useConfigStore } from "@/stores/config";

const configStore = useConfigStore();

// Textos institucionales editables desde el panel (ajustes del sitio).
const descripcion = computed(
  () =>
    configStore.data.about_description ||
    `${configStore.hotelName} es un lugar para descansar, compartir y disfrutar de una atención cercana.`,
);
const mision = computed(
  () =>
    configStore.data.mission ||
    "Ofrecer una experiencia de hospedaje cómoda, cercana y respetuosa con el entorno.",
);
const vision = computed(
  () =>
    configStore.data.vision ||
    "Ser un referente de hospitalidad reconocido por la calidad de nuestro servicio.",
);
</script>

<style scoped>
.texto-config {
  white-space: pre-line;
}

/* Hero de la página About */
.about-hero {
  position: relative;
  background: linear-gradient(135deg, var(--k-forest) 0%, var(--k-forest-soft) 100%);
  color: var(--k-cream);
  padding: 120px 20px 100px;
  text-align: center;
}

.titulo-hero {
  font-family: "Handlee", cursive;
  font-size: 3.5rem;
  margin-top: 15px;
}

.lead-text {
  max-width: 700px;
  margin: 20px auto 0;
  font-size: 1.2rem;
  opacity: 0.9;
}

/* Divisor SVG */
.custom-shape-divider-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  line-height: 0;
  transform: rotate(180deg);
}

.custom-shape-divider-bottom svg {
  display: block;
  width: 100%;
  height: 60px;
}

.shape-fill {
  fill: var(--k-cream); /* Debe coincidir con el fondo de la siguiente sección */
}

/* Tarjetas de Misión y Visión */
.mision-vision {
  background-color: var(--k-cream);
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

/* Título de sección */
.titulo-seccion {
  font-family: "Handlee", cursive;
  font-size: 2.5rem;
  color: var(--k-forest);
  margin-bottom: 20px;
}

.subtitulo-blanco {
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--k-apple-light);
  font-weight: 700;
}
img {
  object-fit: cover;
  width: 100%;
  height: 50%;
  justify-content: center;
  align-items: center;
}
/* --- SECCIÓN VALORES --- */
.titulo-valores {
  font-family: "Handlee", cursive;
  font-size: 2.2rem;
  color: var(--k-forest);
  position: relative;
  display: inline-block;
}

.titulo-valores::after {
  content: "";
  position: absolute;
  width: 50%;
  height: 3px;
  background: var(--k-apple-light);
  bottom: -10px;
  left: 25%;
  border-radius: 2px;
}

.grid-valores {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
  padding-bottom: 40px;
}

.valor-item {
  text-align: center;
  padding: 20px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.valor-item:hover {
  background: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  transform: translateY(-5px);
}

.valor-icon-sm {
  font-size: 1.8rem;
  color: var(--k-forest-soft);
  margin-bottom: 15px;
}

.valor-item h4 {
  font-family: "Handlee", cursive;
  font-size: 1.4rem;
  color: var(--k-forest);
  margin-bottom: 10px;
}

.valor-item p {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .grid-valores {
    grid-template-columns: 1fr 1fr; /* Dos columnas en móvil */
    gap: 15px;
  }
}

/* --- FAQ STYLE --- */
.faq-section {
  background-color: rgba(15, 59, 42, 0.04); /* Un gris verdoso muy tenue */
}

.subtitulo-verde {
  color: var(--k-forest-soft);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-size: 0.9rem;
}

.custom-accordion .accordion-item {
  border: none;
  border-radius: 15px !important;
  overflow: hidden;
}

.custom-accordion .accordion-button {
  font-weight: 600;
  color: var(--k-forest);
  padding: 20px;
  background-color: white;
  box-shadow: none;
}

.custom-accordion .accordion-button:not(.collapsed) {
  color: var(--k-forest-soft);
  background-color: var(--k-apple-soft);
}

.custom-accordion .accordion-button::after {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%231a5c43'%3e%3cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3e%3c/svg%3e");
}

.custom-accordion .accordion-body {
  font-size: 0.95rem;
  color: #555;
  line-height: 1.6;
  background-color: #f0f7f4;
}

/* --- SECCIÓN IMPACTO --- */
.impacto-local {
  background-color: var(--k-forest-soft);
  padding: 100px 20px;
  color: var(--k-cream);
}

.etiqueta-verde {
  color: var(--k-apple-light);
  text-transform: uppercase;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 2px;
}

.titulo-impacto {
  font-family: "Handlee", cursive;
  font-size: 3rem;
  margin: 15px 0 25px;
}

.descripcion-impacto {
  font-size: 1.1rem;
  line-height: 1.7;
  opacity: 0.9;
  margin-bottom: 30px;
}

/* Lista de compromisos */
.lista-compromisos {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.compromiso-item {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 1rem;
}

.icon-check {
  color: var(--k-apple-light);
  font-size: 1.2rem;
}

/* Tarjetas de Métricas */
.card-metrica {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 30px 20px;
  border-radius: 25px;
  text-align: center;
  transition: all 0.3s ease;
  height: 100%;
}

.card-metrica:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-5px);
  border-color: var(--k-apple-light);
}

.numero {
  font-family: "Handlee", cursive;
  font-size: 2.5rem;
  color: var(--k-apple-light);
  margin-bottom: 5px;
}

.concepto {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.8;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .titulo-impacto {
    font-size: 2.2rem;
  }
  .card-metrica {
    padding: 20px 10px;
  }
  .numero {
    font-size: 1.8rem;
  }
}

/* --- ESTILO CARRUSEL ARTÍSTICO INFINITO --- */
.gallery-carousel {
  background-color: var(--k-cream);
  padding: 60px 0;
  overflow: hidden;
}

.carousel-track {
  display: flex;
  /* El ancho debe ser (ancho_foto + gap) * total_fotos */
  width: calc(320px * 10);
  animation: scrollInfinito 40s linear infinite;
}

.carousel-track:hover {
  animation-play-state: paused; /* Se detiene para que el usuario aprecie la foto */
}

.carousel-item-img {
  width: 400px; /* Un poco más grandes para mayor impacto */
  height: 320px;
  flex-shrink: 0;
  margin: 0 10px;
  perspective: 1000px; /* Para un efecto de profundidad opcional */
}

.carousel-item-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 20px;
  /* EFECTO ARTÍSTICO INICIAL */
  filter: grayscale(100%) contrast(110%);
  opacity: 0.7;
  transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  cursor: pointer;
}

/* EFECTO AL PASAR EL MOUSE (Hover) */
.carousel-item-img img:hover {
  filter: grayscale(0%) contrast(100%); /* Vuelve el color natural */
  opacity: 1;
  transform: scale(1.05); /* Pequeño zoom para resaltar */
  box-shadow: 0 15px 30px rgba(15, 59, 42, 0.3); /* Sombra verde bosque */
}

/* Animación fluida */
@keyframes scrollInfinito {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(calc(-320px * 5));
  } /* Mitad del track */
}

/* Ajustes para móviles */
@media (max-width: 768px) {
  .carousel-item-img {
    width: 220px;
    height: 180px;
  }
  .carousel-item-img img {
    filter: grayscale(0%); /* En móvil es mejor mostrar color de una vez */
    opacity: 1;
  }
  @keyframes scrollInfinito {
    0% {
      transform: translateX(0);
    }
    100% {
      transform: translateX(calc(-240px * 5));
    }
  }
}
</style>
