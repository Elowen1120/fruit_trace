<template>
  <div class="row justify-content-center">
    <div class="col-md-5">
      <div class="ft-card p-4">
        <h1 class="h4 mb-4">管理员登录</h1>
        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">账号</label>
            <input v-model="username" class="form-control" autocomplete="username" />
          </div>
          <div class="mb-3">
            <label class="form-label">密码</label>
            <input
              v-model="password"
              type="password"
              class="form-control"
              autocomplete="current-password"
            />
          </div>
          <p v-if="err" class="text-danger small">{{ err }}</p>
          <button class="btn btn-ft-primary w-100" type="submit" :disabled="loading">
            登录
          </button>
        </form>
        <p class="small text-muted mt-3 mb-0">默认账号 admin / 123456</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { adminLogin } from "../api.js";

const router = useRouter();
const route = useRoute();
const username = ref("admin");
const password = ref("");
const err = ref("");
const loading = ref(false);

async function submit() {
  err.value = "";
  loading.value = true;
  try {
    const data = await adminLogin(username.value, password.value);
    if (!data?.ok) {
      err.value = data?.error || "登录失败";
      return;
    }
    const redir = route.query.redirect;
    if (typeof redir === "string" && redir.startsWith("/admin")) {
      await router.replace(redir);
    } else {
      await router.replace({ name: "AdminDashboard" });
    }
  } catch (e) {
    const st = e.response?.status;
    if (st >= 500) {
      err.value = "服务暂时不可用，请稍后重试";
    } else if (st === 401) {
      err.value = e.response?.data?.error || "账号或密码错误";
    } else {
      err.value = e.response?.data?.error || "登录失败";
    }
  } finally {
    loading.value = false;
  }
}
</script>
