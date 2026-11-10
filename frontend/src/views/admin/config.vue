<script setup>
import { ref, onMounted } from "vue";
import { errorMessage } from "@/api/apiClient";
import { getSiteSettings, updateSiteSettings, uploadLogo } from "@/api/content";
import { assetUrl } from "@/config/env";
import { useConfigStore } from "@/stores/config";

const configStore = useConfigStore();

// Claves exactas que acepta PUT /settings (logo_url y deposit_percent no se envían).
const SETTINGS_KEYS = [
  "hotel_name",
  "tagline",
  "legal_name",
  "tax_id",
  "contact_email",
  "phone",
  "whatsapp_number",
  "address",
  "city",
  "country",
  "check_in_time",
  "check_out_time",
  "currency",
  "tax_percentage",
  "social_facebook",
  "social_instagram",
  "social_tiktok",
  "payment_instructions",
  "about_description",
  "mission",
  "vision",
];

const isLoading = ref(true);
const isSaving = ref(false);
const isUploadingLogo = ref(false);
const message = ref({ text: "", type: "" });
const fileInput = ref(null);
let messageTimer = null;

const config = ref({
  hotel_name: "",
  tagline: "",
  logo_url: "",
  legal_name: "",
  tax_id: "",
  contact_email: "",
  phone: "",
  whatsapp_number: "",
  address: "",
  city: "",
  country: "Colombia",
  check_in_time: "15:00",
  check_out_time: "11:00",
  currency: "COP",
  tax_percentage: 0,
  social_facebook: "",
  social_instagram: "",
  social_tiktok: "",
  payment_instructions: "",
  about_description: "",
  mission: "",
  vision: "",
});

const showMessage = (text, type) => {
  message.value = { text, type };
  clearTimeout(messageTimer);
  messageTimer = setTimeout(() => (message.value.text = ""), 4000);
};

const handleLogoUpload = async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;

  isUploadingLogo.value = true;
  try {
    const result = await uploadLogo(file);
    config.value.logo_url = result.logo_url;
    configStore.setData(result);
    showMessage("Perfecto, el logo del hotel ya está actualizado.", "success");
  } catch (error) {
    showMessage(
      errorMessage(error, "No pudimos actualizar la imagen por ahora. Inténtalo nuevamente."),
      "danger",
    );
  } finally {
    isUploadingLogo.value = false;
  }
};

const loadSettings = async () => {
  try {
    const data = await getSiteSettings();
    if (data) config.value = { ...config.value, ...data };
  } catch (error) {
    showMessage(errorMessage(error, "No se pudo cargar la configuración del hotel."), "danger");
  } finally {
    isLoading.value = false;
  }
};

const buildPayload = () => {
  const payload = {};
  SETTINGS_KEYS.forEach((key) => {
    const value = config.value[key];
    payload[key] = typeof value === "string" ? value.trim() : value;
  });
  payload.tax_percentage = Number(payload.tax_percentage) || 0;
  return payload;
};

const handleSave = async () => {
  isSaving.value = true;
  message.value = { text: "", type: "" };

  try {
    const result = await updateSiteSettings(buildPayload());
    config.value = { ...config.value, ...result };
    configStore.setData(result);
    showMessage("Listo, los cambios quedaron guardados correctamente.", "success");
  } catch (error) {
    showMessage(
      errorMessage(error, "No pudimos guardar por ahora. Tus datos siguen seguros; intentemos nuevamente."),
      "danger",
    );
  } finally {
    isSaving.value = false;
  }
};

onMounted(loadSettings);
</script>

<template>
  <div class="container-fluid py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
      <div>
        <p class="brand-handmade mb-1">Detalles que acompañan cada bienvenida</p>
        <h2 class="fw-bold section-title text-brand mb-0">
          <font-awesome-icon icon="fa-solid fa-hotel" class="me-2" />Configuración del Hotel
        </h2>
      </div>
      <button class="btn btn-brand px-4 shadow-sm" :disabled="isSaving || isLoading" @click="handleSave">
        <span v-if="isSaving" class="spinner-border spinner-border-sm me-2"></span>
        <font-awesome-icon v-else icon="fa-solid fa-circle-check" class="me-2" />
        Guardar cambios del hotel
      </button>
    </div>

    <div
      v-if="message.text"
      :class="['alert alert-dismissible fade show shadow-sm alert-handmade', `alert-${message.type}`]"
      style="border-radius: 12px"
    >
      {{ message.text }}
    </div>

    <div v-if="isLoading" class="text-center py-5">
      <div class="spinner-border verde-brand" role="status"></div>
      <p class="mt-2 text-muted brand-handmade">Preparando los detalles del hotel...</p>
    </div>

    <div v-else class="card config-card eco-card shadow-sm border-0">
      <div class="card-body p-0">
        <div class="row g-0">
          <div class="col-md-3 border-end bg-light p-3 sidebar-config">
            <div id="v-pills-tab" class="nav flex-column nav-pills" role="tablist">
              <button class="nav-link active text-start mb-2" data-bs-toggle="pill" data-bs-target="#general">
                <font-awesome-icon icon="fa-solid fa-circle-info" class="me-2" />Esencia del hotel
              </button>
              <button class="nav-link text-start mb-2" data-bs-toggle="pill" data-bs-target="#hotel">
                <font-awesome-icon icon="fa-solid fa-hotel" class="me-2" />Operación diaria
              </button>
              <button class="nav-link text-start mb-2" data-bs-toggle="pill" data-bs-target="#pagos">
                <font-awesome-icon icon="fa-solid fa-hand-holding-dollar" class="me-2" />Pagos y textos
              </button>
              <button class="nav-link text-start mb-2" data-bs-toggle="pill" data-bs-target="#social">
                <font-awesome-icon icon="fa-solid fa-share-nodes" class="me-2" />Canales de contacto
              </button>
            </div>
          </div>

          <div class="col-md-9 p-4 p-lg-5">
            <form @submit.prevent="handleSave">
              <div class="tab-content">
                <div id="general" class="tab-pane fade show active">
                  <h5 class="mb-4 fw-bold text-dark">Información Principal</h5>
                  <div class="row g-3">
                    <div class="col-md-12 mb-4 text-center">
                      <label class="form-label d-block fw-semibold text-muted mb-3">Logo Actual</label>
                      <div class="mb-3">
                        <img
                          v-if="config.logo_url"
                          :src="assetUrl(config.logo_url)"
                          alt="Logo Preview"
                          class="img-thumbnail shadow-sm p-2"
                          style="max-height: 120px; border-radius: 15px"
                        />
                        <p v-else class="text-muted small mb-0">Aún no hay un logo cargado.</p>
                      </div>
                      <input
                        ref="fileInput"
                        type="file"
                        class="d-none"
                        accept="image/jpeg,image/png,image/webp"
                        @change="handleLogoUpload"
                      />
                      <button
                        type="button"
                        class="btn btn-outline-secondary btn-sm"
                        style="border-radius: 10px"
                        :disabled="isUploadingLogo"
                        @click="fileInput.click()"
                      >
                        <span v-if="isUploadingLogo" class="spinner-border spinner-border-sm me-2"></span>
                        <font-awesome-icon v-else icon="fa-solid fa-camera" class="me-2" />Cambiar Logo
                      </button>
                    </div>

                    <div class="col-md-12">
                      <label class="form-label fw-semibold small ms-1">Nombre del Hospedaje</label>
                      <input
                        v-model="config.hotel_name"
                        type="text"
                        class="form-control custom-input"
                        required
                        minlength="2"
                        maxlength="120"
                      />
                    </div>
                    <div class="col-md-12">
                      <label class="form-label fw-semibold small ms-1">Frase de bienvenida (eslogan)</label>
                      <input
                        v-model="config.tagline"
                        type="text"
                        class="form-control custom-input"
                        maxlength="300"
                      />
                    </div>
                    <div class="col-md-8">
                      <label class="form-label fw-semibold small ms-1">Razón social</label>
                      <input
                        v-model="config.legal_name"
                        type="text"
                        class="form-control custom-input"
                        maxlength="300"
                        placeholder="Si está vacío se usa el nombre del hospedaje"
                      />
                    </div>
                    <div class="col-md-4">
                      <label class="form-label fw-semibold small ms-1">NIT</label>
                      <input
                        v-model="config.tax_id"
                        type="text"
                        class="form-control custom-input"
                        maxlength="30"
                      />
                    </div>
                    <div class="col-12">
                      <p class="small text-muted ms-1 mb-0">
                        La razón social, el NIT, la dirección y el contacto aparecen en la política de
                        tratamiento de datos.
                      </p>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Email de Contacto</label>
                      <input
                        v-model="config.contact_email"
                        type="email"
                        class="form-control custom-input"
                        maxlength="300"
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Teléfono Principal</label>
                      <input
                        v-model="config.phone"
                        type="text"
                        class="form-control custom-input"
                        maxlength="300"
                      />
                    </div>
                    <div class="col-md-12">
                      <label class="form-label fw-semibold small ms-1">Dirección Física</label>
                      <input
                        v-model="config.address"
                        type="text"
                        class="form-control custom-input"
                        maxlength="300"
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Ciudad</label>
                      <input
                        v-model="config.city"
                        type="text"
                        class="form-control custom-input"
                        maxlength="300"
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">País</label>
                      <input
                        v-model="config.country"
                        type="text"
                        class="form-control custom-input"
                        maxlength="300"
                      />
                    </div>
                  </div>
                </div>

                <div id="hotel" class="tab-pane fade">
                  <h5 class="mb-4 fw-bold text-dark">Parámetros de Reserva</h5>
                  <div class="row g-3">
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Hora de Check-in</label>
                      <input
                        v-model="config.check_in_time"
                        type="time"
                        class="form-control custom-input"
                        required
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Hora de Check-out</label>
                      <input
                        v-model="config.check_out_time"
                        type="time"
                        class="form-control custom-input"
                        required
                      />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Moneda Base</label>
                      <select v-model="config.currency" class="form-select custom-input">
                        <option value="COP">Peso Colombiano (COP)</option>
                        <option value="USD">Dólar (USD)</option>
                      </select>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Impuesto / IVA (%)</label>
                      <input
                        v-model.number="config.tax_percentage"
                        type="number"
                        min="0"
                        max="100"
                        step="any"
                        class="form-control custom-input"
                      />
                    </div>
                  </div>
                </div>

                <div id="pagos" class="tab-pane fade">
                  <h5 class="mb-2 fw-bold text-dark">Datos para transferir el anticipo</h5>
                  <p class="text-muted small mb-3">
                    No hay pasarela de pago: el huésped transfiere el anticipo y sube el comprobante, que el
                    hotel verifica a mano. Estos datos se muestran al reservar (banco, tipo y número de
                    cuenta, titular, llaves de pago, etc.).
                  </p>
                  <textarea
                    v-model="config.payment_instructions"
                    class="form-control custom-input mb-4"
                    rows="5"
                    maxlength="4000"
                    placeholder="Ej: Bancolombia · Cuenta de ahorros 000-000000-00 · Titular: ... · NIT ..."
                  ></textarea>

                  <h5 class="mb-3 fw-bold text-dark">Textos institucionales</h5>
                  <div class="row g-3">
                    <div class="col-12">
                      <label class="form-label fw-semibold small ms-1">Descripción "Sobre nosotros"</label>
                      <textarea
                        v-model="config.about_description"
                        class="form-control custom-input"
                        rows="4"
                        maxlength="4000"
                      ></textarea>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Misión</label>
                      <textarea
                        v-model="config.mission"
                        class="form-control custom-input"
                        rows="4"
                        maxlength="4000"
                      ></textarea>
                    </div>
                    <div class="col-md-6">
                      <label class="form-label fw-semibold small ms-1">Visión</label>
                      <textarea
                        v-model="config.vision"
                        class="form-control custom-input"
                        rows="4"
                        maxlength="4000"
                      ></textarea>
                    </div>
                  </div>
                </div>

                <div id="social" class="tab-pane fade">
                  <h5 class="mb-4 fw-bold text-dark">Presencia Digital</h5>
                  <div class="row g-4">
                    <div class="col-md-12">
                      <label class="form-label fw-semibold small ms-1">Facebook URL</label>
                      <div class="position-relative">
                        <font-awesome-icon
                          :icon="['fab', 'facebook-f']"
                          class="text-primary position-absolute top-50 translate-middle-y ms-3 fs-5"
                        />
                        <input
                          v-model="config.social_facebook"
                          type="url"
                          class="form-control custom-input ps-5 py-2"
                          style="border-radius: 12px"
                          placeholder="https://facebook.com/..."
                        />
                      </div>
                    </div>

                    <div class="col-md-12">
                      <label class="form-label fw-semibold small ms-1">Instagram URL</label>
                      <div class="position-relative">
                        <font-awesome-icon
                          :icon="['fab', 'instagram']"
                          class="text-danger position-absolute top-50 translate-middle-y ms-3 fs-5"
                        />
                        <input
                          v-model="config.social_instagram"
                          type="url"
                          class="form-control custom-input ps-5 py-2"
                          style="border-radius: 12px"
                          placeholder="https://instagram.com/..."
                        />
                      </div>
                    </div>

                    <div class="col-md-12">
                      <label class="form-label fw-semibold small ms-1">TikTok URL</label>
                      <div class="position-relative">
                        <font-awesome-icon
                          :icon="['fab', 'tiktok']"
                          class="text-dark position-absolute top-50 translate-middle-y ms-3 fs-5"
                        />
                        <input
                          v-model="config.social_tiktok"
                          type="url"
                          class="form-control custom-input ps-5 py-2"
                          style="border-radius: 12px"
                          placeholder="https://tiktok.com/@..."
                        />
                      </div>
                    </div>

                    <div class="col-md-12">
                      <label class="form-label fw-semibold small ms-1">Número de WhatsApp</label>
                      <div class="position-relative">
                        <font-awesome-icon
                          :icon="['fab', 'whatsapp']"
                          class="text-success position-absolute top-50 translate-middle-y ms-3 fs-5"
                        />
                        <input
                          v-model="config.whatsapp_number"
                          type="text"
                          class="form-control custom-input ps-5 py-2"
                          style="border-radius: 12px"
                          placeholder="Ej: 573001234567"
                        />
                      </div>
                      <div class="form-text small ms-2 mt-1 opacity-75">
                        Incluye el indicativo (ej. 57 para Colombia) sin el símbolo "+".
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.verde-brand {
  color: var(--k-forest) !important;
}

.config-card {
  border-radius: 20px;
  overflow: hidden;
}

.sidebar-config {
  min-height: 400px;
  background: linear-gradient(180deg, #f8fcfe 0%, var(--k-forest-soft) 100%);
}

.nav-pills .nav-link {
  color: var(--k-text);
  border-radius: 14px;
  padding: 0.8rem 1rem;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.nav-pills .nav-link.active {
  background-color: rgba(139, 207, 91, 0.22);
  color: var(--k-forest);
  border-color: rgba(139, 207, 91, 0.45);
}

.nav-pills .nav-link:hover:not(.active) {
  background-color: rgba(255, 255, 255, 0.75);
  border-color: #d6edf7;
}

.custom-input {
  border-radius: 18px !important;
  padding: 0.65rem 1rem;
  font-size: 0.95rem;
  border-color: var(--k-border);
  background: rgba(255, 255, 255, 0.95);
}

.custom-input:focus {
  border-color: var(--k-sky-strong);
  box-shadow: 0 0 0 0.25rem rgba(143, 211, 255, 0.28);
}

.btn-brand:disabled {
  background-color: rgba(139, 207, 91, 0.55) !important;
  border-color: rgba(139, 207, 91, 0.55) !important;
}
</style>
