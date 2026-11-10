import { onScopeDispose, watch } from "vue";

/** Igual que `watch`, pero espera `delay` ms sin cambios antes de llamar a `callback` (buscadores). */
export function useDebouncedWatch(source, callback, delay = 350) {
  let timer = null;
  const stop = watch(source, (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => callback(...args), delay);
  });
  onScopeDispose(() => clearTimeout(timer));
  return stop;
}
