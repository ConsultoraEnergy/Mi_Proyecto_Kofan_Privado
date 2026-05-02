import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

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
    redirect: "/hospedaje"
  },

  {
    path: "/hospedaje",
    component: PublicLayout,
    children: [
      { path: "", name: "hospedaje-home", component: HomeView }, 
      { path: "about", name: "about", component: AboutUs },
      { path: "gallery", name: "gallery", component: PhotoGallery },
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
      },
      {
        path: "register",
        name: "register",
        component: () => import("@/views/auth/Register.vue"),
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
    meta: { requiresAuth: true, isAdmin: true, hideNav: true },
    children: [
      {
        path: "",
        redirect: { name: "admin-dashboard" },
      },
      {
        path: "dashboard",
        name: "admin-dashboard",
        component: () => import("@/views/admin/DashboardView.vue"),
      },
      {
        path: "rooms",
        name: "admin-rooms",
        component: () => import("@/views/admin/RoomsManager.vue"),
      },
      {
        path: "bookings",
        name: "admin-bookings",
        component: () => import("@/views/admin/BookingsManager.vue"),
      },
      {
        path: "users",
        name: "admin-users",
        component: () => import("@/views/admin/UsersManager.vue"),
      },
      {
        path: "gallery",
        name: "admin-gallery",
        component: () => import("@/views/admin/GalleryManager.vue"),
      },
      {
        path: 'configuracion',
        name: 'admin-config',
        component: ConfiguracionAdmin,
      }
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
router.beforeEach((to, from, next) => {
  const auth = useAuthStore();

  if (to.meta.requiresAuth && !auth.isLogged) {
    return next({ name: "login" });
  }

  if (to.meta.isAdmin && !auth.isAdmin) {
    return next({ name: "hospedaje-home" }); 
  }

  if ((to.name === "login" || to.name === "register") && auth.isLogged) {
    if (auth.isAdmin) {
      return next({ name: "admin-dashboard" });
    }
    return next({ name: "account-profile" });
  }

  next();
});

export default router;