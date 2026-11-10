/**
 * Formulario de creación/edición de habitaciones. Al editar solo se envían los campos que
 * cambiaron (PATCH); las fotos nuevas se suben aparte (POST /rooms/{id}/images).
 */
import { computed, ref } from "vue";
import Swal from "sweetalert2";
import { errorMessage } from "@/api/apiClient";
import { addRoomImages, createRoom, removeRoomImage, updateRoom } from "@/api/rooms";
import { BASE_AMENITIES } from "@/constants/rooms";
import { brandColors } from "@/utils/brandColors";

export const EDITABLE_ROOM_FIELDS = Object.freeze([
  "number",
  "name",
  "room_type_id",
  "description",
  "price_per_night",
  "capacity",
  "bedrooms",
  "beds",
  "amenities",
  "is_active",
  "operational_status",
  "main_image",
]);

export const emptyRoomForm = () => ({
  number: "",
  name: "",
  room_type_id: "",
  description: "",
  price_per_night: "",
  capacity: 1,
  bedrooms: 1,
  beds: "",
  amenities: [],
  is_active: true,
  operational_status: "available",
  images: [],
  main_image: null,
});

/** Habitación de la API -> estado del formulario (copias, para no mutar la fila de la tabla). */
export const roomToForm = (room) => ({
  number: room.number,
  name: room.name,
  room_type_id: room.room_type?.id || "",
  description: room.description || "",
  price_per_night: room.price_per_night,
  capacity: room.capacity,
  bedrooms: room.bedrooms || 1,
  beds: room.beds || "",
  amenities: [...(room.amenities || [])],
  is_active: room.is_active,
  operational_status: room.operational_status || "available",
  images: [...(room.images || [])],
  main_image: room.main_image || null,
});

/** Estado del formulario -> cuerpo de la API (tipos correctos y textos recortados). */
export const normalizeRoomForm = (form) => ({
  number: String(form.number).trim(),
  name: form.name.trim(),
  room_type_id: form.room_type_id,
  description: (form.description || "").trim(),
  price_per_night: Number(form.price_per_night),
  capacity: Number(form.capacity),
  bedrooms: Number(form.bedrooms),
  beds: (form.beds || "").trim(),
  amenities: form.amenities,
  is_active: form.is_active,
  operational_status: form.operational_status,
  main_image: form.main_image,
});

/** Campos editables cuyo valor normalizado cambió respecto al original. */
export function diffRoomForm(current, original) {
  const now = normalizeRoomForm(current);
  const before = normalizeRoomForm(original);
  const changes = {};
  for (const field of EDITABLE_ROOM_FIELDS) {
    if (JSON.stringify(now[field]) !== JSON.stringify(before[field])) changes[field] = now[field];
  }
  return changes;
}

const clone = (value) => JSON.parse(JSON.stringify(value));

export function useRoomForm() {
  const form = ref(emptyRoomForm());
  const roomId = ref(null);
  const pendingFiles = ref([]);
  const submitting = ref(false);
  let original = null;

  const isEditing = computed(() => roomId.value !== null);

  // Incluye amenidades ya guardadas en la habitación aunque no estén en la lista base.
  const amenityOptions = computed(() => [
    ...BASE_AMENITIES,
    ...(form.value.amenities || []).filter((a) => !BASE_AMENITIES.includes(a)),
  ]);

  function reset() {
    form.value = emptyRoomForm();
    original = null;
    roomId.value = null;
    pendingFiles.value = [];
  }

  function startEdit(room) {
    reset();
    roomId.value = room.id;
    form.value = roomToForm(room);
    original = clone(form.value);
  }

  const missingRequired = () => {
    const { number, name, price_per_night, room_type_id } = form.value;
    return (
      !number ||
      !name ||
      !price_per_night ||
      !room_type_id ||
      (!isEditing.value && !pendingFiles.value.length)
    );
  };

  /** Guarda la habitación. Devuelve true si el modal puede cerrarse. */
  async function save() {
    if (missingRequired()) {
      Swal.fire({
        icon: "error",
        title: "Faltan algunos datos",
        text: "Completa la información principal, el tipo de habitación y al menos una foto para continuar.",
      });
      return false;
    }

    submitting.value = true;
    try {
      const files = pendingFiles.value;
      if (isEditing.value) {
        const changes = diffRoomForm(form.value, original);
        if (Object.keys(changes).length) await updateRoom(roomId.value, changes);
        if (files.length) await addRoomImages(roomId.value, files);
        Swal.fire({
          icon: "success",
          title: "Espacio actualizado",
          text: "Los cambios de la habitación quedaron guardados.",
          timer: 1800,
          showConfirmButton: false,
        });
      } else {
        const { main_image: _mainImage, ...payload } = normalizeRoomForm(form.value);
        const created = await createRoom(payload);
        try {
          await addRoomImages(created.id, files);
          Swal.fire({
            icon: "success",
            title: "Espacio registrado",
            text: "La habitación ahora está lista para recibir huéspedes.",
            timer: 1800,
            showConfirmButton: false,
          });
        } catch (error) {
          Swal.fire(
            "Habitación creada sin fotos",
            errorMessage(error, "No se pudieron subir las fotos. Edítala para intentarlo de nuevo."),
            "warning",
          );
        }
      }
      reset();
      return true;
    } catch (error) {
      Swal.fire({
        icon: "error",
        title: "No pudimos guardar este espacio",
        text: errorMessage(error, "Verifica los datos o tu conexión e inténtalo nuevamente."),
      });
      return false;
    } finally {
      submitting.value = false;
    }
  }

  /** Borra una foto ya guardada (inmediato, con confirmación). Devuelve true si se borró. */
  async function removeImage(imageUrl) {
    const colors = brandColors();
    const result = await Swal.fire({
      title: "¿Borrar esta foto?",
      text: "Se eliminará permanentemente.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: colors.danger,
      cancelButtonColor: colors.forest,
      confirmButtonText: "Sí, borrar",
      cancelButtonText: "Cancelar",
    });
    if (!result.isConfirmed) return false;

    try {
      const updated = await removeRoomImage(roomId.value, imageUrl);
      form.value.images = [...(updated.images || [])];
      form.value.main_image = updated.main_image || null;
      // El servidor ya aplicó el cambio: no debe contarse como pendiente al guardar.
      original.images = [...form.value.images];
      original.main_image = form.value.main_image;
      Swal.fire({ icon: "success", title: "Foto eliminada", timer: 1500, showConfirmButton: false });
      return true;
    } catch (error) {
      Swal.fire("Error", errorMessage(error, "No se pudo eliminar la foto"), "error");
      return false;
    }
  }

  // La foto principal se guarda junto con el resto de cambios al pulsar "Guardar cambios".
  const setMainImage = (imageUrl) => {
    form.value.main_image = imageUrl;
  };

  return {
    form,
    isEditing,
    pendingFiles,
    submitting,
    amenityOptions,
    reset,
    startEdit,
    save,
    removeImage,
    setMainImage,
  };
}
