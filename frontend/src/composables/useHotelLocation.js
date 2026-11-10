/** Dirección del hotel (ajustes del sitio) y su mapa embebido. */
import { computed } from "vue";
import { useConfigStore } from "@/stores/config";

export const mapEmbedUrl = (query) =>
  `https://www.google.com/maps?q=${encodeURIComponent(query)}&output=embed`;

export function useHotelLocation() {
  const configStore = useConfigStore();

  const hasLocation = computed(() => !!(configStore.data.address || configStore.data.city));
  const locationText = computed(() =>
    [configStore.data.address, configStore.data.city, configStore.data.country].filter(Boolean).join(", "),
  );
  const mapUrl = computed(() => mapEmbedUrl(locationText.value));

  return { hasLocation, locationText, mapUrl };
}
