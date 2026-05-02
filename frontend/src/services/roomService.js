import apiClient from '@/api/apiClient';
// 1. CREAR (Con múltiples imágenes/FormData)
export const createRoom = async (roomDetails, imageFilesArray) => {
  const formData = new FormData();

  // 1. Usamos 'roomDetails' que es el nombre correcto del parámetro
  formData.append("room_number", roomDetails.room_number);
  formData.append("name", roomDetails.name);
  formData.append("price", roomDetails.price);
  formData.append("capacity", roomDetails.capacity);
  formData.append("active", roomDetails.active);
  formData.append("type", roomDetails.type);
  formData.append('num_cuartos', roomDetails.num_cuartos);
  formData.append('tipo_camas', roomDetails.tipo_camas);

  // 2. Descripción: la agregamos solo si existe y no está vacía
  if (roomDetails.description && roomDetails.description.trim() !== "") {
    formData.append("description", roomDetails.description.trim());
  }

  // 3. Imágenes: Nos aseguramos de extraer el archivo real (.file)
  if (imageFilesArray && imageFilesArray.length > 0) {
    imageFilesArray.forEach((imgItem) => {
      // Como tu componente manda { file: File, previewUrl: '...' }, extraemos 'file'
      const archivoReal = imgItem.file ? imgItem.file : imgItem;
      formData.append("images", archivoReal); 
    });
  }

  if (roomDetails.amenities && roomDetails.amenities.length > 0) {
    roomDetails.amenities.forEach(amenidad => {
      formData.append('amenities', amenidad); // Se envía uno por uno
    });
  }

  // --- LOG DE DEPURACIÓN (Súper útil) ---
  console.log("--- REVISANDO QUÉ LLEVA EL FORMDATA ---");
  for (let [key, value] of formData.entries()) {
    // Si es un archivo, mostramos su nombre para no imprimir basura en la consola
    if (value instanceof File) {
      console.log(`${key}: [Archivo -> ${value.name}]`);
    } else {
      console.log(`${key}:`, value);
    }
  }
  console.log("---------------------------------------");

  // 4. Enviamos la petición indicando que es un formulario con archivos
  const response = await apiClient.post('/rooms/create-with-images', formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  
  return response.data;
};

// 2. OBTENER
export const getRooms = async () => {
  const response = await apiClient.get('/rooms/');
  return response.data; 
};

// 3. ACTUALIZAR (Datos básicos)
export const updateRoom = async (id, roomData) => {
  const response = await apiClient.put(`/rooms/${id}`, roomData);
  return response.data;
};

// 4. ELIMINAR HABITACIÓN
export const deleteRoom = async (id) => {
  const response = await apiClient.delete(`/rooms/${id}`);
  return response.data;
};

// 5. ELIMINAR UNA IMAGEN ESPECÍFICA
export const deleteRoomImage = async (roomId, imageUrl) => {
  const response = await apiClient.delete(`/rooms/${roomId}/delete-image`, {
    params: { url: imageUrl }
  });
  return response.data;
};

// 6. AÑADIR NUEVAS IMÁGENES A HABITACIÓN EXISTENTE
export const addRoomImages = async (roomId, files) => {
  const formData = new FormData();
  
  // Verifica que FastAPI espere el parámetro 'files' aquí
  files.forEach(file => {
    formData.append('files', file); 
  });

  const response = await apiClient.post(`/rooms/${roomId}/add-images`, formData);
  return response.data;
};

export const getRoomLogs = async (page = 1, limit = 8) => {
  const response = await apiClient.get(`/rooms/logs/history?page=${page}&limit=${limit}`);
  return response.data;
};

export const searchAvailableRoom = async (tipo, entrada, salida, huespedes) => {
  const response = await apiClient.get('/busqueda/disponibilidad', {
    params: {
      tipo: tipo,
      entrada: entrada,
      salida: salida,
      huespedes: huespedes
    }
  });
  
  return response; 
};