<template>
  <div>
    <FtToastHost />
    <template v-if="!isAdminShell">
      <nav class="navbar navbar-expand-lg navbar-light border-bottom ft-nav mb-3">
        <div class="container">
          <div class="d-flex align-items-center justify-content-between w-100 gap-2">
            <router-link
              class="navbar-brand d-flex align-items-center gap-2 fw-semibold text-danger mb-0"
              to="/"
            >
              <img src="/logo.svg" alt="" width="36" height="36" class="ft-brand-logo" />
              <span>果蔬溯源</span>
            </router-link>
            <div class="d-flex align-items-center gap-2 flex-shrink-0 flex-wrap justify-content-end">
              <template v-if="admin">
                <span class="small text-muted d-none d-sm-inline">管理员</span>
                <button
                  class="btn btn-sm btn-outline-secondary ft-btn-press"
                  type="button"
                  @click="logout"
                >
                  退出
                </button>
              </template>
              <template v-else>
                <template v-if="currentUser">
                  <span class="small text-muted d-none d-sm-inline">{{ currentUser.username }}</span>
                  <button
                    class="btn btn-sm btn-outline-secondary ft-btn-press"
                    type="button"
                    @click="logoutEndUser"
                  >
                    退出
                  </button>
                </template>
                <template v-else>
                  <router-link class="btn btn-sm btn-outline-danger ft-btn-press" to="/login">
                    登录
                  </router-link>
                  <router-link class="btn btn-sm btn-outline-secondary ft-btn-press" to="/register">
                    注册
                  </router-link>
                </template>
              </template>
            </div>
          </div>
          <button
            v-if="admin"
            class="navbar-toggler w-100 mt-2"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navMain"
          >
            <span class="navbar-toggler-icon"></span>
            <span class="small ms-1">菜单</span>
          </button>
          <div
            v-if="admin"
            id="navMain"
            class="collapse navbar-collapse mt-2"
          >
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
              <li class="nav-item">
                <router-link class="nav-link" to="/admin/dashboard">管理后台</router-link>
              </li>
            </ul>
          </div>
        </div>
      </nav>
      <main class="container pb-5">
        <router-view />
      </main>
      <footer class="text-center text-muted small py-4 border-top ft-footer">
        <div class="container">
          <div class="mb-1">果蔬食品全流程溯源模式设计</div>
          <router-link
            to="/admin/login"
            class="ft-footer-admin-link text-decoration-none"
          >
            管理登录
          </router-link>
        </div>
      </footer>
    </template>
    <router-view v-else />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import FtToastHost from "./components/FtToastHost.vue";
import { http, adminLogout } from "./api.js";
import { currentUser as currentUserRef, logoutUser, refreshUserAuth } from "./auth/user.js";

const route = useRoute();
const router = useRouter();
const admin = ref(false);

/** 本地 computed，避免外部 import 的 ref 在个别环境下模板未正确绑定 */
const currentUser = computed(() => currentUserRef.value);

const isAdminShell = computed(
  () => route.path.startsWith("/admin") && route.path !== "/admin/login"
);

async function refreshAdmin() {
  try {
    const { data } = await http.get("/api/admin/me", { silent: true });
    admin.value = !!data?.admin;
  } catch {
    admin.value = false;
  }
}

async function refreshSession() {
  await Promise.all([refreshAdmin(), refreshUserAuth()]);
}

async function logoutEndUser() {
  await logoutUser();
}

async function logout() {
  try {
    await adminLogout();
  } finally {
    admin.value = false;
    await router.replace({ name: "AdminLogin" });
  }
}

onMounted(refreshSession);
watch(() => route.fullPath, refreshSession);
</script>

<style scoped>
.ft-nav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(6px);
}
.ft-footer {
  background: rgba(255, 255, 255, 0.6);
}
.ft-brand-logo {
  display: block;
}
/* 页脚管理入口：更小、更淡，不抢主内容 */
.ft-footer-admin-link {
  font-size: 0.75rem;
  color: #adb5bd;
}
.ft-footer-admin-link:hover {
  color: #6c757d;
  text-decoration: underline !important;
}
</style>
