<template>
  <div class="row justify-content-center">
    <div class="col-md-5">
      <div class="ft-card p-4">
        <h1 class="h4 mb-4">用户注册</h1>
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
              autocomplete="new-password"
              placeholder="6～20 位"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">确认密码</label>
            <input
              v-model="password2"
              type="password"
              class="form-control"
              autocomplete="new-password"
            />
          </div>
          <p v-if="err" class="text-danger small">{{ err }}</p>
          <button class="btn btn-ft-primary w-100" type="submit" :disabled="loading">
            {{ loading ? "提交中…" : "注册" }}
          </button>
        </form>
        <p class="small text-muted mt-3 mb-0">
          已有账号？
          <router-link :to="loginLink">去登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { userRegister } from "../api.js";

const router = useRouter();
const route = useRoute();
const username = ref("");
const password = ref("");
const password2 = ref("");
const err = ref("");
const loading = ref(false);

const loginLink = computed(() => {
  const r = route.query.redirect;
  if (typeof r === "string" && r.startsWith("/")) {
    return { path: "/login", query: { redirect: r } };
  }
  return { path: "/login" };
});

async function submit() {
  err.value = "";
  const u = username.value.trim();
  if (!u || u.length > 10 || /\s/.test(u)) {
    err.value = "用户名：1～10 个字符且不能含空格";
    return;
  }
  if (password.value.length < 6 || password.value.length > 20) {
    err.value = "密码长度为 6～20 位";
    return;
  }
  if (password.value !== password2.value) {
    err.value = "两次输入的密码不一致";
    return;
  }
  loading.value = true;
  try {
    const data = await userRegister(u, password.value);
    if (!data?.ok) {
      err.value = data?.error || "注册失败";
      return;
    }
    const r = route.query.redirect;
    if (typeof r === "string" && r.startsWith("/")) {
      await router.replace({ path: "/login", query: { redirect: r } });
    } else {
      await router.replace({ path: "/login" });
    }
  } catch (e) {
    err.value = e.response?.data?.error || "注册失败";
  } finally {
    loading.value = false;
  }
}
</script>
