<template>
  <div class="timeline-wrap">
    <h5 class="mb-3">全流程环节</h5>
    <div class="d-flex flex-column flex-md-row flex-wrap gap-2 align-items-stretch">
      <div
        v-for="(s, i) in steps"
        :key="s.key"
        class="flex-grow-1 position-relative"
        style="min-width: 140px"
      >
        <div
          class="rounded-3 p-3 text-center border step-box h-100"
          :class="boxClass(statuses[s.key])"
        >
          <div class="fw-semibold">{{ s.label }}</div>
          <div
            class="small mt-1 opacity-75 d-flex align-items-center justify-content-center gap-1 flex-wrap"
          >
            <span
              v-if="statuses[s.key] === 'active'"
              class="ft-step-dot"
              title="当前环节"
            ></span>
            <span v-if="statusText(statuses[s.key])">{{ statusText(statuses[s.key]) }}</span>
          </div>
        </div>
        <div
          v-if="i < steps.length - 1"
          class="d-none d-md-block arrow-desktop"
          aria-hidden="true"
        >
          →
        </div>
      </div>
    </div>

    <div class="mt-4">
      <h6 class="text-secondary">环节详情</h6>
      <div class="row g-3">
        <div class="col-12" v-if="planting">
          <div class="ft-card p-3">
            <strong>种植</strong>
            <div v-if="environmentSeries.planting?.length" class="table-responsive mt-2">
              <table class="table table-sm table-bordered mb-2 small">
                <thead>
                  <tr><th>时间</th><th>温度(℃)</th><th>湿度(%)</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(r, i) in environmentSeries.planting" :key="'p'+i">
                    <td>{{ r.label }}</td>
                    <td>{{ r.temp }}</td>
                    <td>{{ r.humidity ?? "—" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <ul class="mb-0 mt-2 small">
              <li>⏱ 采收时间：{{ formatOperateTimeMinute(planting.harvest_time) || "—" }}</li>
              <li>💧 每日平均浇水量：{{ planting.daily_water }} L</li>
              <li>☀️ 每日平均光照时间：{{ planting.light_hour }} h</li>
              <li>🌡️ 每日平均环境温度：{{ planting.temp }} ℃</li>
              <li>🌿 每日平均土壤湿度：{{ planting.soil_humidity }} %</li>
              <li>🧴 每周平均施肥量：{{ planting.fertilizer }}（kg）</li>
              <li>⚠️ 每周平均施药量：{{ planting.pesticide }}（L）</li>
            </ul>
            <p class="small text-muted mb-0 mt-2">（按每亩计）</p>
          </div>
        </div>
        <div class="col-12" v-if="process">
          <div class="ft-card p-3">
            <strong>加工</strong>
            <ul class="mb-0 mt-2 small">
              <li>⏱ 加工开始时间：{{ formatOperateTimeMinute(process.process_start_time) || "—" }}</li>
              <li>🏭 加工车间：{{ process.workshop }}</li>
              <li>🧼 清洗：{{ process.clean_method }}</li>
              <li>⚙️ 加工方式：{{ process.process_method || "—" }}</li>
              <li>📦 包装：{{ process.package_material }}</li>
              <li>⏱ 加工结束时间：{{ formatOperateTimeMinute(process.process_end_time) || "—" }}</li>
              <li>✅ 质检结果：{{ process.quality_result }}</li>
              <li v-if="process.report_img" class="d-flex flex-wrap align-items-center gap-2">
                <span>🖼️ 质检报告：</span>
                <template v-if="isImageMedia(process.report_img)">
                  <img
                    :src="mediaUrl(process.report_img)"
                    alt="质检报告"
                    class="ft-trace-thumb rounded border"
                    role="button"
                    tabindex="0"
                    @click="openLightbox(process.report_img)"
                    @keyup.enter="openLightbox(process.report_img)"
                  />
                </template>
                <button
                  v-else
                  type="button"
                  class="btn btn-link btn-sm p-0 align-baseline"
                  @click="openLightbox(process.report_img)"
                >
                  查看（PDF）
                </button>
              </li>
            </ul>
          </div>
        </div>
        <div class="col-12" v-if="storage">
          <div class="ft-card p-3">
            <strong>仓储</strong>
            <EnvSeriesChart class="mt-2" :records="storageChartRecords" />
            <ul class="mb-0 mt-2 small">
              <li>⏱ 入库时间：{{ formatOperateTimeMinute(storage.in_time) || "—" }}</li>
              <li>🏢 仓库地址：{{ storage.warehouse_addr }}</li>
              <li>🌡️ 存储温度：{{ storage.storage_temp }} ℃</li>
              <li>💧 存储湿度：{{ storage.storage_humidity }} %</li>
              <li>📅 保质期：{{ storage.shelf_life }} 天</li>
              <li>⏱ 出库时间：{{ formatOperateTimeMinute(storage.out_time) || "—" }}</li>
            </ul>
          </div>
        </div>
        <div class="col-12" v-if="transport">
          <div class="ft-card p-3">
            <strong>运输</strong>
            <EnvSeriesChart class="mt-2" :records="transportChartRecords" />
            <ul class="mb-0 mt-2 small">
              <li>⏱ 发货时间：{{ formatOperateTimeMinute(transport.departure_time) || "—" }}</li>
              <li>🚚 承运方：{{ transport.transport_company }}</li>
              <li>📄 运单号：{{ transport.waybill_no }}</li>
              <li>🌡️ 运输温度：{{ transport.transport_temp }} ℃</li>
              <li>⏱ 到达时间：{{ formatOperateTimeMinute(transport.arrive_time) || "—" }}</li>
              <li>✍️ 签收人：{{ transport.receiver }}</li>
              <li v-if="transport.track_img" class="d-flex flex-wrap align-items-center gap-2">
                <span>🗺️ 运输轨迹：</span>
                <img
                  :src="mediaUrl(transport.track_img)"
                  alt="运输轨迹"
                  class="ft-trace-thumb rounded border"
                  role="button"
                  tabindex="0"
                  @click="openLightbox(transport.track_img)"
                  @keyup.enter="openLightbox(transport.track_img)"
                />
              </li>
            </ul>
          </div>
        </div>
        <div class="col-12" v-if="sales">
          <div class="ft-card p-3">
            <strong>销售</strong>
            <ul class="mb-0 mt-2 small">
              <li>⏱ 商品上架时间：{{ formatOperateTimeMinute(sales.listing_time) || "—" }}</li>
              <li>📍 销售地点：{{ sales.store_name }}</li>
              <li>💰 销售价格：{{ sales.price }} 元 / 500g</li>
              <li>📅 销售截止时间：{{ sales.sale_end_date }}</li>
              <li>👤 负责人：{{ sales.seller }}</li>
              <li v-if="sales.voucher_img" class="d-flex flex-wrap align-items-center gap-2">
                <span>🧾 销售凭证：</span>
                <img
                  :src="mediaUrl(sales.voucher_img)"
                  alt="销售凭证"
                  class="ft-trace-thumb rounded border"
                  role="button"
                  tabindex="0"
                  @click="openLightbox(sales.voucher_img)"
                  @keyup.enter="openLightbox(sales.voucher_img)"
                />
              </li>
            </ul>
          </div>
        </div>
        <div class="col-12" v-if="done">
          <div class="ft-card p-3 border-success">
            <strong>已完成</strong>
            <p class="mb-0 small mt-2">该批次全流程已闭环。</p>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-show="lightbox.show"
        class="ft-lightbox"
        role="dialog"
        aria-modal="true"
        aria-label="大图预览"
        @click.self="closeLightbox"
      >
        <div class="ft-lightbox-panel">
          <button
            type="button"
            class="btn-close btn-close-white ft-lightbox-close"
            aria-label="关闭"
            @click="closeLightbox"
          ></button>
          <img
            v-if="lightbox.show && lightbox.kind === 'image'"
            :src="lightbox.url"
            class="ft-lightbox-img"
            alt="预览"
            @click.stop
          />
          <iframe
            v-else-if="lightbox.show && lightbox.kind === 'pdf'"
            :src="lightbox.url"
            class="ft-lightbox-pdf"
            title="PDF"
            @click.stop
          />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { resolveUploadUrl } from "../config.js";
import { formatOperateTimeMinute } from "../utils/formatTime.js";
import {
  resolveStorageChartRecords,
  resolveTransportChartRecords,
} from "../utils/simulateEnvSeries.js";
import EnvSeriesChart from "./EnvSeriesChart.vue";

const props = defineProps({
  statuses: { type: Object, default: () => ({}) },
  planting: { type: Object, default: null },
  process: { type: Object, default: null },
  storage: { type: Object, default: null },
  transport: { type: Object, default: null },
  sales: { type: Object, default: null },
  environmentSeries: {
    type: Object,
    default: () => ({ planting: [], storage: [], transport: [] }),
  },
});

const steps = [
  { key: "种植", label: "种植" },
  { key: "加工", label: "加工" },
  { key: "仓储", label: "仓储" },
  { key: "运输", label: "运输" },
  { key: "销售", label: "销售" },
  { key: "已完成", label: "已完成" },
];

function boxClass(st) {
  if (st === "active") return "ft-step-active";
  if (st === "completed") return "ft-step-completed";
  return "ft-step-neutral";
}

/** 仅「已完成」「待开始」；当前环节不显示「进行中」文案，仅用圆点与配色区分 */
function statusText(st) {
  if (st === "completed") return "已完成";
  if (st === "active") return "";
  if (st === "skipped") return "已跳过";
  return "待开始";
}

const done = computed(() => props.statuses["已完成"] === "active" || props.statuses["已完成"] === "completed");

/** env_readings 优先；否则用环节表单点在前端生成 5 点模拟曲线（不写库） */
const storageChartRecords = computed(() =>
  resolveStorageChartRecords(
    props.environmentSeries?.storage,
    props.storage
  )
);

const transportChartRecords = computed(() =>
  resolveTransportChartRecords(
    props.environmentSeries?.transport,
    props.transport
  )
);

const lightbox = ref({
  show: false,
  url: "",
  kind: "image",
});

function mediaUrl(path) {
  return resolveUploadUrl(path);
}

function isImageMedia(path) {
  return typeof path === "string" && /\.(jpe?g|png|gif|webp)(\?|#|$)/i.test(path);
}

function lightboxKindForPath(path) {
  if (typeof path === "string" && /\.pdf(\?|#|$)/i.test(path)) return "pdf";
  return "image";
}

function openLightbox(path) {
  const url = resolveUploadUrl(path);
  if (!url) return;
  lightbox.value = {
    show: true,
    url,
    kind: lightboxKindForPath(path),
  };
}

function closeLightbox() {
  lightbox.value = { ...lightbox.value, show: false };
}
</script>

<style scoped>
.step-box {
  transition: transform 0.15s ease;
}
.arrow-desktop {
  position: absolute;
  right: -10px;
  top: 50%;
  transform: translateY(-50%);
  font-weight: bold;
  color: #c44c4c;
  z-index: 1;
}
.ft-step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.35);
  animation: ftPulse 1.4s ease-in-out infinite;
}
.ft-step-active .ft-step-dot {
  background: #fff;
}
@keyframes ftPulse {
  50% {
    transform: scale(1.15);
    opacity: 0.85;
  }
}
.ft-trace-thumb {
  max-height: 56px;
  max-width: 120px;
  object-fit: cover;
  cursor: pointer;
  vertical-align: middle;
}
</style>

<style>
/* 全屏预览挂载到 body，避免 scoped 裁剪 */
.ft-lightbox {
  position: fixed;
  inset: 0;
  z-index: 1055;
  background: rgba(0, 0, 0, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.ft-lightbox-panel {
  position: relative;
  max-width: min(96vw, 1200px);
  max-height: 92vh;
}
.ft-lightbox-close {
  position: absolute;
  top: -0.25rem;
  right: -0.25rem;
  z-index: 2;
  opacity: 1;
  filter: drop-shadow(0 0 2px #000);
}
.ft-lightbox-img {
  display: block;
  max-width: min(96vw, 1200px);
  max-height: 88vh;
  width: auto;
  height: auto;
  margin: 0 auto;
  border-radius: 0.35rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
}
.ft-lightbox-pdf {
  width: min(96vw, 900px);
  height: min(85vh, 800px);
  border: 0;
  border-radius: 0.35rem;
  background: #fff;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
}
</style>
