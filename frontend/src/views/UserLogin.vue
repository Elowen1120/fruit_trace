<template>
  <div class="row justify-content-center">
    <div class="col-md-5">
      <div class="ft-card p-4">
        <h1 class="h4 mb-4">用户登录</h1>
        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">用户名</label>
            <input
              v-model="username"
              class="form-control"
              maxlength="10"
              autocomplete="username"
              placeholder="1～10 个字符，不含空格"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">密码</label>
            <input
              v-model="password"
              type="password"
              class="form-control"
              autocomplete="current-password"
              placeholder="6～20 位"
            />
          </div>
          <p v-if="err" class="text-danger small">{{ err }}</p>
          <button class="btn btn-ft-primary w-100" type="submit" :disabled="loading">
            {{ loading ? "登录中…" : "登录" }}
          </button>
        </form>
        <p class="small text-muted mt-3 mb-0">
          还没有账号？
          <router-link :to="registerLink">去注册</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { userLogin } from "../api.js";
import { refreshUserAuth } from "../auth/user.js";

const router = useRouter();
const route = useRoute();
const username = ref("");
const password = ref("");
const err = ref("");
const loading = ref(false);

const registerLink = computed(() => {
  const r = route.query.redirect;
  if (typeof r === "string" && r.startsWith("/")) {
    return { path: "/register", query: { redirect: r } };
  }
  return { path: "/register" };
});

async function submit() {
  err.value = "";
  const u = username.value.trim();
  if (!u || u.length > 10 || /\s/.test(u)) {
    err.value = "请输入有效用户名";
    return;
  }
  if (password.value.length < 6 || password.value.length > 20) {
    err.value = "密码长度为 6～20 位";
    return;
  }
  loading.value = true;
  try {
    const data = await userLogin(u, password.value);
    if (!data?.ok) {
      err.value = data?.error || "登录失败";
      return;
    }
    await refreshUserAuth();
    const redir = route.query.redirect;
    if (typeof redir === "string" && redir.startsWith("/")) {
      await router.replace(redir);
    } else {
      await router.replace({ name: "Home" });
    }
  } catch (e) {
    const st = e.response?.status;
    if (st >= 500) {
      err.value = "服务暂时不可用，请稍后重试";
    } else {
      err.value = e.response?.data?.error || "登录失败";
    }
  } finally {
    loading.value = false;
  }
}
</script>
