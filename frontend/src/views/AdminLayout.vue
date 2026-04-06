<template>
  <div class="admin-shell d-flex flex-column flex-md-row min-vh-100">
    <!-- Desktop / tablet sidebar -->
    <aside
      class="admin-sidebar border-end d-none d-md-flex flex-column bg-white"
      :class="{ 'sidebar-collapsed': sidebarCollapsed && isTablet }"
    >
      <div class="p-3 border-bottom d-flex align-items-center justify-content-between">
        <router-link class="fw-semibold text-danger text-decoration-none" to="/admin/dashboard">
          管理后台
        </router-link>
        <button
          v-if="isTablet"
          type="button"
          class="btn btn-sm btn-outline-secondary"
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          {{ sidebarCollapsed ? "展开" : "收起" }}
        </button>
      </div>
      <nav class="flex-grow-1 p-2 nav flex-column gap-1">
        <router-link
          v-for="l in navLinks"
          :key="l.to"
          class="nav-link rounded-pill px-3 py-2 admin-nav-link"
          active-class="active"
          :to="l.to"
        >
          <span class="me-2">{{ l.icon }}</span>
          <span v-show="!sidebarCollapsed || !isTablet">{{ l.label }}</span>
        </router-link>
      </nav>
      <div class="p-3 border-top small text-muted">
        <button type="button" class="btn btn-sm btn-outline-secondary w-100" @click="doLogout">
          退出登录
        </button>
      </div>
    </aside>

    <!-- Mobile bottom nav -->
    <nav class="admin-bottom-nav d-md-none fixed-bottom border-top bg-white py-2 px-1">
      <div class="d-flex justify-content-around">
        <router-link
          v-for="l in navLinks"
          :key="'m-' + l.to"
          class="text-center text-decoration-none flex-fill py-1 admin-bottom-link"
          :class="{ active: route.path === l.to }"
          :to="l.to"
        >
          <div class="small">{{ l.icon }}</div>
          <div class="tiny">{{ l.label }}</div>
        </router-link>
      </div>
    </nav>

    <div class="admin-main flex-grow-1 d-flex flex-column pb-5 pb-md-0">
      <header
        class="border-bottom bg-white px-3 py-2 d-md-none d-flex align-items-center justify-content-between gap-2"
      >
        <span class="fw-semibold text-danger">果蔬溯源 · 管理</span>
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary flex-shrink-0"
          @click="doLogout"
        >
          退出登录
        </button>
      </header>
      <div class="position-relative flex-grow-1 p-3 p-md-4">
        <router-view v-slot="{ Component }">
          <transition name="fade-page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { adminLogout } from "../api.js";

const route = useRoute();
const router = useRouter();
const sidebarCollapsed = ref(false);
const winW = ref(typeof window !== "undefined" ? window.innerWidth : 1200);

const isTablet = computed(() => winW.value >= 768 && winW.value <= 1200);

const navLinks = [
  { to: "/admin/dashboard", label: "仪表盘", icon: "📊" },
  { to: "/admin/products", label: "产品管理", icon: "📦" },
  { to: "/admin/comments", label: "评价管理", icon: "💬" },
  { to: "/admin/complaints", label: "投诉管理", icon: "📋" },
];

function onResize() {
  winW.value = window.innerWidth;
  if (!isTablet.value) sidebarCollapsed.value = false;
}

onMounted(() => {
  window.addEventListener("resize", onResize);
});
onUnmounted(() => window.removeEventListener("resize", onResize));

async function doLogout() {
  try {
    await adminLogout();
  } finally {
    await router.replace({ name: "AdminLogin" });
  }
}
</script>

<style scoped>
.admin-sidebar {
  width: 250px;
  min-height: 100vh;
  position: sticky;
  top: 0;
  align-self: flex-start;
  transition: width 0.25s ease;
}
.sidebar-collapsed {
  width: 72px;
}
.sidebar-collapsed .admin-nav-link span:not(.me-2) {
  display: none;
}
.admin-nav-link {
  color: #5c3d40;
}
.admin-nav-link.active {
  background: linear-gradient(90deg, #ffe4ea 0%, #fff5f7 100%);
  color: #c44c4c !important;
  font-weight: 600;
}
.admin-main {
  min-width: 0;
  background: linear-gradient(180deg, #fff8fa 0%, #ffeef2 100%);
}
.admin-bottom-link {
  color: #6c757d;
  font-size: 0.7rem;
}
.admin-bottom-link.active {
  color: #c44c4c;
  font-weight: 600;
}
.tiny {
  font-size: 0.65rem;
}
.fade-page-enter-active,
.fade-page-leave-active {
  transition: opacity 0.3s ease;
}
.fade-page-enter-from,
.fade-page-leave-to {
  opacity: 0;
}
@media (max-width: 767.98px) {
  .admin-main {
    padding-bottom: 4.5rem !important;
  }
}
</style>
