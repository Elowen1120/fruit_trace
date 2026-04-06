<template>
  <div
    class="modal fade"
    :id="modalId"
    tabindex="-1"
    ref="modalRef"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ title }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body" v-if="step">
          <div v-if="status === 'later'" class="alert alert-secondary">
            请先完成前面的环节。
          </div>
          <div v-else-if="status === 'skipped'" class="alert alert-light border">
            该环节已跳过，无法再填写该环节数据。
          </div>
          <template v-else-if="step === '已完成'">
            <p v-if="status === 'fillable' || status === 'active'">
              确认将该 RFID 的全流程标记为「已完成」？需已填写销售环节。
            </p>
            <p v-else class="text-muted">当前状态不可操作。</p>
          </template>
          <template v-else>
            <fieldset :disabled="status === 'completed' || status === 'skipped'" class="border-0 m-0 p-0">
            <div class="row g-2" v-if="step === '种植'">
              <div class="col-12">
                <label class="form-label">采收时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.operate_time"
                />
              </div>
              <div class="col-12" v-if="canSimulate">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger ft-btn-press"
                  @click="simulatePlanting"
                >
                  模拟传感器数据
                </button>
              </div>
              <div class="col-md-6">
                <label class="form-label">每日平均浇水量 (L)</label>
                <input type="number" class="form-control" v-model.number="form.daily_water" />
              </div>
              <div class="col-md-6">
                <label class="form-label">每日平均光照时间 (h)</label>
                <input type="number" class="form-control" v-model.number="form.light_hour" />
              </div>
              <div class="col-md-6">
                <label class="form-label">每日平均环境温度 (℃)</label>
                <input type="number" step="0.1" class="form-control" v-model.number="form.temp" />
              </div>
              <div class="col-md-6">
                <label class="form-label">每日平均土壤湿度 (%)</label>
                <input type="number" class="form-control" v-model.number="form.soil_humidity" />
              </div>
              <div class="col-12">
                <label class="form-label">每周平均施肥量（kg）</label>
                <input class="form-control" v-model="form.fertilizer" />
              </div>
              <div class="col-12">
                <label class="form-label">每周平均施药量（L）</label>
                <input class="form-control" v-model="form.pesticide" />
              </div>
              <div class="col-12">
                <p class="small text-muted mb-0">
                  注：以上浇水量、施肥量、施药量均按每亩面积计算
                </p>
              </div>
              <div class="col-12">
                <label class="form-label">负责人</label>
                <input class="form-control" v-model="form.manager" />
              </div>
            </div>
            <div class="row g-2" v-else-if="step === '加工'">
              <div class="col-12">
                <label class="form-label">加工开始时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.operate_time"
                />
              </div>
              <div class="col-12">
                <label class="form-label">加工结束时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.process_end_time"
                />
              </div>
              <div class="col-12" v-if="canSimulate">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger ft-btn-press"
                  @click="simulateProcess"
                >
                  模拟数据
                </button>
              </div>
              <div class="col-md-6">
                <label class="form-label">加工车间</label>
                <input class="form-control" v-model="form.workshop" />
              </div>
              <div class="col-md-6">
                <label class="form-label">清洗</label>
                <input class="form-control" v-model="form.clean_method" />
              </div>
              <div class="col-md-6">
                <label class="form-label">加工方式</label>
                <input class="form-control" v-model="form.process_method" />
              </div>
              <div class="col-md-6">
                <label class="form-label">包装</label>
                <input class="form-control" v-model="form.package_material" />
              </div>
              <div class="col-md-6">
                <label class="form-label">质检结果</label>
                <select class="form-select" v-model="form.quality_result">
                  <option value="合格">合格</option>
                  <option value="不合格">不合格</option>
                </select>
              </div>
              <div class="col-12">
                <label class="form-label">上传质检报告图片（可选，jpg / png / pdf）</label>
                <input
                  ref="reportFileRef"
                  type="file"
                  class="form-control"
                  accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
                  @change="onReportFile"
                />
                <div v-if="reportFileHint" class="small text-muted mt-1">{{ reportFileHint }}</div>
                <div v-if="reportBlobUrl" class="mt-2">
                  <img
                    :src="reportBlobUrl"
                    alt="预览"
                    class="img-thumbnail"
                    style="max-height: 160px"
                  />
                </div>
                <div
                  v-if="form.report_img && !pendingReportFile"
                  class="small mt-2 text-muted"
                >
                  已保存文件：
                  <template v-if="isPdfPath(form.report_img)">PDF</template>
                  <img
                    v-else-if="isImagePath(form.report_img)"
                    :src="resolveUploadUrl(form.report_img)"
                    alt=""
                    class="img-thumbnail mt-1 d-block"
                    style="max-height: 120px"
                  />
                </div>
              </div>
            </div>
            <div class="row g-2" v-else-if="step === '仓储'">
              <div class="col-12">
                <label class="form-label">入库时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.operate_time"
                />
              </div>
              <div class="col-12">
                <label class="form-label">出库时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.out_time"
                />
              </div>
              <div class="col-12" v-if="canSimulate">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger ft-btn-press"
                  @click="simulateStorage"
                >
                  模拟数据
                </button>
              </div>
              <div class="col-12">
                <label class="form-label">仓库地址</label>
                <input class="form-control" v-model="form.warehouse_addr" />
              </div>
              <div class="col-md-6">
                <label class="form-label">存储温度 (℃)</label>
                <input type="number" step="0.1" class="form-control" v-model.number="form.storage_temp" />
              </div>
              <div class="col-md-6">
                <label class="form-label">存储湿度 (%)</label>
                <input type="number" class="form-control" v-model.number="form.storage_humidity" />
              </div>
              <div class="col-md-6">
                <label class="form-label">保质期 (天)</label>
                <input type="number" class="form-control" v-model.number="form.shelf_life" />
              </div>
              <div class="col-md-6">
                <label class="form-label">仓库负责人</label>
                <input class="form-control" v-model="form.storekeeper" />
              </div>
            </div>
            <div class="row g-2" v-else-if="step === '运输'">
              <div class="col-12">
                <label class="form-label">发货时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.operate_time"
                />
              </div>
              <div class="col-12">
                <label class="form-label">到达时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.arrive_time"
                />
              </div>
              <div class="col-12" v-if="canSimulate">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger ft-btn-press"
                  @click="simulateTransport"
                >
                  模拟数据
                </button>
              </div>
              <div class="col-md-6">
                <label class="form-label">承运方</label>
                <input class="form-control" v-model="form.transport_company" />
              </div>
              <div class="col-md-6">
                <label class="form-label">运单号</label>
                <input class="form-control" v-model="form.waybill_no" />
              </div>
              <div class="col-md-6">
                <label class="form-label">运输温度 (℃)</label>
                <input type="number" step="0.1" class="form-control" v-model.number="form.transport_temp" />
              </div>
              <div class="col-md-6">
                <label class="form-label">签收人</label>
                <input class="form-control" v-model="form.receiver" />
              </div>
              <div class="col-12">
                <label class="form-label">上传运输轨迹截图（可选，jpg / png）</label>
                <input
                  ref="trackFileRef"
                  type="file"
                  class="form-control"
                  accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                  @change="onTrackFile"
                />
                <div v-if="trackBlobUrl" class="mt-2">
                  <img
                    :src="trackBlobUrl"
                    alt="预览"
                    class="img-thumbnail"
                    style="max-height: 160px"
                  />
                </div>
                <div
                  v-if="form.track_img && !pendingTrackFile"
                  class="small mt-2 text-muted"
                >
                  已保存截图：
                  <img
                    :src="resolveUploadUrl(form.track_img)"
                    alt=""
                    class="img-thumbnail mt-1 d-block"
                    style="max-height: 120px"
                  />
                </div>
              </div>
            </div>
            <div class="row g-2" v-else-if="step === '销售'">
              <div class="col-12">
                <label class="form-label">商品上架时间</label>
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="form.operate_time"
                />
              </div>
              <div class="col-12" v-if="canSimulate">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger ft-btn-press"
                  @click="simulateSales"
                >
                  模拟数据
                </button>
              </div>
              <div class="col-12">
                <label class="form-label">销售地点</label>
                <input class="form-control" v-model="form.store_name" />
              </div>
              <div class="col-md-6">
                <label class="form-label">销售价格 (元/500g)</label>
                <input type="number" step="0.01" class="form-control" v-model.number="form.price" />
              </div>
              <div class="col-md-6">
                <label class="form-label">负责人</label>
                <input class="form-control" v-model="form.seller" />
              </div>
              <div class="col-md-6">
                <label class="form-label">销售截止日期</label>
                <input type="date" class="form-control" v-model="form.sale_end_date" />
              </div>
              <div class="col-12">
                <label class="form-label">上传销售凭证图片（可选，jpg / png）</label>
                <input
                  ref="voucherFileRef"
                  type="file"
                  class="form-control"
                  accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                  @change="onVoucherFile"
                />
                <div v-if="voucherBlobUrl" class="mt-2">
                  <img
                    :src="voucherBlobUrl"
                    alt="预览"
                    class="img-thumbnail"
                    style="max-height: 160px"
                  />
                </div>
                <div
                  v-if="form.voucher_img && !pendingVoucherFile"
                  class="small mt-2 text-muted"
                >
                  已保存凭证：
                  <img
                    :src="resolveUploadUrl(form.voucher_img)"
                    alt=""
                    class="img-thumbnail mt-1 d-block"
                    style="max-height: 120px"
                  />
                </div>
              </div>
            </div>
            </fieldset>
          </template>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
          <button
            v-if="canSkip"
            type="button"
            class="btn btn-outline-danger"
            :disabled="loading"
            @click="onSkipStep"
          >
            跳过此环节
          </button>
          <button
            v-if="canSubmit"
            type="button"
            class="btn btn-ft-primary"
            :disabled="loading"
            @click="onSave"
          >
            {{
              loading
                ? "加载中…"
                : step === "已完成"
                  ? "确认完成"
                  : "保存"
            }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { Modal } from "bootstrap";
import { resolveUploadUrl } from "../config.js";
import {
  completeFlow,
  getStepData,
  saveStep,
  saveStepFormData,
  skipStep,
} from "../api.js";
import { showToast } from "../utils/toast.js";

const props = defineProps({
  modalId: { type: String, required: true },
  rfid: { type: String, default: "" },
  step: { type: String, default: "" },
  status: { type: String, default: "" },
});

const emit = defineEmits(["saved"]);

const modalRef = ref(null);
let modalInstance = null;

const form = ref({});
const loading = ref(false);

const reportFileRef = ref(null);
const trackFileRef = ref(null);
const voucherFileRef = ref(null);
const pendingReportFile = ref(null);
const pendingTrackFile = ref(null);
const pendingVoucherFile = ref(null);
const reportBlobUrl = ref("");
const trackBlobUrl = ref("");
const voucherBlobUrl = ref("");

function isPdfPath(p) {
  return typeof p === "string" && /\.pdf(\?|#|$)/i.test(p);
}

function isImagePath(p) {
  return typeof p === "string" && /\.(jpe?g|png)(\?|#|$)/i.test(p);
}

function resetReportUpload() {
  if (reportBlobUrl.value) URL.revokeObjectURL(reportBlobUrl.value);
  reportBlobUrl.value = "";
  pendingReportFile.value = null;
  if (reportFileRef.value) reportFileRef.value.value = "";
}

function resetTrackUpload() {
  if (trackBlobUrl.value) URL.revokeObjectURL(trackBlobUrl.value);
  trackBlobUrl.value = "";
  pendingTrackFile.value = null;
  if (trackFileRef.value) trackFileRef.value.value = "";
}

function resetVoucherUpload() {
  if (voucherBlobUrl.value) URL.revokeObjectURL(voucherBlobUrl.value);
  voucherBlobUrl.value = "";
  pendingVoucherFile.value = null;
  if (voucherFileRef.value) voucherFileRef.value.value = "";
}

function resetAllUploads() {
  resetReportUpload();
  resetTrackUpload();
  resetVoucherUpload();
}

function onReportFile(e) {
  const file = e.target.files?.[0] || null;
  if (reportBlobUrl.value) URL.revokeObjectURL(reportBlobUrl.value);
  reportBlobUrl.value = "";
  pendingReportFile.value = null;
  if (!file) return;
  pendingReportFile.value = file;
  if (file.type.startsWith("image/")) {
    reportBlobUrl.value = URL.createObjectURL(file);
  }
}

function onTrackFile(e) {
  const file = e.target.files?.[0] || null;
  if (trackBlobUrl.value) URL.revokeObjectURL(trackBlobUrl.value);
  trackBlobUrl.value = "";
  pendingTrackFile.value = null;
  if (!file) return;
  pendingTrackFile.value = file;
  if (file.type.startsWith("image/")) {
    trackBlobUrl.value = URL.createObjectURL(file);
  }
}

function onVoucherFile(e) {
  const file = e.target.files?.[0] || null;
  if (voucherBlobUrl.value) URL.revokeObjectURL(voucherBlobUrl.value);
  voucherBlobUrl.value = "";
  pendingVoucherFile.value = null;
  if (!file) return;
  pendingVoucherFile.value = file;
  if (file.type.startsWith("image/")) {
    voucherBlobUrl.value = URL.createObjectURL(file);
  }
}

const reportFileHint = computed(() => {
  const f = pendingReportFile.value;
  if (!f) return "";
  if (f.type === "application/pdf" || /\.pdf$/i.test(f.name)) {
    return `已选择 PDF：${f.name}（保存后可在溯源页查看）`;
  }
  return "";
});

onBeforeUnmount(() => {
  resetAllUploads();
});

const title = computed(() => {
  if (!props.step) return "环节";
  const st =
    props.status === "completed" || props.status === "skipped"
      ? "查看"
      : props.status === "active"
        ? "编辑"
        : "填写";
  return `${st} · ${props.step}`;
});

const canSubmit = computed(() => {
  if (!props.step || props.status === "later") return false;
  if (props.status === "completed" || props.status === "skipped") return false;
  if (props.step === "已完成") return props.status === "fillable" || props.status === "active";
  return props.status === "fillable" || props.status === "active";
});

const canSkip = computed(() => {
  if (!props.step) return false;
  if (props.status !== "fillable" && props.status !== "active") return false;
  return ["加工", "仓储", "运输"].includes(props.step);
});

/** 仅填充表单、不保存；与可编辑状态一致 */
const canSimulate = computed(
  () =>
    props.step &&
    props.step !== "已完成" &&
    (props.status === "fillable" || props.status === "active")
);

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomFloat(min, max, decimals) {
  const v = Math.random() * (max - min) + min;
  return Number(v.toFixed(decimals));
}

function pickOne(list) {
  return list[Math.floor(Math.random() * list.length)];
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function nowDateTimeLocal() {
  const d = new Date();
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

/** type="date" 默认值 yyyy-MM-dd */
function nowDateLocal() {
  const d = new Date();
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function isoToDatetimeLocal(iso) {
  if (!iso || typeof iso !== "string") return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

const WORKSHOPS = ["分拣车间A", "包装车间B", "清洗车间C", "预冷车间D"];
const CLEAN_METHODS = ["气泡清洗", "高压喷淋", "超声波清洗"];
const PACKAGE_MATERIALS = ["食品级塑料袋", "纸箱", "真空包装"];
const QUALITY_RESULTS = ["合格", "不合格"];
const TRANSPORT_COMPANIES = ["顺丰冷链", "京东物流", "德邦快递"];

function simulatePlanting() {
  const f = form.value;
  f.daily_water = randomInt(300, 800);
  f.light_hour = randomInt(6, 12);
  f.temp = randomFloat(18, 35, 1);
  f.soil_humidity = randomInt(50, 85);
}

function simulateProcess() {
  const f = form.value;
  f.workshop = pickOne(WORKSHOPS);
  f.clean_method = pickOne(CLEAN_METHODS);
  f.package_material = pickOne(PACKAGE_MATERIALS);
  f.quality_result = pickOne(QUALITY_RESULTS);
}

function simulateStorage() {
  const f = form.value;
  f.storage_temp = randomFloat(-2, 10, 1);
  f.storage_humidity = randomInt(60, 90);
  f.shelf_life = randomInt(30, 365);
}

function simulateTransport() {
  const f = form.value;
  f.transport_company = pickOne(TRANSPORT_COMPANIES);
  f.transport_temp = randomFloat(-2, 10, 1);
}

function simulateSales() {
  form.value.price = randomFloat(5, 50, 2);
}

function finiteNum(v) {
  return typeof v === "number" && Number.isFinite(v);
}

function nonEmptyStr(v) {
  return typeof v === "string" && v.trim().length > 0;
}

/** 提交前校验：全部必填且数字字段为有效数字 */
function validateCurrentStep() {
  const f = form.value;
  if (
    props.step &&
    ["种植", "加工", "仓储", "运输", "销售"].includes(props.step)
  ) {
    if (!nonEmptyStr(f.operate_time)) {
      if (props.step === "种植") return "请选择采收时间";
      if (props.step === "加工") return "请选择加工开始时间";
      if (props.step === "仓储") return "请选择入库时间";
      if (props.step === "运输") return "请选择发货时间";
      if (props.step === "销售") return "请选择商品上架时间";
      return "请选择时间";
    }
  }
  if (props.step === "种植") {
    if (!finiteNum(f.daily_water)) return "请填写有效的每日平均浇水量（数字）";
    if (!finiteNum(f.light_hour)) return "请填写有效的每日平均光照时间（数字）";
    if (!finiteNum(f.temp)) return "请填写有效的每日平均环境温度（数字）";
    if (!finiteNum(f.soil_humidity)) return "请填写有效的每日平均土壤湿度（数字）";
    if (!nonEmptyStr(f.fertilizer)) return "请填写每周平均施肥量";
    if (!nonEmptyStr(f.pesticide)) return "请填写每周平均施药量";
    if (!nonEmptyStr(f.manager)) return "请填写负责人";
  } else if (props.step === "加工") {
    if (!nonEmptyStr(f.workshop)) return "请填写加工车间";
    if (!nonEmptyStr(f.clean_method)) return "请填写清洗方式";
    if (!nonEmptyStr(f.package_material)) return "请填写包装材料";
    if (!["合格", "不合格"].includes(String(f.quality_result || "").trim())) {
      return "请选择质检结果";
    }
  } else if (props.step === "仓储") {
    if (!nonEmptyStr(f.warehouse_addr)) return "请填写仓库地址";
    if (!finiteNum(f.storage_temp)) return "请填写有效的存储温度（数字）";
    if (!finiteNum(f.storage_humidity)) return "请填写有效的存储湿度（数字）";
    if (!finiteNum(f.shelf_life)) return "请填写有效的保质期（数字，天）";
    if (!nonEmptyStr(f.storekeeper)) return "请填写仓库负责人";
  } else if (props.step === "运输") {
    if (!nonEmptyStr(f.transport_company)) return "请填写承运方";
    if (!nonEmptyStr(f.waybill_no)) return "请填写运单号";
    if (!finiteNum(f.transport_temp)) return "请填写有效的运输温度（数字）";
    if (!nonEmptyStr(f.receiver)) return "请填写签收人";
  } else if (props.step === "销售") {
    if (!nonEmptyStr(f.store_name)) return "请填写销售地点";
    if (!finiteNum(f.price)) return "请填写有效的售价（数字）";
    if (!nonEmptyStr(f.seller)) return "请填写负责人";
    if (!nonEmptyStr(f.sale_end_date)) return "请选择销售截止日期";
  }
  return null;
}

function emptyForm() {
  return {
    daily_water: 0,
    light_hour: 0,
    temp: 0,
    soil_humidity: 0,
    fertilizer: "",
    pesticide: "",
    manager: "",
    workshop: "",
    clean_method: "",
    package_material: "",
    quality_result: "合格",
    report_img: "",
    warehouse_addr: "",
    storage_temp: 0,
    storage_humidity: 0,
    shelf_life: 0,
    storekeeper: "",
    transport_company: "",
    waybill_no: "",
    transport_temp: 0,
    receiver: "",
    track_img: "",
    store_name: "",
    price: 0,
    seller: "",
    sale_end_date: "",
    voucher_img: "",
    harvest_time: "",
    process_method: "",
    process_end_time: "",
    out_time: "",
    arrive_time: "",
    operate_time: "",
  };
}

async function loadData() {
  resetAllUploads();
  if (!props.rfid || !props.step || props.step === "已完成") {
    form.value = emptyForm();
    return;
  }
  loading.value = true;
  try {
    const res = await getStepData(props.rfid, props.step);
    const d = res.data;
    const base = emptyForm();
    if (d) Object.assign(base, d);
    if (props.step === "销售") {
      if (base.sale_end_date && String(base.sale_end_date).length >= 10) {
        base.sale_end_date = String(base.sale_end_date).slice(0, 10);
      } else {
        base.sale_end_date = nowDateLocal();
      }
    } else if (base.sale_end_date && String(base.sale_end_date).length >= 10) {
      base.sale_end_date = String(base.sale_end_date).slice(0, 10);
    }
    if (d?.operate_time) {
      base.operate_time = isoToDatetimeLocal(d.operate_time);
    } else {
      base.operate_time = nowDateTimeLocal();
    }
    // 新论文字段：把后端 ISO DATETIME 转为 datetime-local 所需格式
    if (d?.harvest_time) base.harvest_time = isoToDatetimeLocal(d.harvest_time);
    if (d?.process_end_time) {
      base.process_end_time = isoToDatetimeLocal(d.process_end_time);
    } else if (props.step === "加工") {
      base.process_end_time = nowDateTimeLocal();
    }
    if (d?.out_time) {
      base.out_time = isoToDatetimeLocal(d.out_time);
    } else if (props.step === "仓储") {
      base.out_time = nowDateTimeLocal();
    }
    if (d?.arrive_time) {
      base.arrive_time = isoToDatetimeLocal(d.arrive_time);
    } else if (props.step === "运输") {
      base.arrive_time = nowDateTimeLocal();
    }
    if (props.step === "加工") {
      const qr = String(base.quality_result || "").trim();
      base.quality_result = ["合格", "不合格"].includes(qr) ? qr : "合格";
    }
    form.value = base;
  } catch {
    const b = emptyForm();
    b.operate_time = nowDateTimeLocal();
    if (props.step === "加工") b.process_end_time = nowDateTimeLocal();
    if (props.step === "仓储") b.out_time = nowDateTimeLocal();
    if (props.step === "运输") b.arrive_time = nowDateTimeLocal();
    if (props.step === "销售") b.sale_end_date = nowDateLocal();
    form.value = b;
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.rfid, props.step, props.status],
  () => {
    loadData();
  }
);

onMounted(() => {
  modalInstance = new Modal(modalRef.value);
  loadData();
});

function show() {
  loadData();
  modalInstance?.show();
}

function hide() {
  modalInstance?.hide();
}

async function onSave() {
  if (props.step === "已完成") {
    loading.value = true;
    try {
      await completeFlow(props.rfid);
      emit("saved");
      hide();
    } catch {
      /* axios 拦截器已提示 */
    } finally {
      loading.value = false;
    }
    return;
  }
  const errMsg = validateCurrentStep();
  if (errMsg) {
    showToast(errMsg, "warning");
    return;
  }
  const f = form.value;
  let payload = {};
  if (props.step === "种植") {
    payload = {
      daily_water: f.daily_water,
      light_hour: f.light_hour,
      temp: f.temp,
      soil_humidity: f.soil_humidity,
      fertilizer: f.fertilizer,
      pesticide: f.pesticide,
      manager: f.manager,
      harvest_time: f.harvest_time,
      operate_time: f.operate_time,
    };
  } else if (props.step === "加工") {
    const fd = new FormData();
    fd.append("workshop", f.workshop ?? "");
    fd.append("clean_method", f.clean_method ?? "");
    fd.append("process_method", f.process_method ?? "");
    fd.append("package_material", f.package_material ?? "");
    fd.append("quality_result", f.quality_result ?? "");
    fd.append("report_img", f.report_img ?? "");
    fd.append("operate_time", f.operate_time ?? "");
    fd.append("process_end_time", f.process_end_time ?? "");
    if (pendingReportFile.value) fd.append("report_file", pendingReportFile.value);
    loading.value = true;
    try {
      await saveStepFormData(props.rfid, "加工", fd);
      emit("saved");
      hide();
    } catch {
      /* axios 拦截器已提示 */
    } finally {
      loading.value = false;
    }
    return;
  } else if (props.step === "仓储") {
    payload = {
      warehouse_addr: f.warehouse_addr,
      storage_temp: f.storage_temp,
      storage_humidity: f.storage_humidity,
      shelf_life: f.shelf_life,
      storekeeper: f.storekeeper,
      out_time: f.out_time,
      operate_time: f.operate_time,
    };
  } else if (props.step === "运输") {
    const fd = new FormData();
    fd.append("transport_company", f.transport_company ?? "");
    fd.append("waybill_no", f.waybill_no ?? "");
    fd.append(
      "transport_temp",
      f.transport_temp === null || f.transport_temp === undefined || f.transport_temp === ""
        ? ""
        : String(f.transport_temp)
    );
    fd.append("receiver", f.receiver ?? "");
    fd.append("track_img", f.track_img ?? "");
    fd.append("operate_time", f.operate_time ?? "");
    fd.append("arrive_time", f.arrive_time ?? "");
    if (pendingTrackFile.value) fd.append("track_file", pendingTrackFile.value);
    loading.value = true;
    try {
      await saveStepFormData(props.rfid, "运输", fd);
      emit("saved");
      hide();
    } catch {
      /* axios 拦截器已提示 */
    } finally {
      loading.value = false;
    }
    return;
  } else if (props.step === "销售") {
    const fd = new FormData();
    fd.append("store_name", f.store_name ?? "");
    fd.append(
      "price",
      f.price === null || f.price === undefined || f.price === "" ? "" : String(f.price)
    );
    fd.append("seller", f.seller ?? "");
    fd.append("sale_end_date", f.sale_end_date ?? "");
    fd.append("voucher_img", f.voucher_img ?? "");
    fd.append("operate_time", f.operate_time ?? "");
    fd.append("listing_time", f.operate_time ?? "");
    if (pendingVoucherFile.value) fd.append("voucher_file", pendingVoucherFile.value);
    loading.value = true;
    try {
      await saveStepFormData(props.rfid, "销售", fd);
      emit("saved");
      hide();
    } catch {
      /* axios 拦截器已提示 */
    } finally {
      loading.value = false;
    }
    return;
  }
  loading.value = true;
  try {
    await saveStep(props.rfid, props.step, payload);
    emit("saved");
    hide();
  } catch {
    /* axios 拦截器已提示 */
  } finally {
    loading.value = false;
  }
}

async function onSkipStep() {
  if (!canSkip.value) return;
  const msg = "确定要跳过此环节吗？跳过后将无法再填写该环节数据。";
  if (!confirm(msg)) return;
  loading.value = true;
  try {
    await skipStep(props.rfid, props.step);
    emit("saved");
    hide();
  } catch {
    /* axios 拦截器已提示 */
  } finally {
    loading.value = false;
  }
}

defineExpose({ show, hide });
</script>
