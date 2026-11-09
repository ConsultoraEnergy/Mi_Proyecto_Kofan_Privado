import { defineStore } from "pinia";
import { ref, reactive, computed } from "vue"; // 🟢 Añadimos computed
import Swal from "sweetalert2";
import apiClient from "@/api/apiClient";
import { useAuthStore } from "@/stores/auth";

const getBrandColor = (token, fallback) =>
  typeof window !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
    : fallback;

const COLOR_FOREST = getBrandColor("--k-forest", "#0f3b2a");
const COLOR_DANGER = getBrandColor("--k-danger", "#e74c3c");

export const useReservaStore = defineStore("reserva", () => {
  const isModalOpen = ref(false);
  const isSubmitting = ref(false);
  const habitacionSeleccionada = ref(null);

  const selectedDateRange = ref(null); 
  const disabledDates = ref([]); 
  const minDate = ref(new Date().toISOString().split("T")[0]); 

  const form = reactive({
    nombreCompleto: "",
    correo: "",
    telefono: "",
    comprobante: null,
    comprobantePreview: null
  });

  const errors = reactive({
    nombreCompleto: false,
    correo: false,
    telefono: false,
    dates: false,
    comprobante: false // 🟢 Nuevo validador
  });

  // 🟢 CALCULADORA REACTIVA DEL TOTAL A PAGAR
  const totalCalculado = computed(() => {
    if (!selectedDateRange.value?.start || !selectedDateRange.value?.end || !habitacionSeleccionada.value) {
      return 0;
    }
    const checkIn = selectedDateRange.value.start;
    const checkOut = selectedDateRange.value.end;
    const diasEstadia = Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24)) || 1;
    return habitacionSeleccionada.value.price * diasEstadia;
  });

  // Función para formatear moneda en Vue
  const totalFormateado = computed(() => {
    return totalCalculado.value.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
  });
  const anticipoCalculado = computed(() => totalCalculado.value / 2);
  const anticipoFormateado = computed(() => {
    return anticipoCalculado.value.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0  });
  });

  const handleFileUpload = (event) => {
    const file = event.target?.files[0] || event.dataTransfer?.files[0]; // Soporta clic y arrastrar
    if (file) {
      form.comprobante = file;
      
      // Si es imagen, creamos la vista previa. Si es PDF, ponemos un icono genérico.
      if (file.type.startsWith('image/')) {
        form.comprobantePreview = URL.createObjectURL(file);
      } else if (file.type === 'application/pdf') {
        form.comprobantePreview = 'pdf-icon'; // Una bandera para saber que es PDF
      }
    }
  };

  const openModal = async (habitacion = null) => {
    isModalOpen.value = true;
    clearErrors();
    selectedDateRange.value = null;

    if (habitacion) {
      habitacionSeleccionada.value = { ...habitacion };
      await fetchDisabledDates(habitacion.id || habitacion._id);
    }
  };

  const fetchDisabledDates = async (roomId) => {
    try {
      disabledDates.value = []; 
      const response = await apiClient.get(`/rooms/${roomId}/booked-dates`);
      
      disabledDates.value = response.data.map(reserva => {
        const fEntradaStr = reserva.fecha_entrada.toString().split('T')[0];
        const fSalidaStr = reserva.fecha_salida.toString().split('T')[0];
        const [inYear, inMonth, inDay] = fEntradaStr.split('-');
        const [outYear, outMonth, outDay] = fSalidaStr.split('-');
        
        // 1. Creamos los objetos Date
        const start = new Date(inYear, inMonth - 1, inDay);
        const end = new Date(outYear, outMonth - 1, outDay);
        
        // 2. Le restamos un día a la salida (El check-out queda libre)
        end.setDate(end.getDate() - 1);
        
        // 3. Protección anti-errores
        if (end < start) {
          end.setTime(start.getTime()); 
        }

        // 🟢 EL FIX: Retornamos los objetos que ya calculamos
        return {
          start: start,
          end: end
        };
      }).filter(r => r.start && r.end); 
      
    } catch (error) {
      console.error("Error cargando fechas ocupadas:", error);
    }
  };

  const closeModal = () => {
    isModalOpen.value = false;
    resetForm();
  };

  const clearErrors = () => {
    Object.keys(errors).forEach((key) => (errors[key] = false));
  };

  const resetForm = () => {
    form.nombreCompleto = "";
    form.correo = "";
    form.telefono = "";
    form.comprobante = null;
    
    if (form.comprobantePreview && form.comprobantePreview !== 'pdf-icon') {
      URL.revokeObjectURL(form.comprobantePreview);
    }
    form.comprobantePreview = null;
    
    selectedDateRange.value = null; 
    habitacionSeleccionada.value = null;
    clearErrors();
  };

  

  const validateForm = () => {
    let isValid = true;
    clearErrors();

    if (!selectedDateRange.value?.start || !selectedDateRange.value?.end) { 
      errors.dates = true; isValid = false; 
    }
    if (!form.nombreCompleto.trim()) { errors.nombreCompleto = true; isValid = false; }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!form.correo || !emailRegex.test(form.correo)) { errors.correo = true; isValid = false; }
    if (!form.telefono) { errors.telefono = true; isValid = false; }
    if (!form.comprobante) { errors.comprobante = true; isValid = false; }
    
    
    return isValid;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      Swal.fire({
        icon: "error",
        title: "Faltan datos",
        text: "Verifica que hayas seleccionado fechas, llenado tus datos y/o subido el comprobante.",
        confirmButtonColor: COLOR_FOREST,
      });
      return false; 
    }

    isSubmitting.value = true;

    const checkIn = selectedDateRange.value.start;
    const checkOut = selectedDateRange.value.end;
    
    const formatLocal = (dateObj) => {
      const year = dateObj.getFullYear();
      const month = String(dateObj.getMonth() + 1).padStart(2, '0');
      const day = String(dateObj.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    const fechaInString = formatLocal(checkIn);
    const fechaOutString = formatLocal(checkOut);

    Swal.fire({
      title: "Enviando Reserva y Comprobante...",
      allowOutsideClick: false,
      didOpen: () => { Swal.showLoading(); },
    });

    try {
      // 🟢 EL FIX: Cambiamos JSON por FormData porque hay un archivo de por medio
      const formData = new FormData();
      
      formData.append("habitacion_id", habitacionSeleccionada.value.id || habitacionSeleccionada.value._id);
      formData.append("fecha_entrada", fechaInString);
      formData.append("fecha_salida", fechaOutString);
      formData.append("observaciones", "Reserva web pública con comprobante adjunto.");
      formData.append("tipo_persona", "natural");
      formData.append("tipo_documento", "CC");
      formData.append("cliente_documento", "0");
      formData.append("cliente_nombre", form.nombreCompleto.trim());
      formData.append("cliente_email", form.correo.trim());
      formData.append("cliente_celular", form.telefono.toString());

      if (form.comprobante) {
        formData.append("comprobante", form.comprobante);
      }

      const auth = useAuthStore();
      const tokenGuardado = localStorage.getItem("token"); 
      const usuarioConfirmado = auth.isLogged || tokenGuardado !== null;
      
      const endpoint = usuarioConfirmado ? "/api/reservas/" : "/api/reservas/invitado";

      // Usamos multipart/form-data
      await apiClient.post(endpoint, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      await Swal.fire({
        icon: "success",
        title: "¡Reserva Solicitada!",
        text: `Hemos recibido tu comprobante, ${form.nombreCompleto.split(' ')[0]}. Lo verificaremos y te contactaremos pronto.`,
        confirmButtonColor: COLOR_FOREST,
      });

      closeModal();
      return true;

    } catch (error) {
      console.error("Error del backend:", error);
      Swal.fire({
        icon: "error",
        title: "Ups, algo salió mal",
        text: "No pudimos enviar tu reserva ni el comprobante. Intenta de nuevo.",
        confirmButtonColor: COLOR_DANGER,
      });
      return false;
    } finally {
      isSubmitting.value = false;
    }
  };
  const removerComprobante = () => {
    if (form.comprobantePreview && form.comprobantePreview !== 'pdf-icon') {
      URL.revokeObjectURL(form.comprobantePreview);
    }
    form.comprobante = null;
    form.comprobantePreview = null;
  };


  return {
    isModalOpen, isSubmitting, form, errors, selectedDateRange, disabledDates, minDate,
    habitacionSeleccionada, totalCalculado, totalFormateado, anticipoCalculado,
    openModal, closeModal, handleSubmit, resetForm, handleFileUpload, removerComprobante, anticipoFormateado
  };
});