/**
 * Contenido institucional estático de las páginas públicas (Inicio y Nosotros).
 *
 * Vive en un solo archivo para que el hotel pueda revisarlo sin tocar componentes. Cuando estos
 * textos pasen a ser editables desde el panel (backlog, Fase 4), solo hay que reemplazar este
 * módulo por datos de `settings`. Los textos que dependen de la configuración son funciones.
 */
import imgAncestral from "@/img/ancestral.jpg";
import imgEventos1 from "@/img/eventos1.jpg";
import imgEventos2 from "@/img/eventos2.jpg";
import imgEventos5 from "@/img/eventos5.jpg";
import imgHabitacion1 from "@/img/habitacion1.jpg";
import imgHabitacion3 from "@/img/habitacion3.jpg";

// --- Inicio ---
export const HOME_EXPERIENCES = [
  {
    icon: "fa-solid fa-leaf",
    title: "Senderismo",
    text: "Camina por senderos sagrados y descubre la biodiversidad amazónica.",
  },
  {
    icon: "fa-solid fa-hands-holding",
    title: "Cultura Viva",
    text: "Conéctate con las tradiciones y saberes de la región.",
  },
  {
    icon: "fa-solid fa-moon",
    title: "Descanso Pleno",
    text: "Habitaciones diseñadas para el bienestar físico y espiritual.",
  },
];

// --- Nosotros ---
export const ABOUT_DEFAULTS = {
  tagline: "Un refugio pensado para descansar y conectar con la naturaleza.",
  description: (hotelName) =>
    `${hotelName} es un lugar para descansar, compartir y disfrutar de una atención cercana.`,
  mission: "Ofrecer una experiencia de hospedaje cómoda, cercana y respetuosa con el entorno.",
  vision: "Ser un referente de hospitalidad reconocido por la calidad de nuestro servicio.",
};

export const ABOUT_STORY = {
  title: "Más que un hotel, un compromiso",
  image: imgAncestral,
};

export const ABOUT_VALUES = [
  {
    icon: "fa-solid fa-heart-pulse",
    title: "Hospitalidad",
    text: "Servicio desde el corazón, haciendo sentir a cada huésped en su hogar amazónico.",
  },
  {
    icon: "fa-solid fa-earth-americas",
    title: "Sostenibilidad",
    text: "Protegemos la biodiversidad mediante prácticas de bajo impacto ambiental.",
  },
  {
    icon: "fa-solid fa-person-praying",
    title: "Identidad",
    text: "Honramos y difundimos la riqueza cultural de nuestra región.",
  },
  {
    icon: "fa-solid fa-handshake-angle",
    title: "Integridad",
    text: "Actuamos con transparencia y respeto hacia nuestra comunidad y visitantes.",
  },
];

/** `answer` recibe { depositPercent } de los ajustes del sitio. */
export const ABOUT_FAQS = [
  {
    question: "¿Qué ropa debo llevar para mi visita?",
    answer: () =>
      "Recomendamos ropa ligera y transpirable, preferiblemente de secado rápido. No olvides botas de " +
      "trekking o calzado cerrado, repelente para insectos y un impermeable ligero, ya que el clima " +
      "amazónico es impredecible.",
  },
  {
    question: "¿El hotel cuenta con conexión a internet?",
    answer: () =>
      "Sí, contamos con conexión Wi-Fi de alta velocidad en las zonas comunes y habitaciones, ideal " +
      "para nómadas digitales que desean trabajar rodeados de naturaleza.",
  },
  {
    question: "¿Cómo funciona la política de cancelación?",
    answer: ({ depositPercent }) =>
      "Puedes cancelar tu reserva con hasta 72 horas de anticipación para recibir un reembolso " +
      `parcial. El anticipo del ${depositPercent}% no es reembolsable, pero puede ser reprogramado ` +
      "para una fecha futura según disponibilidad.",
  },
];

export const ABOUT_IMPACT = {
  label: "Turismo Regenerativo",
  title: "Guardianes de la Selva",
  description: (hotelName) =>
    `En ${hotelName}, entendemos que somos huéspedes de la naturaleza. Nuestra operación está ` +
    "diseñada para devolverle a la tierra más de lo que tomamos, apoyando directamente a la " +
    "biodiversidad y a las familias de la región.",
  commitments: [
    { icon: "fa-solid fa-droplet", text: "Tratamiento biológico de aguas residuales." },
    { icon: "fa-solid fa-sun", text: "Energía limpia en senderos y zonas comunes." },
    { icon: "fa-solid fa-mound", text: "Compostaje de residuos orgánicos para nuestra huerta." },
  ],
  metrics: [
    { value: "+500", label: "Árboles Nativos Plantados" },
    { value: "100%", label: "Empleo Local Legítimo" },
    { value: "0%", label: "Plásticos de un solo uso" },
    { value: "+20", label: "Artesanos Apoyados" },
  ],
};

export const ABOUT_CAROUSEL = [
  { src: imgEventos1, alt: "Amanecer en el muelle" },
  { src: imgHabitacion1, alt: "Detalle de Artesanía Ancestral" },
  { src: imgEventos2, alt: "Paseo en canoa por el río" },
  { src: imgHabitacion3, alt: "Senderismo por Bosque Nativo" },
  { src: imgEventos5, alt: "Interior de Habitación Ancestral" },
];
