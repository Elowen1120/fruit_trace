<template>
  <div class="trace-page-root">
  <div v-if="loading" class="text-center py-5">
    <div class="spinner-border text-danger" role="status"></div>
    <p class="mt-2 text-muted small">加载中…</p>
  </div>
  <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
  <div v-else>
    <h1 class="h5 text-secondary text-center mb-4 page-main-title">
      果蔬食品全流程溯源模式设计
    </h1>
    <div class="ft-card p-4 mb-4">
      <div class="d-flex flex-wrap align-items-start justify-content-between gap-3">
        <div class="flex-grow-1">
          <h2 class="h4 mb-3">{{ product.product_name }}</h2>
          <ul class="list-unstyled small text-muted mb-0 trace-meta">
            <li v-if="product.product_id">🏷️ 产品编号：{{ product.product_id }}</li>
            <li v-if="product.rfid_id">🔖 RFID 编码：{{ product.rfid_id }}</li>
            <li v-if="product.product_address">
              📍 产地：{{ product.product_address }}
            </li>
            <li v-if="product.plant_time">📅 种植开始时间：{{ product.plant_time }}</li>
            <li v-if="product.check_result">✅ 抽检结果：{{ product.check_result }}</li>
            <li v-if="product.plot_no">🧭 地块编号：{{ product.plot_no }}</li>
            <li v-if="product.variety">🌱 品种：{{ product.variety }}</li>
            <li v-if="product.category">🥬 果蔬大类：{{ product.category }}</li>
          </ul>
        </div>
        <div
          class="text-center qr-wrap flex-shrink-0"
          title="手机扫码查看"
        >
          <img
            v-if="pageQrDataUrl"
            :src="pageQrDataUrl"
            alt="页面二维码"
            class="qr-img rounded border bg-white"
          />
          <div class="tiny text-muted mt-1">手机扫码查看</div>
        </div>
      </div>
    </div>

    <!-- 新鲜度分析 -->
    <div class="ft-card p-4 mb-4">
      <h5 class="mb-3">新鲜度分析</h5>
      <p class="small text-muted mb-2">{{ freshness.detail }}</p>
      <div
        v-if="freshness.level !== 'unknown'"
        class="ft-fresh-pill"
        :class="freshness.level === 'good' ? 'ok' : freshness.level === 'mid' ? 'mid' : 'bad'"
      >
        {{
          freshness.level === "good"
            ? "新鲜度良好"
            : freshness.level === "mid"
              ? "新鲜度一般"
              : "新鲜度较差，请注意"
        }}
      </div>
      <div v-else class="ft-fresh-pill unknown">数据不足，暂无法评估新鲜度</div>
    </div>

    <Timeline
      :statuses="stepStatuses"
      :planting="planting"
      :process="process"
      :storage="storage"
      :transport="transport"
      :sales="sales"
      :environment-series="environmentSeries"
    />

    <CommentSection
      :rfid="complaintRfid"
      :comments="comments"
      show-complaint
      @submitted="reload"
      @open-complaint="openComplaint"
      @open-comment="openCommentModal"
      @need-login="onNeedLogin"
    />
  </div>

  <!-- 始终挂载，避免加载/错误态下 ref 为 null 及 Modal 与路由切换时的 parentNode 报错 -->
  <ComplaintModal
    ref="complaintModalRef"
    :rfid="complaintRfid"
    @submitted="reload"
  />
  <CommentModal
    ref="commentModalRef"
    :rfid="complaintRfid"
    @submitted="reload"
  />
  <LoginRequiredModal ref="loginRequiredModalRef" />
  </div>
</template>

<script setup>
import QRCode from "qrcode";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { getTrace } from "../api.js";
import { getFreshnessTempRange } from "../utils/freshnessCategoryStandards.js";
import Timeline from "../components/Timeline.vue";
import CommentSection from "../components/CommentSection.vue";
import ComplaintModal from "../components/ComplaintModal.vue";
import CommentModal from "../components/CommentModal.vue";
import LoginRequiredModal from "../components/LoginRequiredModal.vue";
import { currentUser as currentUserRef } from "../auth/user.js";

const props = defineProps({
  rfid: { type: String, default: "" },
});

const route = useRoute();
const loading = ref(true);
const error = ref("");
const product = ref({});
const stepStatuses = ref({});
const planting = ref(null);
const process = ref(null);
const storage = ref(null);
const transport = ref(null);
const sales = ref(null);
const comments = ref([]);
const environmentSeries = ref({ planting: [], storage: [], transport: [] });
const pageQrDataUrl = ref("");
const complaintModalRef = ref(null);
const commentModalRef = ref(null);
const loginRequiredModalRef = ref(null);

const currentUser = computed(() => currentUserRef.value);

const effectiveRfid = computed(() => String(props.rfid || "").trim());

/** 投诉接口按 product_info.rfid_id 精确匹配，须用溯源接口返回的真实 RFID（P002 与 RFID002 打开页面均可） */
const complaintRfid = computed(() => {
  const rid = product.value?.rfid_id;
  if (rid != null && String(rid).trim()) return String(rid).trim();
  return effectiveRfid.value;
});

const freshness = computed(() =>
  computeFreshness(product.value, storage.value, transport.value, environmentSeries.value)
);

function computeFreshness(prod, st, tr, env) {
  const temps = [];
  const hums = [];
  const addSeriesHumidity = (arr) => {
    for (const x of arr || []) {
      if (x.humidity != null && x.humidity !== "") hums.push(Number(x.humidity));
    }
  };
  addSeriesHumidity(env?.storage);
  addSeriesHumidity(env?.transport);
  if (!hums.length && st?.storage_humidity != null) hums.push(Number(st.storage_humidity));

  const pushTemp = (v) => {
    if (v != null && v !== "") temps.push(Number(v));
  };
  for (const x of env?.storage || []) pushTemp(x?.temp);
  for (const x of env?.transport || []) pushTemp(x?.temp);
  pushTemp(st?.storage_temp);
  pushTemp(tr?.transport_temp);

  if (!temps.length) {
    return {
      level: "unknown",
      detail: "暂无仓储与运输环节温度数据，无法评估新鲜度。",
    };
  }

  const minT = Math.min(...temps);
  const maxT = Math.max(...temps);
  const avg = temps.reduce((a, b) => a + b, 0) / temps.length;
  const spread = maxT - minT;
  const halfSpread = spread / 2;

  let humText = "湿度数据暂缺";
  if (hums.length) {
    const hm = Math.min(...hums);
    const hx = Math.max(...hums);
    humText = hums.length === 1 || hm === hx ? `${hm}%` : `${hm}～${hx}%`;
  }

  const basePrefix = `基于冷链监测：温度 ${minT.toFixed(1)}～${maxT.toFixed(1)}℃，湿度 ${humText}。`;

  const cat = prod?.category || "其他";
  const { minTemp: lo, maxTemp: hi } = getFreshnessTempRange(cat);

  if (maxT > hi) {
    return {
      level: "bad",
      detail: `${basePrefix}温度超出适宜范围（最高不宜超过 ${hi}℃），可能变质，新鲜度较差，请注意。`,
    };
  }
  if (minT < lo) {
    return {
      level: "bad",
      detail: `${basePrefix}温度低于适宜范围（最低不宜低于 ${lo}℃），可能冻伤，新鲜度较差，请注意。`,
    };
  }

  const inRange = minT >= lo && maxT <= hi;
  if (spread > 2.5 && inRange) {
    return {
      level: "mid",
      detail: `${basePrefix}温度波动较大（波动超过 2.5℃），可能影响品质，新鲜度一般。`,
    };
  }

  return {
    level: "good",
    detail: `${basePrefix}温度稳定在 ${avg.toFixed(1)}℃±${halfSpread.toFixed(1)}℃，符合冷链标准。新鲜度良好。`,
  };
}

async function buildPageQr() {
  const url = `${window.location.origin}${route.fullPath}`;
  try {
    pageQrDataUrl.value = await QRCode.toDataURL(url, {
      width: 120,
      margin: 1,
      color: { dark: "#4a2c2f" },
    });
  } catch {
    pageQrDataUrl.value = "";
  }
}

function showLoginRequired(message) {
  loginRequiredModalRef.value?.show(route.fullPath, message);
}

function onNeedLogin() {
  showLoginRequired("请先登录");
}

function openComplaint() {
  if (!currentUser.value) {
    showLoginRequired("请登录后再投诉");
    return;
  }
  complaintModalRef.value?.show();
}

function openCommentModal() {
  commentModalRef.value?.show();
}

async function reload() {
  loading.value = true;
  error.value = "";
  const code = String(props.rfid || "").trim();
  if (!code) {
    error.value = "请输入RFID编号";
    loading.value = false;
    return;
  }
  try {
    const data = await getTrace(code);
    if (!data.ok) {
      error.value = data.error || "查询失败";
      return;
    }
    product.value = data.product;
    stepStatuses.value = data.step_statuses || {};
    planting.value = data.planting;
    process.value = data.process;
    storage.value = data.storage;
    transport.value = data.transport;
    sales.value = data.sales;
    comments.value = data.comments || [];
    environmentSeries.value = data.environment_series || {
      planting: [],
      storage: [],
      transport: [],
    };
    await buildPageQr();
  } catch (e) {
    error.value = e.response?.data?.error || "网络错误";
  } finally {
    loading.value = false;
  }
}

onMounted(reload);
watch(
  () => props.rfid,
  () => reload()
);
</script>

<style scoped>
.page-main-title {
  font-weight: 600;
}
.trace-meta li {
  margin-bottom: 0.35rem;
}
.qr-img {
  width: 96px;
  height: 96px;
  transition: transform 0.2s ease;
}
.qr-wrap:hover .qr-img {
  transform: scale(1.08);
}
.tiny {
  font-size: 0.7rem;
}
.ft-fresh-pill {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-weight: 600;
}
.ft-fresh-pill.ok {
  background: #e8f5e9;
  color: #2e7d32;
}
.ft-fresh-pill.mid {
  background: #fff8e1;
  color: #f57f17;
}
.ft-fresh-pill.bad {
  background: #ffebee;
  color: #c62828;
}
.ft-fresh-pill.unknown {
  background: #f5f5f5;
  color: #666;
}
</style>
