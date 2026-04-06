<template>
  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="ft-card p-4 p-md-5 text-center home-hero">
        <div class="d-inline-flex align-items-center justify-content-center gap-3 home-hero-row">
          <img
            src="/logo.svg"
            alt=""
            width="72"
            height="72"
            class="home-hero-logo flex-shrink-0"
          />
          <span class="home-hero-title mb-0">果蔬溯源</span>
        </div>
        <p class="text-muted mt-4 mb-0 home-hero-sub">
          从田间地头到餐桌，全程可追溯种植、加工、仓储、运输与销售信息，守护每一份新鲜与安全。
        </p>

        <form
          class="home-query mx-auto mt-4"
          @submit.prevent="onQuery"
        >
          <div class="input-group input-group-lg home-query-group">
            <input
              v-model.trim="rfidInput"
              type="text"
              class="form-control"
              placeholder="例如：RFID001 或 P001"
              maxlength="80"
              autocomplete="off"
            />
            <button class="btn btn-ft-primary ft-btn-press" type="submit" :disabled="querying">
              {{ querying ? "查询中…" : "查询" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { checkTraceExists } from "../api.js";
import { showToast } from "../utils/toast.js";

const router = useRouter();
const rfidInput = ref("");
const querying = ref(false);

async function onQuery() {
  const code = rfidInput.value.trim();
  if (!code) {
    showToast("请输入产品编号或 RFID 编码", "warning");
    return;
  }
  querying.value = true;
  try {
    const { ok, data, status } = await checkTraceExists(code);
    if (status >= 500) {
      showToast("服务暂时不可用，请稍后重试", "error");
      return;
    }
    if (typeof data !== "object" || data === null) {
      showToast("服务响应异常，请稍后重试", "error");
      return;
    }
    if (status === 404 || !ok) {
      showToast(data?.error || "未找到该产品", "warning");
      return;
    }
    router.push({ path: "/trace", query: { rfid: code } });
  } catch (e) {
    const msg =
      e?.message === "Network Error"
        ? "网络异常，请检查后端是否已启动"
        : "无法连接服务器，请稍后重试";
    showToast(msg, "error");
  } finally {
    querying.value = false;
  }
}
</script>

<style scoped>
.home-hero-logo {
  display: block;
}
.home-hero-title {
  font-size: clamp(1.75rem, 5vw, 2.25rem);
  font-weight: 700;
  color: #c44c4c;
  letter-spacing: 0.02em;
}
.home-hero-row {
  gap: 1.25rem !important;
}
.home-hero-sub {
  font-size: 0.95rem;
  line-height: 1.65;
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
}
.home-query {
  max-width: 520px;
}
.home-query-group {
  box-shadow: 0 0.15rem 0.75rem rgba(196, 76, 76, 0.08);
  border-radius: 0.5rem;
  overflow: hidden;
}
</style>
