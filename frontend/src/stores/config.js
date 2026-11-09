/**
 * Ajustes públicos del sitio (nombre del hotel, logo, contacto, instrucciones de pago, textos).
 * Toda la marca sale de aquí: ningún componente debe escribir el nombre del hotel en el código.
 */
import { defineStore } from "pinia";
import { getSiteSettings } from "@/api/content";
import { assetUrl } from "@/config/env";

const DEFAULTS = {
  hotel_name: "Hotel Kawari",
  tagline: "",
  logo_url: "",
  contact_email: "",
  phone: "",
  whatsapp_number: "",
  address: "",
  city: "",
  country: "Colombia",
  check_in_time: "15:00",
  check_out_time: "11:00",
  currency: "COP",
  tax_percentage: 0,
  social_facebook: "",
  social_instagram: "",
  social_tiktok: "",
  payment_instructions: "",
  about_description: "",
  mission: "",
  vision: "",
  deposit_percent: 50,
};

export const useConfigStore = defineStore("config", {
  state: () => ({
    data: { ...DEFAULTS },
    isLoaded: false,
  }),

  getters: {
    hotelName: (state) => state.data.hotel_name || DEFAULTS.hotel_name,
    logoUrl: (state) => assetUrl(state.data.logo_url),
    whatsappLink: (state) => {
      const digits = (state.data.whatsapp_number || "").replace(/\D/g, "");
      return digits ? `https://wa.me/${digits}` : "";
    },
  },

  actions: {
    async fetchSiteConfig(force = false) {
      if (this.isLoaded && !force) return;
      try {
        this.data = { ...DEFAULTS, ...(await getSiteSettings()) };
        this.isLoaded = true;
        document.title = this.data.hotel_name;
      } catch (error) {
        console.error("No se pudo cargar la configuración del sitio:", error);
      }
    },

    setData(data) {
      this.data = { ...DEFAULTS, ...data };
      this.isLoaded = true;
    },
  },
});
