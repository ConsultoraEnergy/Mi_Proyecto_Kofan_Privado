import { computed, ref } from "vue";

/**
 * Paginación por página/límite (la que usa la API: ?page=&limit= -> { items, total }).
 * `onChange` se llama cuando el usuario cambia de página con `goTo`.
 */
export function usePagination(limit, onChange = () => {}) {
  const page = ref(1);
  const total = ref(0);
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)));

  function goTo(target) {
    if (target < 1 || target > totalPages.value || target === page.value) return;
    page.value = target;
    onChange(target);
  }

  const reset = () => {
    page.value = 1;
  };

  return { page, total, limit, totalPages, goTo, reset };
}
