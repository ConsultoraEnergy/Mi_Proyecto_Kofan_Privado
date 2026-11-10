<script setup>
import { ref, computed, onMounted, watch } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { listUsers, createUser, updateUser, setUserStatus } from "@/api/users";
import { useAuthStore } from "@/stores/auth";
import { DOCUMENT_TYPES, PERMISSIONS, ROLE_LABELS } from "@/constants/booking";
import ModalUsuario from "@/components/ModalUsuario.vue";

const auth = useAuthStore();

const STAFF_ROLES = ["admin", "receptionist"];
const ROLE_ICONS = {
  admin: "fa-solid fa-user-shield",
  receptionist: "fa-solid fa-user-gear",
  client: "fa-solid fa-user",
};

const puedeCrear = computed(() => auth.can(PERMISSIONS.USERS_CREATE));
const puedeEditar = computed(() => auth.can(PERMISSIONS.USERS_UPDATE));
const puedeGestionarPersonal = computed(() => auth.can(PERMISSIONS.USERS_MANAGE_STAFF));

const usuarios = ref([]);
const cargando = ref(false);
const cargandoRegistro = ref(false);
const mostrarModal = ref(false);
const usuarioSeleccionado = ref(null);
const busqueda = ref("");
const filtroRol = ref("");

const paginaActual = ref(1);
const limite = 10;
const totalUsuarios = ref(0);
const totalPaginas = computed(() => Math.max(1, Math.ceil(totalUsuarios.value / limite)));

const documentoLabel = (tipo) => DOCUMENT_TYPES.find((d) => d.value === tipo)?.label || tipo || "";
const esPropio = (user) => user.id === auth.user?.id;
// Sin el permiso users:manage_staff no se pueden modificar cuentas del personal.
const esIntocable = (user) =>
  esPropio(user) || (STAFF_ROLES.includes(user.role) && !puedeGestionarPersonal.value);

const cargarUsuarios = async () => {
  try {
    cargando.value = true;
    const params = { page: paginaActual.value, limit: limite };
    if (busqueda.value.trim()) params.q = busqueda.value.trim();
    if (filtroRol.value) params.role = filtroRol.value;
    const data = await listUsers(params);
    usuarios.value = data.items || [];
    totalUsuarios.value = data.total || 0;
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo obtener la lista de usuarios"), "error");
  } finally {
    cargando.value = false;
  }
};

let timeoutBusqueda = null;
watch(busqueda, () => {
  clearTimeout(timeoutBusqueda);
  timeoutBusqueda = setTimeout(() => {
    paginaActual.value = 1;
    cargarUsuarios();
  }, 350);
});

watch(filtroRol, () => {
  paginaActual.value = 1;
  cargarUsuarios();
});

const cambiarPagina = (delta) => {
  const destino = paginaActual.value + delta;
  if (destino < 1 || destino > totalPaginas.value) return;
  paginaActual.value = destino;
  cargarUsuarios();
};

const abrirNuevo = () => {
  usuarioSeleccionado.value = null;
  mostrarModal.value = true;
};

const abrirEdicion = (user) => {
  usuarioSeleccionado.value = { ...user };
  mostrarModal.value = true;
};

const guardarUsuario = async (datos) => {
  const { id, ...campos } = datos;
  // El backend lo rechazaría igualmente; se avisa antes para dar un mensaje claro.
  if (campos.role && STAFF_ROLES.includes(campos.role) && !puedeGestionarPersonal.value) {
    Swal.fire("Sin permiso", "Solo un administrador puede crear o asignar cuentas del personal.", "warning");
    return;
  }

  try {
    cargandoRegistro.value = true;

    if (id) {
      await updateUser(id, campos);
      Swal.fire("¡Actualizado!", "Los datos del usuario han sido modificados.", "success");
    } else {
      await createUser(campos);
      Swal.fire(
        "¡Creado!",
        "El usuario ha sido registrado y recibirá un correo para definir su contraseña.",
        "success",
      );
    }

    mostrarModal.value = false;
    cargarUsuarios();
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "Hubo un problema al guardar el usuario."), "error");
  } finally {
    cargandoRegistro.value = false;
  }
};

const toggleEstado = async (user) => {
  const estaActivo = user.is_active;
  const accion = estaActivo ? "Suspender" : "Reactivar";
  const colorBoton = estaActivo ? "#d33" : "#0f3b2a";

  const result = await Swal.fire({
    title: `¿${accion} usuario?`,
    text: estaActivo
      ? "El usuario ya no podrá iniciar sesión ni hacer reservas."
      : "El usuario recuperará su acceso al sistema del hotel.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: colorBoton,
    cancelButtonColor: "#6c757d",
    confirmButtonText: `Sí, ${accion.toLowerCase()}`,
    cancelButtonText: "Cancelar",
  });

  if (!result.isConfirmed) return;
  try {
    await setUserStatus(user.id, !estaActivo);
    Swal.fire("¡Listo!", `El usuario ha sido ${estaActivo ? "suspendido" : "reactivado"}.`, "success");
    cargarUsuarios();
  } catch (error) {
    Swal.fire("Error", errorMessage(error, "No se pudo cambiar el estado del usuario."), "error");
  }
};

onMounted(() => {
  cargarUsuarios();
});
</script>

<template>
  <div class="users-manager p-1">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
      <div>
        <h4 class="fw-bold mb-1 text-dark">Gestión de Usuarios</h4>
        <p class="text-muted small mb-0">Administra los accesos de clientes y personal del hotel.</p>
      </div>
      <button v-if="puedeCrear" class="btn btn-dark shadow-sm rounded-pill px-4" @click="abrirNuevo">
        <font-awesome-icon icon="fa-solid fa-user-plus" class="me-2" />
        Nuevo Usuario
      </button>
    </div>

    <div class="d-flex flex-wrap gap-2 mb-3">
      <div class="input-group shadow-sm rounded-pill overflow-hidden bg-white" style="max-width: 360px">
        <span class="input-group-text border-0 bg-white ps-3">
          <font-awesome-icon icon="fa-solid fa-magnifying-glass" class="text-muted" />
        </span>
        <input
          v-model="busqueda"
          type="text"
          class="form-control border-0 shadow-none"
          placeholder="Buscar por nombre, correo o documento..."
        />
      </div>
      <select v-model="filtroRol" class="form-select shadow-sm rounded-pill" style="max-width: 200px">
        <option value="">Todos los roles</option>
        <option v-for="(label, value) in ROLE_LABELS" :key="value" :value="value">{{ label }}</option>
      </select>
    </div>

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th class="ps-4 py-3 text-muted small fw-bold">NOMBRE</th>
              <th class="py-3 text-muted small fw-bold">DOCUMENTO</th>
              <th class="py-3 text-muted small fw-bold">CORREO ELECTRÓNICO</th>
              <th class="py-3 text-muted small fw-bold">ROL</th>
              <th class="py-3 text-muted small fw-bold">ESTADO</th>
              <th v-if="puedeEditar" class="text-center py-3 text-muted small fw-bold">ACCIONES</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="cargando">
              <td colspan="6" class="text-center py-5">
                <div class="spinner-border text-success" role="status"></div>
                <p class="mt-2 text-muted fw-bold">Consultando usuarios del hotel...</p>
              </td>
            </tr>

            <tr v-else-if="usuarios.length === 0">
              <td colspan="6" class="text-center py-5 text-muted">
                <font-awesome-icon
                  icon="fa-solid fa-ban"
                  class="display-4 mb-3 d-block mx-auto text-secondary"
                />
                No se encontraron usuarios registrados.
              </td>
            </tr>

            <template v-else>
              <tr v-for="user in usuarios" :key="user.id" :class="{ 'opacity-50 bg-light': !user.is_active }">
                <td class="ps-4 fw-bold text-dark">
                  {{ user.full_name }}
                  <span v-if="esPropio(user)" class="badge bg-light text-muted border ms-1 fw-normal"
                    >Tú</span
                  >
                </td>

                <td>
                  <span class="text-muted small d-block mb-1">{{ documentoLabel(user.document_type) }}</span>
                  <span class="text-dark">{{ user.document_number || "—" }}</span>
                </td>

                <td class="text-muted">
                  {{ user.email }}
                  <font-awesome-icon
                    v-if="user.email_verified"
                    icon="fa-solid fa-circle-check"
                    class="text-success ms-1"
                    title="Correo verificado"
                  />
                </td>

                <td>
                  <span
                    class="badge rounded-pill px-3 py-2 border"
                    :class="
                      user.role === 'client' ? 'bg-light text-secondary' : 'bg-dark text-white border-dark'
                    "
                  >
                    <font-awesome-icon
                      :icon="ROLE_ICONS[user.role] || ROLE_ICONS.client"
                      class="me-1"
                      :class="user.role === 'client' ? 'text-secondary' : 'text-success'"
                    />
                    {{ ROLE_LABELS[user.role] || user.role }}
                  </span>
                </td>

                <td>
                  <span
                    class="badge rounded-pill px-3 py-2"
                    :class="
                      user.is_active
                        ? 'bg-success bg-opacity-10 text-success border border-success'
                        : 'bg-danger bg-opacity-10 text-danger border border-danger'
                    "
                  >
                    <font-awesome-icon
                      :icon="user.is_active ? 'fa-solid fa-circle-check' : 'fa-solid fa-ban'"
                      class="me-1"
                    />
                    {{ user.is_active ? "Activo" : "Suspendido" }}
                  </span>
                </td>

                <td v-if="puedeEditar" class="text-center align-middle">
                  <div class="d-flex justify-content-center gap-2">
                    <button
                      :disabled="esIntocable(user)"
                      class="btn btn-sm btn-outline-dark rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      :title="esPropio(user) ? 'Edita tu cuenta desde tu perfil' : 'Editar'"
                      @click="abrirEdicion(user)"
                    >
                      <font-awesome-icon icon="fa-regular fa-pen-to-square" class="fs-6" />
                    </button>

                    <button
                      :disabled="esIntocable(user)"
                      class="btn btn-sm rounded-circle d-inline-flex align-items-center justify-content-center shadow-sm"
                      style="width: 35px; height: 35px"
                      :class="user.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                      :title="
                        esPropio(user)
                          ? 'No puedes suspender tu propia cuenta'
                          : user.is_active
                            ? 'Suspender'
                            : 'Reactivar'
                      "
                      @click="toggleEstado(user)"
                    >
                      <font-awesome-icon
                        :icon="user.is_active ? 'fa-solid fa-lock' : 'fa-solid fa-rotate'"
                        class="fs-6"
                      />
                    </button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div
        class="card-footer bg-light border-top border-0 d-flex flex-column flex-md-row justify-content-between align-items-center p-3"
      >
        <span class="text-muted small fw-bold mb-2 mb-md-0">
          Página {{ paginaActual }} de {{ totalPaginas }} · {{ totalUsuarios }} usuarios
        </span>
        <div class="btn-group shadow-sm">
          <button
            class="btn btn-sm btn-white border bg-white"
            :disabled="paginaActual === 1 || cargando"
            @click="cambiarPagina(-1)"
          >
            <font-awesome-icon icon="fa-solid fa-chevron-left" class="me-1" /> Anterior
          </button>
          <button
            class="btn btn-sm btn-white border bg-white"
            :disabled="paginaActual >= totalPaginas || cargando"
            @click="cambiarPagina(1)"
          >
            Siguiente <font-awesome-icon icon="fa-solid fa-chevron-right" class="ms-1" />
          </button>
        </div>
      </div>
    </div>

    <ModalUsuario
      v-if="mostrarModal"
      :show="true"
      :cargando="cargandoRegistro"
      :usuario-editando="usuarioSeleccionado"
      @cerrar="mostrarModal = false"
      @guardar="guardarUsuario"
    />
  </div>
</template>

<style scoped>
.card {
  border-radius: 15px;
}
.table thead th {
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 700;
  color: #888;
}
.badge {
  font-weight: 500;
  font-size: 0.8rem;
}
</style>
