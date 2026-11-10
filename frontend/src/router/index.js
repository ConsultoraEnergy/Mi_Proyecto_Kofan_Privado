import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { PERMISSIONS } from "@/constants/booking";

const PublicLayout = () => import("@/layouts/PublicLayout.vue");
const HomeView = () => import("@/views/public/Home.vue");
const AboutUs = () => import("@/views/public/AboutUs.vue");
const PhotoGallery = () => import("@/views/public/PhotosGallery.vue");
const ConfiguracionAdmin = () => import("@/views/admin/config.vue");

const AppLayout = () => import("@/layouts/AppLayout.vue");
const AdminLayout = () => import("@/layouts/AdminLayout.vue");
const AuthLayout = () => import("@/layouts/AuthLayout.vue");

const routes = [
  // ZONA PÚBLICA
  {
    path: "/",
    redirect: "/hospedaje",
  },

  {
    path: "/hospedaje",
    component: PublicLayout,
    children: [
      { path: "", name: "hospedaje-home", component: HomeView },
      { path: "about", name: "about", component: AboutUs },
      { path: "gallery", name: "gallery", component: PhotoGallery },
      {
        path: "politica-de-datos",
        name: "privacy-policy",
        component: () => import("@/views/public/PrivacyPolicy.vue"),
      },
    ],
  },

  // ZONA AUTH
  {
    path: "/auth",
    component: AuthLayout,
    children: [
      {
        path: "login",
        name: "login",
        component: () => import("@/views/auth/Login.vue"),
        meta: { guestOnly: true },
      },
      {
        path: "register",
        name: "register",
        component: () => import("@/views/auth/Register.vue"),
        meta: { guestOnly: true },
      },
      {
        path: "verify-email",
        name: "verify-email",
        component: () => import("@/views/auth/VerifyEmail.vue"),
      },
      {
        path: "forgot-password",
        name: "forgot-password",
        component: () => import("@/views/auth/ForgotPassword.vue"),
        meta: { guestOnly: true },
      },
      {
        path: "reset-password",
        name: "reset-password",
        component: () => import("@/views/auth/ResetPassword.vue"),
      },
    ],
  },

  // ZONA APP (CLIENTE)
  {
    path: "/app",
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        redirect: { name: "account-profile" },
      },
      {
        path: "profile",
        name: "account-profile",
        component: () => import("@/views/app/ProfileView.vue"),
      },
      {
        path: "settings",
        name: "account-settings",
        component: () => import("@/views/app/SettingsView.vue"),
      },
      {
        path: "bookings",
        name: "account-bookings",
        component: () => import("@/views/app/BookingsView.vue"),
      },
      {
        path: "notifications",
        name: "account-notifications",
        component: () => import("@/views/app/NotificationsView.vue"),
      },
    ],
  },

  // ZONA ADMIN
  {
    path: "/admin",
    component: AdminLayout,
    // Zona del personal (admin y recepción). Cada vista exige además su permiso.
    meta: { requiresAuth: true, requiresStaff: true, hideNav: true },
    children: [
      {
        path: "",
        redirect: { name: "admin-dashboard" },
      },
      {
        path: "dashboard",
        name: "admin-dashboard",
        meta: { permission: PERMISSIONS.DASHBOARD_READ },
        component: () => import("@/views/admin/DashboardView.vue"),
      },
      {
        path: "rooms",
        name: "admin-rooms",
        meta: { permission: PERMISSIONS.ROOMS_READ_ALL },
        component: () => import("@/views/admin/RoomsManager.vue"),
      },
      {
        path: "bookings",
        name: "admin-bookings",
        meta: { permission: PERMISSIONS.BOOKINGS_READ_ALL },
        component: () => import("@/views/admin/BookingsManager.vue"),
      },
      {
        path: "users",
        name: "admin-users",
        meta: { permission: PERMISSIONS.USERS_READ },
        component: () => import("@/views/admin/UsersManager.vue"),
      },
      {
        path: "gallery",
        name: "admin-gallery",
        meta: { permission: PERMISSIONS.GALLERY_WRITE },
        component: () => import("@/views/admin/GalleryManager.vue"),
      },
      {
        path: "configuracion",
        name: "admin-config",
        component: ConfiguracionAdmin,
        meta: { permission: PERMISSIONS.SETTINGS_WRITE },
      },
    ],
  },

  // 404
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    meta: { hideNav: true },
    component: () => import("@/views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0, behavior: "smooth" };
  },
});

// GUARDIA DE NAVEGACIÓN
// La sesión se restaura (cookie HttpOnly -> /auth/refresh) antes de la primera navegación.
// Estas guardias solo mejoran la experiencia: la autorización real la aplica el backend.
router.beforeEach(async (to) => {
  const auth = useAuthStore();
  await auth.init();

  if (to.meta.requiresAuth && !auth.isLogged) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.meta.requiresStaff && !auth.isStaff) {
    return { name: "hospedaje-home" };
  }
  if (to.meta.permission && !auth.can(to.meta.permission)) {
    return to.name === "admin-dashboard" ? { name: "hospedaje-home" } : { name: "admin-dashboard" };
  }
  if (to.meta.guestOnly && auth.isLogged) {
    return auth.homeRoute();
  }
  return true;
});

export default router;
