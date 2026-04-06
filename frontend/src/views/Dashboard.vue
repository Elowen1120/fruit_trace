<template>
  <div>
    <h1 class="h4 mb-3">仪表盘</h1>

    <div v-if="loadError" class="alert alert-danger mb-3" role="alert">
      {{ loadError }}
    </div>

    <div v-if="!loaded" class="text-center py-5">
      <div class="spinner-border text-danger" role="status"></div>
      <p class="mt-2 text-muted small">加载中…</p>
    </div>
    <div v-else-if="!loadError" class="row g-3">
      <div class="col-6 col-lg-3">
        <div class="ft-card ft-card-hover p-4 h-100">
          <div class="text-muted small">总产品数</div>
          <div class="display-6 fw-semibold text-danger">{{ stats.total_products }}</div>
        </div>
      </div>
      <div class="col-6 col-lg-3">
        <div class="ft-card ft-card-hover p-4 h-100">
          <div class="text-muted small">进行中流程（未闭环）</div>
          <div class="display-6 fw-semibold" style="color: #c44c4c">
            {{ stats.active_pipeline_count }}
          </div>
        </div>
      </div>
      <div class="col-6 col-lg-3">
        <div class="ft-card ft-card-hover p-4 h-100">
          <div class="text-muted small">今日评论数</div>
          <div class="display-6 fw-semibold" style="color: #f6b0b8">
            {{ stats.today_comments }}
          </div>
        </div>
      </div>
      <div class="col-6 col-lg-3">
        <div class="ft-card ft-card-hover p-4 h-100">
          <div class="text-muted small">待处理投诉数</div>
          <div class="display-6 fw-semibold" style="color: #b85c5c">
            {{ stats.pending_complaints_count }}
          </div>
        </div>
      </div>
      <div class="col-6 col-lg-3">
        <div class="ft-card ft-card-hover p-4 h-100">
          <div class="text-muted small">产品合格率</div>
          <div
            v-if="stats.total_products === 0"
            class="display-6 fw-semibold text-muted"
          >
            暂无数据
          </div>
          <div
            v-else
            class="display-6 fw-semibold"
            style="color: #8b4a5c"
          >
            {{ stats.product_qualified_rate_pct }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { getDashboardStats } from "../api.js";

const loaded = ref(false);
const loadError = ref("");
const stats = ref({
  total_products: 0,
  active_pipeline_count: 0,
  today_comments: 0,
  pending_complaints_count: 0,
  product_qualified_rate_pct: 0,
});

onMounted(async () => {
  loadError.value = "";
  try {
    const data = await getDashboardStats();
    stats.value = {
      ...stats.value,
      ...data,
      pending_complaints_count: Number(data.pending_complaints_count) || 0,
      product_qualified_rate_pct:
        data.product_qualified_rate_pct == null
          ? 0
          : Number(data.product_qualified_rate_pct) || 0,
    };
  } catch (e) {
    const msg =
      e.response?.data?.error ||
      e.response?.data?.message ||
      (e.message === "Network Error" ? "网络异常，请检查服务是否启动" : null) ||
      `加载失败 (${e.response?.status || "错误"})`;
    loadError.value = msg;
  } finally {
    loaded.value = true;
  }
});
</script>
