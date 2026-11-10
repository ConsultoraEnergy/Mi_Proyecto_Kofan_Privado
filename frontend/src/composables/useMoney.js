import { useConfigStore } from "@/stores/config";
import { formatMoney } from "@/utils/format";

/** Formateador de dinero en la moneda configurada para el hotel. */
export function useMoney() {
  const configStore = useConfigStore();
  return (value) => formatMoney(value, configStore.data.currency);
}
