import { beforeEach, describe, expect, it, vi } from "vitest";
import { effectScope, nextTick } from "vue";
import { createPinia, setActivePinia } from "pinia";

vi.mock("sweetalert2", () => ({ default: { fire: vi.fn() } }));
vi.mock("@/api/bookings", () => ({
  listBookings: vi.fn(),
  changeBookingStatus: vi.fn(),
  openReceipt: vi.fn(),
}));
vi.mock("@/api/operations", () => ({ getDashboard: vi.fn() }));
vi.mock("@/api/rooms", () => ({
  listRooms: vi.fn(),
  listRoomTypes: vi.fn(),
  createRoom: vi.fn(),
  updateRoom: vi.fn(),
  deleteRoom: vi.fn(),
  addRoomImages: vi.fn(),
  removeRoomImage: vi.fn(),
}));

import Swal from "sweetalert2";
import * as bookingsApi from "@/api/bookings";
import * as roomsApi from "@/api/rooms";
import { usePagination } from "@/composables/usePagination";
import { groupRoomsByType } from "@/composables/useRoomCatalog";
import { mapEmbedUrl } from "@/composables/useHotelLocation";
import { diffRoomForm, normalizeRoomForm, roomToForm, useRoomForm } from "@/composables/useRoomForm";
import { BOOKINGS_PAGE_SIZE, useBookingsBoard } from "@/composables/useBookingsBoard";
import { useBookingActions } from "@/composables/useBookingActions";

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));
// Los composables con watchers se crean dentro de un scope, como lo haría un componente.
const inScope = (factory) => effectScope().run(factory);

const room = {
  id: "r1",
  number: "101",
  name: "Cabaña del río",
  room_type: { id: "t1", code: "cabana", name: "Cabaña" },
  description: "",
  price_per_night: 200000,
  capacity: 2,
  bedrooms: 1,
  beds: "1 doble",
  amenities: ["Wifi"],
  is_active: true,
  operational_status: "available",
  images: ["/static/a.webp", "/static/b.webp"],
  main_image: "/static/a.webp",
};

describe("usePagination", () => {
  it("calcula páginas y solo navega dentro del rango", () => {
    const onChange = vi.fn();
    const p = usePagination(10, onChange);
    expect(p.totalPages.value).toBe(1); // nunca 0, aunque no haya registros
    p.total.value = 25;
    expect(p.totalPages.value).toBe(3);

    p.goTo(0);
    p.goTo(4);
    p.goTo(1); // ya está en la 1
    expect(onChange).not.toHaveBeenCalled();

    p.goTo(3);
    expect(p.page.value).toBe(3);
    expect(onChange).toHaveBeenCalledWith(3);
    p.reset();
    expect(p.page.value).toBe(1);
  });
});

describe("groupRoomsByType", () => {
  it("respeta el orden del catálogo, agrega tipos desconocidos y deja 'Otros' al final", () => {
    const types = [
      { code: "familiar", name: "Familiar" },
      { code: "cabana", name: "Cabaña" },
      { code: "suite", name: "Suite" }, // sin habitaciones: no aparece
    ];
    const rooms = [
      { id: 1, room_type: { code: "cabana", name: "Cabaña" } },
      { id: 2, room_type: null },
      { id: 3, room_type: { code: "glamping", name: "Glamping" } },
      { id: 4, room_type: { code: "familiar", name: "Familiar" } },
    ];
    const sections = groupRoomsByType(rooms, types);
    expect(sections.map((s) => s.code)).toEqual(["familiar", "cabana", "glamping", "otros"]);
    expect(sections.find((s) => s.code === "otros").rooms.map((r) => r.id)).toEqual([2]);
  });
});

describe("mapEmbedUrl", () => {
  it("codifica la dirección", () => {
    expect(mapEmbedUrl("Calle 1 # 2-3, Mocoa")).toBe(
      "https://www.google.com/maps?q=Calle%201%20%23%202-3%2C%20Mocoa&output=embed",
    );
  });
});

describe("formulario de habitación", () => {
  beforeEach(() => vi.clearAllMocks());

  it("normaliza tipos y recorta textos", () => {
    const body = normalizeRoomForm({
      ...roomToForm(room),
      number: " 101 ",
      price_per_night: "150000",
      capacity: "3",
    });
    expect(body.number).toBe("101");
    expect(body.price_per_night).toBe(150000);
    expect(body.capacity).toBe(3);
  });

  it("roomToForm copia las listas (no muta la fila de la tabla)", () => {
    const form = roomToForm(room);
    form.amenities.push("Balcón");
    form.images.pop();
    expect(room.amenities).toEqual(["Wifi"]);
    expect(room.images).toHaveLength(2);
  });

  it("el diff solo incluye los campos que cambiaron", () => {
    const original = roomToForm(room);
    const current = {
      ...roomToForm(room),
      name: "Cabaña grande",
      amenities: ["Wifi", "Balcón"],
      capacity: "2",
    };
    expect(diffRoomForm(current, original)).toEqual({ name: "Cabaña grande", amenities: ["Wifi", "Balcón"] });
  });

  it("al editar envía un PATCH solo con los cambios", async () => {
    roomsApi.updateRoom.mockResolvedValue({});
    const f = useRoomForm();
    f.startEdit(room);
    expect(f.isEditing.value).toBe(true);
    f.form.value.price_per_night = "250000";
    f.setMainImage("/static/b.webp");

    expect(await f.save()).toBe(true);
    expect(roomsApi.updateRoom).toHaveBeenCalledWith("r1", {
      price_per_night: 250000,
      main_image: "/static/b.webp",
    });
    expect(roomsApi.addRoomImages).not.toHaveBeenCalled();
    expect(f.isEditing.value).toBe(false); // el formulario queda limpio
  });

  it("no crea una habitación sin fotos", async () => {
    const f = useRoomForm();
    Object.assign(f.form.value, { number: "1", name: "Nueva", price_per_night: 1, room_type_id: "t1" });
    expect(await f.save()).toBe(false);
    expect(roomsApi.createRoom).not.toHaveBeenCalled();
    expect(Swal.fire).toHaveBeenCalled();
  });

  it("al crear no envía main_image y sube las fotos a la habitación creada", async () => {
    roomsApi.createRoom.mockResolvedValue({ id: "nueva" });
    roomsApi.addRoomImages.mockResolvedValue({});
    const f = useRoomForm();
    Object.assign(f.form.value, { number: "1", name: "Nueva", price_per_night: 1, room_type_id: "t1" });
    const file = new File(["x"], "a.png", { type: "image/png" });
    f.pendingFiles.value = [file];

    expect(await f.save()).toBe(true);
    expect(roomsApi.createRoom.mock.calls[0][0]).not.toHaveProperty("main_image");
    expect(roomsApi.addRoomImages).toHaveBeenCalledWith("nueva", [file]);
  });

  it("una foto borrada en el servidor no cuenta como cambio pendiente", async () => {
    Swal.fire.mockResolvedValueOnce({ isConfirmed: true });
    roomsApi.removeRoomImage.mockResolvedValue({ images: ["/static/b.webp"], main_image: "/static/b.webp" });
    const f = useRoomForm();
    f.startEdit(room);

    expect(await f.removeImage("/static/a.webp")).toBe(true);
    expect(f.form.value.images).toEqual(["/static/b.webp"]);
    await f.save();
    expect(roomsApi.updateRoom).not.toHaveBeenCalled();
  });
});

describe("useBookingsBoard", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("filtra por los estados de la pestaña y vuelve a la página 1 al cambiarla", async () => {
    bookingsApi.listBookings.mockResolvedValue({
      items: [],
      total: 35,
      summary: { pending_verification: 2 },
    });
    const board = inScope(() => useBookingsBoard({ initialTab: "no-existe" }));
    expect(board.activeTab.value).toBe("pending_verification");

    await board.load();
    expect(bookingsApi.listBookings).toHaveBeenLastCalledWith({
      status: "pending_verification",
      page: 1,
      limit: BOOKINGS_PAGE_SIZE,
    });
    expect(board.totalPages.value).toBe(4);
    expect(board.summary.value.pending_verification).toBe(2);

    board.goToPage(3);
    await flush();
    expect(bookingsApi.listBookings).toHaveBeenLastCalledWith(expect.objectContaining({ page: 3 }));

    board.activeTab.value = "history";
    await nextTick();
    await flush();
    expect(board.page.value).toBe(1);
    expect(bookingsApi.listBookings).toHaveBeenLastCalledWith(
      expect.objectContaining({ status: "checked_out,cancelled", page: 1 }),
    );
  });

  it("ignora la respuesta de una petición anterior que llega tarde", async () => {
    let resolveSlow;
    bookingsApi.listBookings
      .mockImplementationOnce(() => new Promise((resolve) => (resolveSlow = resolve)))
      .mockResolvedValueOnce({ items: [{ id: "nueva" }], total: 1 });

    const board = inScope(() => useBookingsBoard());
    const slow = board.load();
    await board.load();
    resolveSlow({ items: [{ id: "vieja" }], total: 1 });
    await slow;

    expect(board.bookings.value.map((b) => b.id)).toEqual(["nueva"]);
    expect(board.loading.value).toBe(false);
  });

  it("espera a que el usuario deje de escribir para buscar", async () => {
    vi.useFakeTimers();
    try {
      bookingsApi.listBookings.mockResolvedValue({ items: [], total: 0 });
      const board = inScope(() => useBookingsBoard());
      board.search.value = "ana";
      await nextTick();
      board.search.value = "ana@correo.co ";
      await nextTick();
      expect(bookingsApi.listBookings).not.toHaveBeenCalled();

      await vi.advanceTimersByTimeAsync(400);
      expect(bookingsApi.listBookings).toHaveBeenCalledTimes(1);
      expect(bookingsApi.listBookings).toHaveBeenCalledWith(expect.objectContaining({ q: "ana@correo.co" }));
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("useBookingActions", () => {
  beforeEach(() => vi.clearAllMocks());

  const booking = { id: "b1", code: "KW-1", status: "pending_verification", guest: { full_name: "Ana" } };

  it("rechazar un comprobante exige motivo y lo envía recortado", async () => {
    Swal.fire.mockResolvedValueOnce({ isConfirmed: true, value: "  monto incorrecto " });
    bookingsApi.changeBookingStatus.mockResolvedValue({});
    const onChanged = vi.fn();
    const { changeStatus } = useBookingActions({ onChanged });

    expect(await changeStatus(booking, "pending_payment")).toBe(true);
    expect(Swal.fire.mock.calls[0][0].input).toBe("textarea");
    expect(bookingsApi.changeBookingStatus).toHaveBeenCalledWith("b1", "pending_payment", "monto incorrecto");
    expect(onChanged).toHaveBeenCalled();
  });

  it("aprobar no pide motivo y no hace nada si el usuario se arrepiente", async () => {
    Swal.fire.mockResolvedValueOnce({ isConfirmed: false });
    const { changeStatus } = useBookingActions();

    expect(await changeStatus(booking, "confirmed")).toBe(false);
    expect(Swal.fire.mock.calls[0][0].input).toBeUndefined();
    expect(bookingsApi.changeBookingStatus).not.toHaveBeenCalled();
  });
});
