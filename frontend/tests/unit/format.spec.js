import { describe, expect, it } from "vitest";
import { assetUrl } from "@/config/env";
import { formatDate, formatDateTime, formatMoney, fromIsoDate, nightsBetween, toIsoDate } from "@/utils/format";
import { canTransition, requiresReason, statusLabel } from "@/constants/booking";

describe("utils/format", () => {
  it("formatea pesos colombianos sin decimales", () => {
    expect(formatMoney(1250000).replace(/\s/g, " ")).toMatch(/\$\s?1\.250\.000/);
  });

  it("las fechas de calendario no se corren de día por la zona horaria", () => {
    expect(formatDate("2026-12-01")).toMatch(/01/);
    expect(toIsoDate(fromIsoDate("2026-12-31"))).toBe("2026-12-31");
  });

  it("muestra los instantes en la hora de Colombia (UTC-5)", () => {
    // 03:30 UTC del 10 de nov = 22:30 del 9 de nov en Bogotá
    expect(formatDateTime("2026-11-10T03:30:00Z")).toMatch(/^9\/11\/2026.*10:30/);
  });

  it("cuenta noches con intervalo semiabierto", () => {
    expect(nightsBetween("2026-11-10", "2026-11-13")).toBe(3);
    expect(nightsBetween("2026-11-13", "2026-11-10")).toBe(0);
  });
});

describe("config/env", () => {
  it("assetUrl respeta URLs absolutas y antepone el origen a rutas relativas", () => {
    expect(assetUrl("https://cdn.example.com/a.webp")).toBe("https://cdn.example.com/a.webp");
    expect(assetUrl("/static/uploads/a.webp")).toBe("/static/uploads/a.webp");
    expect(assetUrl("")).toBe("");
  });
});

describe("constants/booking", () => {
  it("refleja la máquina de estados del backend", () => {
    expect(canTransition("pending_verification", "confirmed")).toBe(true);
    expect(canTransition("cancelled", "confirmed")).toBe(false);
    expect(canTransition("confirmed", "checked_out")).toBe(false);
    expect(requiresReason("pending_verification", "pending_payment")).toBe(true);
    expect(requiresReason("confirmed", "cancelled")).toBe(true);
    expect(requiresReason("confirmed", "checked_in")).toBe(false);
    expect(statusLabel("pending_verification")).toBe("Pago por verificar");
  });
});
