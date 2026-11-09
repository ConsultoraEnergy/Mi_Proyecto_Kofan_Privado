<script setup>
const paginaActual = ref(1);
const totalPaginas = ref(1);
const limitePorPagina = 10;
import { ref, computed, onMounted, watch } from "vue";
import Swal from "sweetalert2";
import apiClient from "@/api/apiClient";
import { defineAsyncComponent } from "vue";
const ModalEdicionReserva = defineAsyncComponent(
  () => import("@/components/ModalEdicionReserva.vue"),
);
const ModalFactura = defineAsyncComponent(
  () => import("@/components/ModalFactura.vue"),
);

// 🟢 1. CONSTANTES (Eliminación de Magic Strings)
const ESTADOS_RESERVA = {
  PENDIENTE: "pendiente",
  CONFIRMADA: "confirmada",
  OCUPADA: "ocupada",
  FINALIZADA: "finalizada",
  CANCELADA: "cancelada",
};

const reservas = ref([]);
const filtro = ref("");
const filtroAplicado = ref(""); // Lo que realmente usaremos para filtrar
let timeoutBuscador = null; // Nuestro reloj temporizador

// Vigilar cada vez que el usuario teclea en "filtro"
watch(filtro, (nuevoValor) => {
  clearTimeout(timeoutBuscador); // Cancelar la búsqueda anterior si sigue tecleando

  timeoutBuscador = setTimeout(() => {
    filtroAplicado.value = nuevoValor; // Aplicar la búsqueda real después de 300ms (0.3 seg)
  }, 300);
});
const cargandoReservas = ref(true);
const pestanaActiva = ref("proximas");

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_APPLE = getBrandColor("--k-apple", "#8BCF5B");
const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");

const cargarReservas = async () => {
  cargandoReservas.value = true;
  try {
    // 1. Armamos el texto que le vamos a enviar al backend según la pestaña
    let estadosQuery = "";
    if (pestanaActiva.value === "proximas")
      estadosQuery = `${ESTADOS_RESERVA.PENDIENTE},${ESTADOS_RESERVA.CONFIRMADA}`;
    if (pestanaActiva.value === "casa") estadosQuery = ESTADOS_RESERVA.OCUPADA;
    if (pestanaActiva.value === "historial")
      estadosQuery = `${ESTADOS_RESERVA.FINALIZADA},${ESTADOS_RESERVA.CANCELADA}`;

    // 🟢 2. EL FIX ESTÁ AQUÍ: Mira bien que la URL ahora incluye ?estados=${estadosQuery}
    const response = await apiClient.get(
      `/api/reservas/admin/todas?estados=${estadosQuery}&page=${paginaActual.value}&limit=${limitePorPagina}`,
    );

    reservas.value =
      response.data.reservas || response.data.data || response.data;

    // 3. Sincronizamos la paginación
    if (response.data.resumen) {
      totalPaginas.value = response.data.resumen.total_paginas || 1;
      paginaActual.value =
        response.data.resumen.pagina_actual || paginaActual.value;
    }
  } catch (error) {
    console.error("Error al cargar reservas:", error);
    Swal.fire("Error", "No se pudieron cargar las reservas.", "error");
  } finally {
    setTimeout(() => {
      cargandoReservas.value = false;
    }, 300);
  }
};

// 🟢 Agrega esta nueva función para cambiar de página
const cambiarPestana = (nuevaPestana) => {
  pestanaActiva.value = nuevaPestana;
  paginaActual.value = 1;
  cargarReservas();
};
const cambiarPagina = (nuevaPagina) => {
  // Solo avanza o retrocede si la página destino existe
  if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas.value) {
    paginaActual.value = nuevaPagina; // Actualiza el número
    cargarReservas(); // Llama al backend pidiendo el nuevo bloque de 10
  }
};

onMounted(() => {
  cargarReservas();
});

// FILTRO MAESTRO
const reservasParaMostrar = computed(() => {
  let filtradas = reservas.value;

  // Ya no filtramos por pestaña aquí, solo dejamos el buscador de texto
  if (filtroAplicado.value) {
    const termino = filtroAplicado.value.toLowerCase();
    filtradas = filtradas.filter((res) => {
      const nombre = (res.cliente || res.cliente_nombre || "").toLowerCase();
      const email = (res.cliente_email || "").toLowerCase();
      const idReserva = (res._id || res.id || "").toLowerCase();
      return (
        nombre.includes(termino) ||
        email.includes(termino) ||
        idReserva.includes(termino)
      );
    });
  }

  return filtradas;
});

// 🔒 Los comprobantes ya no son públicos: se descargan con el token del admin
// y se abren como un archivo local (blob) en una pestaña nueva.
const verComprobante = async (urlComprobante) => {
  // Abrimos la pestaña de inmediato (dentro del clic) para que el navegador no la bloquee.
  const ventana = window.open("", "_blank");
  try {
    const { data } = await apiClient.get(urlComprobante, { responseType: "blob" });
    const objectUrl = URL.createObjectURL(data);
    if (ventana) {
      ventana.location.href = objectUrl;
    } else {
      window.open(objectUrl, "_blank");
    }
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  } catch (error) {
    ventana?.close();
    Swal.fire("Error", "No se pudo cargar el comprobante de pago.", "error");
  }
};

// 🟢 2. SEPARACIÓN DE LÓGICA: Solo llamadas a la API
const procesarCambioEstadoAPI = async (id, nuevoEstado, datosReserva) => {
  // 1. Actualizamos el estado de la reserva
  await apiClient.patch(`/api/reservas/${id}/estado`, {
    estado: nuevoEstado,
    motivo_actualizacion: "Cambio de estado desde el panel",
  });

  // 2. SI ES CHECK-IN, CREAMOS EL INVOICE
  if (nuevoEstado === ESTADOS_RESERVA.OCUPADA && datosReserva) {
    const payloadInvoice = {
      booking_id: id,
      guest_name: datosReserva.cliente_nombre || datosReserva.cliente,
      guest_document: datosReserva.cliente_documento || "N/A",
      guest_email: datosReserva.cliente_email || "N/A",
      guest_phone: datosReserva.cliente_celular || "N/A",
      room_name:
        datosReserva.habitacion_nombre ||
        datosReserva.habitacion ||
        "Habitación",
      check_in_date: datosReserva.fecha_entrada,
      check_out_date: datosReserva.fecha_salida,
      room_subtotal: datosReserva.monto_total || datosReserva.monto || 0,
      status: "open",
    };
    await apiClient.post("/invoices/", payloadInvoice);
  }

  // 3. SI ES CHECK-OUT, CERRAMOS LA FACTURA
  if (nuevoEstado === ESTADOS_RESERVA.FINALIZADA) {
    try {
      await apiClient.put(`/invoices/close-by-booking/${id}`);
      console.log("Factura cerrada exitosamente");
    } catch (invoiceError) {
      console.warn(
        "No se pudo cerrar la factura (quizás ya estaba cerrada o no existía).",
      );
    }
  }
};

// 🟢 3. SEPARACIÓN DE LÓGICA: Solo Interfaz de Usuario (SweetAlert)
const actualizarEstado = (id, nuevoEstado) => {
  let titulo = "¿Actualizar estado?";
  let texto = `¿Estás seguro de cambiar el estado a ${nuevoEstado}?`;
  let textoBoton = "Sí, cambiar";

  if (nuevoEstado === ESTADOS_RESERVA.CONFIRMADA) {
    titulo = "¿Confirmar esta reserva?";
    texto =
      "El pago quedará validado y la llegada seguirá su curso normalmente.";
    textoBoton = "Sí, confirmar";
  } else if (nuevoEstado === ESTADOS_RESERVA.OCUPADA) {
    titulo = "¿Registrar la llegada?";
    texto = "Todo quedará preparado para recibir a este viajero.";
    textoBoton = "Sí, hacer check-in";
  } else if (nuevoEstado === ESTADOS_RESERVA.FINALIZADA) {
    titulo = "¿Cerrar la estancia?";
    texto =
      "La salida quedará registrada y la cuenta se cerrará correctamente.";
    textoBoton = "Sí, finalizar";
  } else if (nuevoEstado === ESTADOS_RESERVA.PENDIENTE) {
    titulo = "¿Restaurar seguimiento?";
    texto = "La reserva volverá a estar activa para continuar su gestión.";
    textoBoton = "Sí, restaurar";
  }

  Swal.fire({
    title: titulo,
    text: texto,
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: COLOR_APPLE,
    cancelButtonColor: COLOR_FOREST,
    confirmButtonText: textoBoton,
    cancelButtonText: "Volver",
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        const datosReserva = reservas.value.find((r) => (r.id || r._id) === id);

        await procesarCambioEstadoAPI(id, nuevoEstado, datosReserva);
        await cargarReservas();

        Swal.fire({
          title: "Movimiento actualizado",
          text:
            nuevoEstado === ESTADOS_RESERVA.OCUPADA
              ? "Todo preparado para la llegada de este viajero"
              : `La reserva quedó en estado ${nuevoEstado}.`,
          icon: "success",
          timer: 1700,
          showConfirmButton: false,
        });
      } catch (error) {
        console.error("Error al actualizar:", error);
        Swal.fire(
          "No fue posible actualizar esta reserva",
          "Inténtalo nuevamente en unos segundos.",
          "error",
        );
      }
    }
  });
};

const eliminarReserva = (id) => {
  Swal.fire({
    title: "¿Deseas cancelar esta reserva?",
    text: "La habitación volverá a quedar disponible para otras llegadas.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: COLOR_APPLE,
    cancelButtonColor: COLOR_FOREST,
    confirmButtonText: "Sí, cancelar",
    cancelButtonText: "Seguir revisando",
  }).then((result) => {
    if (result.isConfirmed) {
      actualizarEstado(id, ESTADOS_RESERVA.CANCELADA);
    }
  });
};

const getBadgeClass = (estado) => {
  switch (estado) {
    case ESTADOS_RESERVA.CONFIRMADA:
      return "badge-soft-apple";
    case ESTADOS_RESERVA.PENDIENTE:
      return "badge-soft-sand";
    case ESTADOS_RESERVA.OCUPADA:
      return "badge-soft-sky";
    case ESTADOS_RESERVA.FINALIZADA:
      return "badge-soft-neutral";
    case ESTADOS_RESERVA.CANCELADA:
      return "badge-soft-rose";
    default:
      return "badge-soft-neutral";
  }
};

// 🟢 Nueva función para los iconos
const getBadgeIcon = (estado) => {
  switch (estado) {
    case ESTADOS_RESERVA.CONFIRMADA:
      return "fa-solid fa-circle-check";
    case ESTADOS_RESERVA.PENDIENTE:
      return "fa-solid fa-clock";
    case ESTADOS_RESERVA.OCUPADA:
      return "fa-solid fa-house-chimney";
    case ESTADOS_RESERVA.FINALIZADA:
      return "fa-solid fa-circle-check";
    case ESTADOS_RESERVA.CANCELADA:
      return "fa-solid fa-ban";
    default:
      return "fa-solid fa-circle-info";
  }
};

const mostrarModalEdicion = ref(false);
const reservaAEditar = ref(null);
const esModoCheckIn = ref(false);

const abrirModalEdicion = (reserva, checkIn = false) => {
  reservaAEditar.value = reserva;
  esModoCheckIn.value = checkIn;
  mostrarModalEdicion.value = true;
};

const refrescarTabla = async () => {
  await cargarReservas();
};

const mostrarModalFactura = ref(false);
const reservaParaFactura = ref(null);
const invoiceSeleccionada = ref(null);
const cargandoFactura = ref(false);

const abrirModalFactura = async (reserva) => {
  const idReserva = reserva.id || reserva._id;
  reservaParaFactura.value = reserva;
  mostrarModalFactura.value = true;
  cargandoFactura.value = true;
  invoiceSeleccionada.value = null;

  try {
    const { data } = await apiClient.get(`/invoices/by-booking/${idReserva}`);
    invoiceSeleccionada.value = data;
  } catch (error) {
    console.error("No se encontró factura para esta reserva:", error);
  } finally {
    cargandoFactura.value = false;
  }
};

const totalHuespedesEnCasa = ref(0);
const cargarHuespedesDelDashboard = async () => {
  try {
    const response = await apiClient.get("/dashboard");
    totalHuespedesEnCasa.value = response.data.stats.huespedesHoy;
  } catch (error) {
    console.error("No se pudo traer el dato de huéspedes:", error);
  }
};
onMounted(() => {
  cargarReservas();
  cargarHuespedesDelDashboard();
});
</script>

<template>
  <div class="bookings-manager container-fluid py-4">
    <div class="mb-4">
      <p class="brand-handmade mb-1">Seguimiento sereno de cada llegada</p>
      <h2 class="section-title mb-1 d-flex align-items-center gap-2">
        <font-awesome-icon icon="fa-solid fa-calendar-days" />
        Gestión de Reservas
      </h2>
      <p class="text-muted mb-0">
        Prioriza llegadas, salidas y estancias activas con una lectura más
        clara.
      </p>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="eco-card border-0 shadow-sm p-3 rounded-4 stats-card h-100">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <h6 class="text-muted fw-bold mb-2 text-uppercase small-label">
                Confirmadas
              </h6>
              <h3 class="fw-bold mb-1 text-kofan">
                {{
                  reservas.filter(
                    (r) => r.estado === ESTADOS_RESERVA.CONFIRMADA,
                  ).length
                }}
              </h3>
              <p class="text-muted small mb-0">Listas para ingreso</p>
            </div>
            <div class="icon-box tone-apple-box">
              <font-awesome-icon icon="fa-solid fa-leaf" />
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="eco-card border-0 shadow-sm p-3 rounded-4 stats-card h-100">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <h6 class="text-muted fw-bold mb-2 text-uppercase small-label">
                Pendientes
              </h6>
              <h3 class="fw-bold mb-1 text-kofan">
                {{
                  reservas.filter((r) => r.estado === ESTADOS_RESERVA.PENDIENTE)
                    .length
                }}
              </h3>
              <p class="text-muted small mb-0">Por verificar pago</p>
            </div>
            <div class="icon-box tone-sky-box">
              <font-awesome-icon icon="fa-solid fa-calendar-day" />
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="eco-card border-0 shadow-sm p-3 rounded-4 stats-card h-100">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <h6 class="text-muted fw-bold mb-2 text-uppercase small-label">
                Huéspedes Hoy
              </h6>
              <h3 class="fw-bold mb-1 text-kofan">
                {{ totalHuespedesEnCasa }}
              </h3>
              <p class="text-muted small mb-0">En las instalaciones</p>
            </div>
            <div class="icon-box tone-bed-box">
              <font-awesome-icon icon="fa-solid fa-bed" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card eco-card border-0 shadow-sm rounded-4 overflow-hidden">
      <div
        class="card-header bg-transparent p-3 border-0 d-flex flex-column flex-md-row justify-content-between align-items-center gap-3"
      >
        <div class="filter-chip-group">
          <button
            class="filter-chip"
            :class="{ active: pestanaActiva === 'proximas' }"
            @click="cambiarPestana('proximas')"
          >
            <font-awesome-icon icon="fa-solid fa-calendar-days" class="me-2" />
            Por Llegar
          </button>

          <button
            class="filter-chip"
            :class="{ active: pestanaActiva === 'casa' }"
            @click="cambiarPestana('casa')"
          >
            <font-awesome-icon icon="fa-solid fa-bed" class="me-2" /> En Casa
          </button>

          <button
            class="filter-chip"
            :class="{ active: pestanaActiva === 'historial' }"
            @click="cambiarPestana('historial')"
          >
            <font-awesome-icon icon="fa-solid fa-broom" class="me-2" />
            Historial
          </button>
        </div>

        <div
          class="input-group shadow-sm rounded-pill overflow-hidden search-soft"
          style="max-width: 360px"
        >
          <span class="input-group-text border-0 ps-3"
            ><font-awesome-icon icon="fa-solid fa-magnifying-glass" class="text-muted" />
          </span>
          <input
            v-model="filtro"
            type="text"
            class="form-control border-0 shadow-none"
            placeholder="Buscar viajero o reserva..."
          />
        </div>
      </div>

      <div class="card-body p-0 position-relative" style="min-height: 300px">
        <div
          v-if="cargandoReservas"
          class="d-flex flex-column justify-content-center align-items-center h-100 position-absolute w-100 bg-white z-1"
          style="min-height: 300px"
        >
          <div
            class="spinner-border"
            style="width: 3rem; height: 3rem; color: var(--k-apple)"
            role="status"
          >
            <span class="visually-hidden">Cargando...</span>
          </div>
          <p class="brand-handmade mt-3 mb-0">
            Actualizando las reservas del día...
          </p>
        </div>

        <div
          v-else-if="reservasParaMostrar.length === 0"
          class="d-flex flex-column justify-content-center align-items-center h-100 py-5 empty-state-copy"
        >
          <font-awesome-icon
            icon="fa-solid fa-leaf"
            class="display-6 mb-3"
            style="color: var(--k-apple)"
          />
          <h5 class="mb-1">No hay reservas en esta vista por ahora</h5>
          <p class="text-muted small mb-0">
            Cuando aparezcan nuevos movimientos, los verás aquí.
          </p>
        </div>

        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th class="ps-4 py-3 text-muted small fw-bold">ID / CLIENTE</th>
                <th class="py-3 text-muted small fw-bold">HABITACIÓN</th>
                <th class="py-3 text-muted small fw-bold">FECHAS (IN - OUT)</th>
                <th class="py-3 text-muted small fw-bold">TOTAL</th>
                <th class="py-3 text-muted small fw-bold">ESTADO</th>
                <th class="text-center py-3 text-muted small fw-bold">
                  ACCIONES
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="res in reservasParaMostrar" :key="res._id || res.id">
                <td class="ps-4">
                  <div class="fw-bold text-dark">
                    RES-{{ (res.id || res._id || "").slice(-6).toUpperCase() }}
                  </div>
                  <div class="text-dark fw-bold" style="font-size: 0.9rem">
                    {{ res.cliente || res.cliente_nombre }}
                  </div>
                  <div class="text-muted mt-1" style="font-size: 0.75rem">
                    <font-awesome-icon icon="fa-solid fa-phone" class="me-1" />
                    {{ res.cliente_celular || "Sin celular" }} <br />
                    <font-awesome-icon icon="fa-solid fa-envelope" class="me-1" />
                    {{ res.cliente_email || "Sin correo" }}
                  </div>
                </td>
                <td>{{ res.habitacion || res.habitacion_nombre || "N/A" }}</td>
                <td>
                  <div class="small text-muted">
                    <strong>Entra:</strong> {{ res.fecha_entrada }}
                  </div>
                  <div class="small text-muted">
                    <strong>Sale:</strong> {{ res.fecha_salida }}
                  </div>
                </td>
                <td class="fw-bold text-success">
                  ${{ (res.monto_total || res.monto || 0).toLocaleString() }}
                </td>
                <td>
                  <span
                    class="badge rounded-pill px-3 py-2 d-inline-flex align-items-center fw-normal text-capitalize"
                    :class="getBadgeClass(res.estado)"
                  >
                    <font-awesome-icon :icon="getBadgeIcon(res.estado)" class="me-2" />
                    {{ res.estado }}
                  </span>
                </td>
                <td class="text-center align-middle">
                  <div class="d-flex justify-content-center gap-2">
                    <button
                      v-if="res.comprobante_url"
                      type="button"
                      @click="verComprobante(res.comprobante_url)"
                      class="btn btn-sm btn-outline-info rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Ver Comprobante de Pago"
                    >
                      <font-awesome-icon icon="fa-solid fa-images" class="fs-6" />
                    </button>

                    <button
                      v-if="res.estado === ESTADOS_RESERVA.PENDIENTE"
                      @click="
                        actualizarEstado(
                          res.id || res._id,
                          ESTADOS_RESERVA.CONFIRMADA,
                        )
                      "
                      class="btn btn-sm btn-outline-success rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Confirmar Pago"
                    >
                      <font-awesome-icon icon="fa-solid fa-check" class="fs-6" />
                    </button>

                    <button
                      v-if="
                        [
                          ESTADOS_RESERVA.PENDIENTE,
                          ESTADOS_RESERVA.CONFIRMADA,
                        ].includes(res.estado)
                      "
                      @click="eliminarReserva(res.id || res._id)"
                      class="btn btn-sm btn-outline-danger rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Cancelar Reserva"
                    >
                      <font-awesome-icon icon="fa-solid fa-xmark" class="fs-6" />
                    </button>

                    <button
                      v-if="res.estado === ESTADOS_RESERVA.CANCELADA"
                      @click="
                        actualizarEstado(
                          res.id || res._id,
                          ESTADOS_RESERVA.PENDIENTE,
                        )
                      "
                      class="btn btn-sm btn-outline-warning rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Restaurar Reserva"
                    >
                      <font-awesome-icon icon="fa-solid fa-rotate-left" class="fs-6" />
                    </button>

                    <button
                      v-if="res.estado === ESTADOS_RESERVA.CONFIRMADA"
                      @click="abrirModalEdicion(res, true)"
                      class="btn btn-sm btn-outline-primary rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Hacer Check-in"
                    >
                      <font-awesome-icon icon="fa-solid fa-door-open" class="fs-6" />
                    </button>

                    <button
                      v-if="res.estado === ESTADOS_RESERVA.OCUPADA"
                      @click="abrirModalEdicion(res, false)"
                      class="btn btn-sm btn-outline-dark rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Editar Detalles o Agregar Consumos"
                    >
                      <font-awesome-icon :icon="['far', 'pen-to-square']" class="fs-6" />
                    </button>

                    <button
                      v-if="res.estado === ESTADOS_RESERVA.OCUPADA"
                      @click="
                        actualizarEstado(
                          res.id || res._id,
                          ESTADOS_RESERVA.FINALIZADA,
                        )
                      "
                      class="btn btn-sm btn-outline-secondary rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Hacer Check-out"
                    >
                      <font-awesome-icon icon="fa-solid fa-right-from-bracket" class="fs-6" />
                    </button>

                    <button
                      v-if="res.estado === ESTADOS_RESERVA.FINALIZADA"
                      @click="abrirModalFactura(res)"
                      class="btn btn-sm btn-outline-info rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      title="Ver Estado de Cuenta / Factura"
                    >
                      <font-awesome-icon icon="fa-solid fa-receipt" class="fs-6" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="totalPaginas > 1"
          class="d-flex flex-column flex-md-row justify-content-between align-items-center p-3 bg-light border-top"
        >
          <span class="text-muted small fw-bold mb-2 mb-md-0">
            Mostrando página {{ paginaActual }} de {{ totalPaginas }}
          </span>
          <div class="btn-group shadow-sm">
            <button
              @click="cambiarPagina(paginaActual - 1)"
              :disabled="paginaActual === 1"
              class="btn btn-sm btn-white border"
            >
              <font-awesome-icon icon="fa-solid fa-chevron-left" class="me-1" /> Anterior
            </button>
            <button
              @click="cambiarPagina(paginaActual + 1)"
              :disabled="paginaActual === totalPaginas"
              class="btn btn-sm btn-white border"
            >
              Siguiente <font-awesome-icon icon="fa-solid fa-chevron-right" class="ms-1" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <ModalEdicionReserva
      :show="mostrarModalEdicion"
      :reserva="reservaAEditar"
      :modoCheckIn="esModoCheckIn"
      @close="mostrarModalEdicion = false"
      @actualizado="refrescarTabla"
    />
    <ModalFactura
      :show="mostrarModalFactura"
      :reserva="reservaParaFactura"
      @close="mostrarModalFactura = false"
    />
  </div>
</template>

<style scoped>

.eco-card {
  background: linear-gradient(
    135deg,
    rgba(139, 207, 91, 0.08) 0%,
    var(--k-cream) 100%
  );
  border: 1px solid var(--k-border);
}

.eco-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(15, 59, 42, 0.08);
}

.icon-box {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  font-size: 1.2rem;
}

.tone-apple-box {
  background: rgba(139, 207, 91, 0.2);
  color: var(--k-forest);
}

.tone-sky-box {
  background: var(--k-sky-soft);
  color: var(--k-sky);
}

.tone-bed-box {
  background: rgba(36, 64, 58, 0.1);
  color: var(--k-forest);
}

.small-label {
  font-size: 0.75rem;
  letter-spacing: 0.5px;
}

.filter-chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.filter-chip {
  border: 1px solid var(--k-border);
  background: var(--k-offwhite);
  padding: 0.65rem 1rem;
  border-radius: 999px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.filter-chip:hover {
  background: var(--k-apple-soft);
  border-color: rgba(139, 207, 91, 0.35);
}

.filter-chip.active {
  background: rgba(139, 207, 91, 0.2);
  color: var(--k-forest);
  border-color: rgba(139, 207, 91, 0.45);
  box-shadow: 0 8px 18px rgba(139, 207, 91, 0.14);
}

.search-soft,
.search-soft .input-group-text,
.search-soft .form-control {
  background: var(--k-offwhite);
}

.table thead th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.table tbody tr:hover {
  background: rgba(238, 248, 253, 0.32);
}

.btn-group .btn:hover {
  background-color: #f8f9fa;
}

.empty-state-copy {
  font-family: "Handlee", cursive;
  color: var(--k-forest);
}

.badge-soft-apple {
  background: rgba(139, 207, 91, 0.18);
  color: var(--k-forest);
  border: 1px solid rgba(139, 207, 91, 0.45);
}

.badge-soft-sand {
  background: var(--k-sand-soft);
  color: var(--k-sand);
  border: 1px solid rgba(212, 175, 55, 0.32);
}

.badge-soft-sky {
  background: var(--k-sky-soft);
  color: var(--k-sky);
  border: 1px solid rgba(52, 152, 219, 0.25);
}

.badge-soft-neutral {
  background: rgba(36, 64, 58, 0.08);
  color: var(--k-forest);
  border: 1px solid rgba(36, 64, 58, 0.18);
}

.badge-soft-rose {
  background: rgba(229, 184, 184, 0.2);
  color: #8a4c4c;
  border: 1px solid rgba(229, 184, 184, 0.5);
}
</style>
