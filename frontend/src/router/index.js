import { createRouter, createWebHistory } from "vue-router";
import axios from "axios";
import Home from "../views/Home.vue";
import Trace from "../views/Trace.vue";
import AdminLogin from "../views/AdminLogin.vue";
import AdminLayout from "../views/AdminLayout.vue";
import Dashboard from "../views/Dashboard.vue";
import Products from "../views/Products.vue";
import Complaints from "../views/Complaints.vue";
import NotFound from "../views/NotFound.vue";
import UserLogin from "../views/UserLogin.vue";
import UserRegister from "../views/UserRegister.vue";
import AdminComments from "../views/AdminComments.vue";

function rfidFromQuery(raw) {
  if (raw == null) return "";
  if (Array.isArray(raw)) return String(raw[0] ?? "").trim();
  return String(raw).trim();
}

const routes = [
  { path: "/", name: "Home", component: Home },
  { path: "/login", name: "UserLogin", component: UserLogin },
  { path: "/register", name: "UserRegister", component: UserRegister },
  {
    path: "/trace",
    name: "TraceByQuery",
    component: Trace,
    props: (route) => ({ rfid: rfidFromQuery(route.query.rfid) }),
    beforeEnter(to, _from, next) {
      if (!rfidFromQuery(to.query.rfid)) {
        return next({ path: "/" });
      }
      next();
    },
  },
  { path: "/trace/:rfid", name: "Trace", component: Trace, props: true },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: "", redirect: { name: "AdminDashboard" } },
      {
        path: "dashboard",
        name: "AdminDashboard",
        component: Dashboard,
      },
      {
        path: "products",
        name: "AdminProducts",
        component: Products,
      },
      {
        path: "complaints",
        name: "AdminComplaints",
        component: Complaints,
      },
      {
        path: "comments",
        name: "AdminComments",
        component: AdminComments,
      },
    ],
  },
  { path: "/admin/login", name: "AdminLogin", component: AdminLogin },
  { path: "/:pathMatch(.*)*", name: "NotFound", component: NotFound },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach(async (to, from, next) => {
  if (to.name === "AdminLogin" || to.name === "UserLogin" || to.name === "UserRegister") {
    return next();
  }
  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth);
  if (!requiresAuth) {
    return next();
  }
  try {
    const { data } = await axios.get("/api/admin/me", { withCredentials: true });
    if (data.admin) {
      return next();
    }
  } catch {
    /* 未登录 */
  }
  next({ name: "AdminLogin", query: { redirect: to.fullPath } });
});

export default router;
