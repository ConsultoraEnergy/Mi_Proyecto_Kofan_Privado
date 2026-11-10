import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import BookingRowActions from "@/components/admin/bookings/BookingRowActions.vue";
import FilterChips from "@/components/common/FilterChips.vue";
import PaginationBar from "@/components/common/PaginationBar.vue";

const ALL = { changeStatus: true, edit: true, viewReceipts: true, viewFolio: true };
const NONE = { changeStatus: false, edit: false, viewReceipts: false, viewFolio: false };

const titles = (wrapper) => wrapper.findAll("button").map((b) => b.attributes("title"));

describe("BookingRowActions", () => {
  const pending = { id: "b1", status: "pending_verification", has_receipt: true, receipt_url: "/r/1" };

  it("muestra solo las transiciones válidas para el estado", () => {
    const wrapper = mount(BookingRowActions, { props: { booking: pending, can: ALL } });
    expect(titles(wrapper)).toEqual([
      "Ver comprobante de pago",
      "Aprobar pago",
      "Rechazar comprobante",
      "Editar datos de la reserva",
      "Cancelar reserva",
    ]);
  });

  it("en el hotel: check-out y folio, sin cancelar", () => {
    const wrapper = mount(BookingRowActions, {
      props: { booking: { id: "b2", status: "checked_in" }, can: ALL },
    });
    expect(titles(wrapper)).toEqual([
      "Editar datos de la reserva",
      "Hacer check-out",
      "Ver folio / cuenta del huésped",
    ]);
  });

  it("sin permisos no muestra ninguna acción", () => {
    const wrapper = mount(BookingRowActions, { props: { booking: pending, can: NONE } });
    expect(wrapper.findAll("button")).toHaveLength(0);
  });

  it("emite la reserva y el estado destino", async () => {
    const wrapper = mount(BookingRowActions, { props: { booking: pending, can: ALL } });
    await wrapper.find('[title="Rechazar comprobante"]').trigger("click");
    expect(wrapper.emitted("transition")[0]).toEqual([pending, "pending_payment"]);
  });
});

describe("FilterChips", () => {
  const options = [
    { key: "a", label: "Alertas", count: 0, badgeClass: "bg-info" },
    { key: "b", label: "Todas", count: 0 },
  ];

  it("oculta alertas en cero pero siempre muestra totales, y actualiza el v-model", async () => {
    const wrapper = mount(FilterChips, {
      props: { options, modelValue: "a", "onUpdate:modelValue": (v) => wrapper.setProps({ modelValue: v }) },
    });
    expect(wrapper.find(".badge").exists()).toBe(false);
    expect(wrapper.find(".chip-count").text()).toBe("0");

    await wrapper.findAll("button")[1].trigger("click");
    expect(wrapper.props("modelValue")).toBe("b");
    expect(wrapper.findAll("button")[1].classes()).toContain("active");
  });
});

describe("PaginationBar", () => {
  it("se oculta con una sola página y desactiva los extremos", async () => {
    const single = mount(PaginationBar, { props: { page: 1, totalPages: 1 } });
    expect(single.find("button").exists()).toBe(false);

    const wrapper = mount(PaginationBar, {
      props: { page: 1, totalPages: 3, total: 25, itemLabel: "reservas" },
    });
    const [prev, next] = wrapper.findAll("button");
    expect(prev.attributes("disabled")).toBeDefined();
    expect(wrapper.text()).toContain("25 reservas");
    await next.trigger("click");
    expect(wrapper.emitted("change")[0]).toEqual([2]);
  });
});
