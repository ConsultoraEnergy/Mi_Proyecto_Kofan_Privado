<script setup>
import { ref, watch } from 'vue';
import { listAuditLogs } from '@/api/operations';
import { errorMessage } from '@/api/apiClient';
import { formatDateTime } from '@/utils/format';

const props = defineProps({
  show: Boolean,
  // Opcional: limitar el historial a una habitación concreta.
  roomId: { type: String, default: null },
  roomLabel: { type: String, default: '' },
});

defineEmits(['close']);

const ACTIONS = {
  create: { label: 'Creación', badge: 'bg-success-subtle text-success' },
  update: { label: 'Actualización', badge: 'bg-primary-subtle text-primary' },
  delete: { label: 'Eliminación', badge: 'bg-danger-subtle text-danger' },
  add_images: { label: 'Fotos agregadas', badge: 'bg-info-subtle text-info-emphasis' },
  remove_image: { label: 'Foto eliminada', badge: 'bg-warning-subtle text-warning-emphasis' },
};

const FIELD_LABELS = {
  number: 'Número',
  name: 'Nombre',
  room_type_id: 'Tipo de habitación',
  description: 'Descripción',
  price_per_night: 'Precio por noche',
  capacity: 'Capacidad',
  bedrooms: 'Habitaciones',
  beds: 'Camas',
  amenities: 'Comodidades',
  is_active: 'Habilitada para la venta',
  operational_status: 'Estado operativo',
  main_image: 'Imagen principal',
  images: 'Imágenes',
};

const STATUS_LABELS = {
  available: 'Disponible',
  cleaning: 'En limpieza',
  maintenance: 'En mantenimiento',
  out_of_service: 'Fuera de servicio',
};

const logs = ref([]);
const isLoading = ref(false);
const loadError = ref('');
const currentPage = ref(1);
const totalPages = ref(1);
const totalRecords = ref(0);
const limit = 8;

const expandedRows = ref([]);

const actionMeta = (action) => ACTIONS[action] || { label: action, badge: 'bg-secondary-subtle text-secondary' };
const fieldLabel = (field) => FIELD_LABELS[field] || field;

const formatValue = (value) => {
  if (value === null || value === undefined || value === '') return 'Vacío';
  if (typeof value === 'boolean') return value ? 'Sí' : 'No';
  if (Array.isArray(value)) return value.length ? value.join(', ') : 'Vacío';
  if (typeof value === 'object') return JSON.stringify(value);
  return STATUS_LABELS[value] || String(value);
};

const fetchLogs = async (page = 1) => {
  isLoading.value = true;
  loadError.value = '';
  try {
    const params = { entity: 'room', page, limit };
    if (props.roomId) params.entity_id = props.roomId;
    const response = await listAuditLogs(params);
    logs.value = response.items || [];
    totalRecords.value = response.total || 0;
    totalPages.value = Math.max(1, Math.ceil(totalRecords.value / limit));
    currentPage.value = response.page || page;
    expandedRows.value = [];
  } catch (error) {
    loadError.value = errorMessage(error, 'No se pudo cargar el historial.');
    logs.value = [];
  } finally {
    isLoading.value = false;
  }
};

const toggleRow = (logId) => {
  const index = expandedRows.value.indexOf(logId);
  if (index === -1) expandedRows.value.push(logId);
  else expandedRows.value.splice(index, 1);
};

const nextPage = () => { if (currentPage.value < totalPages.value) fetchLogs(currentPage.value + 1); };
const prevPage = () => { if (currentPage.value > 1) fetchLogs(currentPage.value - 1); };

watch(() => props.show, (visible) => {
  if (visible) fetchLogs(1);
});
</script>

<template>
  <div v-if="show" class="modal-backdrop fade show"></div>
  <div class="modal fade show d-block" tabindex="-1" role="dialog" v-if="show" @click.self="$emit('close')">
    <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
      <div class="modal-content border-0 shadow-lg rounded-4">

        <div class="modal-header bg-dark text-white border-0">
          <h5 class="modal-title fw-bold">
            <font-awesome-icon icon="fa-solid fa-clock" class="me-2" /> Registro de Auditoría de Habitaciones
            <span v-if="roomLabel" class="fw-normal small ms-1">— {{ roomLabel }}</span>
          </h5>
          <button type="button" class="btn-close btn-close-white" @click="$emit('close')"></button>
        </div>

        <div class="modal-body p-0 bg-light">
          <div v-if="isLoading" class="text-center py-5">
            <div class="spinner-border text-success" role="status"></div>
            <p class="text-muted mt-2 small">Cargando registros...</p>
          </div>

          <div v-else-if="loadError" class="alert alert-danger m-3 small">{{ loadError }}</div>

          <div v-else-if="logs.length === 0" class="text-center py-5 text-muted">
            No hay movimientos registrados.
          </div>

          <div v-else class="table-responsive">
            <table class="table table-hover align-middle mb-0 bg-white">
              <thead class="table-light text-muted small text-uppercase">
                <tr>
                  <th class="ps-4">Fecha y Hora</th>
                  <th>Habitación</th>
                  <th>Acción</th>
                  <th>Usuario</th>
                  <th class="text-end pe-4">Detalles</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="log in logs" :key="log.id">
                  <tr>
                    <td class="ps-4 small text-muted">{{ formatDateTime(log.created_at) }}</td>
                    <td class="fw-bold">{{ log.entity_label || '—' }}</td>
                    <td>
                      <span class="badge" :class="actionMeta(log.action).badge">
                        {{ actionMeta(log.action).label }}
                      </span>
                    </td>
                    <td class="small">{{ log.actor ? log.actor.split('@')[0] : 'Sistema' }}</td>
                    <td class="text-end pe-4">
                      <button v-if="log.changes && log.changes.length > 0"
                              @click="toggleRow(log.id)"
                              class="btn btn-sm btn-outline-dark rounded-pill" style="font-size: 0.75rem;">
                        {{ expandedRows.includes(log.id) ? 'Ocultar' : 'Ver Cambios' }}
                      </button>
                      <span v-else class="text-muted small" style="font-size: 0.75rem;">Sin cambios de campos</span>
                    </td>
                  </tr>

                  <tr v-if="expandedRows.includes(log.id)">
                    <td colspan="5" class="bg-light p-0">
                      <div class="p-3 ps-5 border-start border-4 border-primary bg-white m-2 rounded shadow-sm">
                        <h6 class="fw-bold small mb-2 text-muted">Valores Modificados:</h6>
                        <div class="row g-2">
                          <div v-for="(change, idx) in log.changes" :key="idx" class="col-md-4">
                            <div class="p-2 border rounded text-break" style="font-size: 0.8rem;">
                              <div class="fw-bold text-uppercase mb-1">{{ fieldLabel(change.field) }}</div>
                              <div class="text-danger text-decoration-line-through">De: {{ formatValue(change.old) }}</div>
                              <div class="text-success fw-bold">A: {{ formatValue(change.new) }}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>

        <div class="modal-footer bg-white border-top-0 d-flex justify-content-between align-items-center p-3">
          <span class="text-muted small">Total: {{ totalRecords }} registros</span>

          <div class="d-flex align-items-center gap-3">
            <button @click="prevPage" :disabled="currentPage === 1" class="btn btn-sm btn-outline-secondary rounded-pill px-3">
              <font-awesome-icon icon="fa-solid fa-chevron-left" /> Anterior
            </button>
            <span class="small fw-bold text-dark">Pág. {{ currentPage }} de {{ totalPages }}</span>
            <button @click="nextPage" :disabled="currentPage >= totalPages" class="btn btn-sm btn-outline-secondary rounded-pill px-3">
              Siguiente <font-awesome-icon icon="fa-solid fa-chevron-right" />
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop { background-color: rgba(0, 0, 0, 0.5); }
.modal { display: block; z-index: 1055; }
</style>
