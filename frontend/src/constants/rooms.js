/** Estados operativos de una habitación (backend: rooms.operational_status). */
export const OPERATIONAL_STATUS = Object.freeze({
  available: { label: "Disponible", icon: "fa-solid fa-leaf", badge: "badge-soft-success" },
  cleaning: { label: "En limpieza", icon: "fa-solid fa-broom", badge: "badge-soft-maintenance" },
  maintenance: { label: "En mantenimiento", icon: "fa-solid fa-user-gear", badge: "badge-soft-warning" },
  out_of_service: { label: "Fuera de servicio", icon: "fa-solid fa-ban", badge: "badge-soft-danger" },
});

export const operationalStatusMeta = (status) => OPERATIONAL_STATUS[status] || OPERATIONAL_STATUS.available;

/** Filtros rápidos del inventario (se aplican sobre la página cargada). */
export const ROOM_FILTERS = Object.freeze([
  { key: "all", label: "Todas", icon: "fa-solid fa-bed", test: () => true },
  { key: "active", label: "Habilitadas", icon: "fa-solid fa-leaf", test: (room) => room.is_active },
  { key: "inactive", label: "No habilitadas", icon: "fa-solid fa-ban", test: (room) => !room.is_active },
  {
    key: "attention",
    label: "Limpieza / mantenimiento",
    icon: "fa-solid fa-broom",
    test: (room) => room.operational_status !== "available",
  },
]);

export const MAX_ROOM_PHOTOS = 5;

export const BASE_AMENITIES = Object.freeze([
  "Aire Acondicionado",
  "Ventilador",
  "Televisión",
  "Wifi",
  "Baño Privado",
  "Nevera / Minibar",
  "Zonas Verdes",
  "Vista a la Selva",
  "Malla Catamarán",
  "Tina / Jacuzzi",
  "Balcón",
]);

/** Miniatura gris "Sin foto" para habitaciones sin imagen o con imagen rota. */
export const NO_PHOTO_PLACEHOLDER =
  "data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%2260%22%20height%3D%2250%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2060%2050%22%20preserveAspectRatio%3D%22none%22%3E%3Crect%20width%3D%2260%22%20height%3D%2250%22%20fill%3D%22%23eeeeee%22%2F%3E%3Ctext%20text-anchor%3D%22middle%22%20x%3D%2230%22%20y%3D%2230%22%20style%3D%22fill%3A%23aaaaaa%3Bfont-weight%3Abold%3Bfont-size%3A10px%3Bfont-family%3AArial%2CHelvetica%2Csans-serif%22%3ESin%20Foto%3C%2Ftext%3E%3C%2Fsvg%3E";
