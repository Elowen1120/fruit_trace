<template>
  <div>
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-danger" role="status"></div>
      <p class="mt-2 text-muted small">加载中…</p>
    </div>
    <div v-else-if="forbidden" class="alert alert-warning">请先登录管理端。</div>
    <div v-else>
      <div class="d-flex flex-wrap gap-2 justify-content-between align-items-center mb-3">
        <h1 class="h4 mb-0">产品管理</h1>
        <button class="btn btn-ft-primary btn-sm ft-btn-press" type="button" @click="openAdd">
          新增产品
        </button>
      </div>

      <div class="table-responsive ft-card p-2 d-none d-md-block">
        <table class="table table-sm align-middle mb-0 ft-table">
          <thead>
            <tr>
              <th>产品编号</th>
              <th>RFID编码</th>
              <th>名称</th>
              <th>产地</th>
              <th style="min-width: 420px">环节操作</th>
              <th style="min-width: 200px">产品</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.product.product_id">
              <td>{{ row.product.product_id }}</td>
              <td><code>{{ row.product.rfid_id }}</code></td>
              <td>{{ row.product.product_name }}</td>
              <td class="small">{{ row.product.product_address }}</td>
              <td>
                <div class="d-flex flex-wrap gap-1">
                  <button
                    v-for="s in stepKeys"
                    :key="s"
                    type="button"
                    class="btn btn-sm ft-btn-press"
                    :class="btnClass(row.steps[s])"
                    @click="openStep(row, s)"
                  >
                    {{ s }}
                  </button>
                </div>
              </td>
              <td>
                <button
                  type="button"
                  class="btn btn-sm btn-primary me-1 ft-btn-press"
                  @click="openQr(row.product)"
                >
                  二维码
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-info me-1 ft-btn-press"
                  @click="openReviews(row.product)"
                >
                  查看评价
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary me-1 ft-btn-press"
                  @click="openEdit(row.product)"
                >
                  编辑
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger ft-btn-press"
                  :disabled="deletingId === row.product.product_id"
                  @click="remove(row.product)"
                >
                  {{ deletingId === row.product.product_id ? "删除中…" : "删除" }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="d-md-none product-mobile-list">
        <div
          v-for="row in items"
          :key="'m-' + row.product.product_id"
          class="ft-card p-3 mb-3"
        >
          <div class="fw-semibold text-danger">{{ row.product.product_name }}</div>
          <div class="small text-muted mt-1">编号 {{ row.product.product_id }}</div>
          <div class="small mt-1">
            RFID <code>{{ row.product.rfid_id }}</code>
          </div>
          <div class="small mt-2">产地：{{ row.product.product_address || "—" }}</div>
          <div class="mt-3 pt-2 border-top">
            <div class="small text-muted mb-2">环节操作</div>
            <div class="d-flex flex-wrap gap-1">
              <button
                v-for="s in stepKeys"
                :key="s"
                type="button"
                class="btn btn-sm ft-btn-press"
                :class="btnClass(row.steps[s])"
                @click="openStep(row, s)"
              >
                {{ s }}
              </button>
            </div>
          </div>
          <div class="d-flex flex-wrap gap-2 mt-3 pt-2 border-top">
            <button
              type="button"
              class="btn btn-sm btn-primary ft-btn-press"
              @click="openQr(row.product)"
            >
              二维码
            </button>
            <button
              type="button"
              class="btn btn-sm btn-outline-info ft-btn-press"
              @click="openReviews(row.product)"
            >
              查看评价
            </button>
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary ft-btn-press"
              @click="openEdit(row.product)"
            >
              编辑
            </button>
            <button
              type="button"
              class="btn btn-sm btn-outline-danger ft-btn-press"
              :disabled="deletingId === row.product.product_id"
              @click="remove(row.product)"
            >
              {{ deletingId === row.product.product_id ? "删除中…" : "删除" }}
            </button>
          </div>
        </div>
      </div>

      <StepModal
        ref="stepModalRef"
        :modal-id="'stepModal'"
        :rfid="modalRfid"
        :step="modalStep"
        :status="modalStatus"
        @saved="refresh"
      />

      <div
        class="modal fade"
        id="productModal"
        tabindex="-1"
        ref="productModalRef"
        aria-hidden="true"
      >
        <div class="modal-dialog">
          <div class="modal-content ft-modal-anim">
            <div class="modal-header">
              <h5 class="modal-title">{{ productForm.id ? "编辑产品" : "新增产品" }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div v-if="!productForm.id" class="alert alert-light border small mb-3 text-start">
                系统将自动分配<strong>产品编号</strong>（P###）与 <strong>RFID 编码</strong>（RFID###，与编号后三位一致）。
              </div>
              <div class="mb-2" v-if="productForm.id">
                <label class="form-label text-muted small">产品编号（只读）</label>
                <input class="form-control" :value="productForm.product_id" disabled />
              </div>
              <div class="mb-2" v-if="productForm.id">
                <label class="form-label text-muted small">RFID 编码（只读）</label>
                <input class="form-control" :value="productForm.rfid_id" disabled />
              </div>
              <div class="mb-2">
                <label class="form-label">名称 <span class="text-danger">*</span></label>
                <input class="form-control" v-model="productForm.product_name" />
              </div>
              <div class="mb-2">
                <label class="form-label">产地 <span class="text-danger">*</span></label>
                <input class="form-control" v-model="productForm.product_address" />
              </div>
              <div class="mb-2">
                <label class="form-label">种植开始日期 <span class="text-danger">*</span></label>
                <input type="date" class="form-control" v-model="productForm.plant_time" />
              </div>
              <div class="mb-2">
                <label class="form-label">抽检结果 <span class="text-danger">*</span></label>
                <select class="form-select" v-model="productForm.check_result">
                  <option v-for="o in checkResultOptions" :key="o" :value="o">{{ o }}</option>
                </select>
              </div>
              <div class="mb-2">
                <label class="form-label">地块 <span class="text-danger">*</span></label>
                <input class="form-control" v-model="productForm.plot_no" />
              </div>
              <div class="mb-2">
                <label class="form-label">品种 <span class="text-danger">*</span></label>
                <input class="form-control" v-model="productForm.variety" />
              </div>
              <div class="mb-2">
                <label class="form-label">果蔬大类</label>
                <select class="form-select" v-model="productForm.category">
                  <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
              <button
                type="button"
                class="btn btn-ft-primary"
                :disabled="saveProductLoading"
                @click="saveProduct"
              >
                {{ saveProductLoading ? "保存中…" : "保存" }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 二维码 -->
      <div class="modal fade" id="qrProductModal" tabindex="-1" ref="qrModalRef" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content ft-modal-anim">
            <div class="modal-header">
              <h5 class="modal-title">溯源二维码</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
              <p class="small text-muted mb-2">{{ qrUrl }}</p>
              <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR" class="img-fluid mb-3" style="max-width: 260px" />
              <div>
                <button type="button" class="btn btn-primary ft-btn-press" @click="downloadQr">
                  下载二维码
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 评分分布 -->
      <div class="modal fade" id="reviewDistModal" tabindex="-1" ref="reviewModalRef" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
          <div class="modal-content ft-modal-anim">
            <div class="modal-header">
              <h5 class="modal-title">评分分布 · {{ reviewProduct?.product_name }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div ref="reviewChartRef" style="height: 320px; width: 100%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from "vue";
import * as echarts from "echarts";
import QRCode from "qrcode";
import { Modal } from "bootstrap";
import {
  addProduct,
  deleteProduct,
  editProduct,
  getCommentScores,
  getProductStepMeta,
} from "../api.js";
import StepModal from "../components/StepModal.vue";
import { PRODUCT_CATEGORY_OPTIONS } from "../utils/freshnessCategoryStandards.js";
import { showToast } from "../utils/toast.js";

const loading = ref(true);
const forbidden = ref(false);
const saveProductLoading = ref(false);
const deletingId = ref(null);
const items = ref([]);
const stepModalRef = ref(null);
const productModalRef = ref(null);
const qrModalRef = ref(null);
const reviewModalRef = ref(null);
const reviewChartRef = ref(null);
let productModal = null;
let qrModal = null;
let reviewModal = null;
let reviewChart = null;

const modalRfid = ref("");
const modalStep = ref("");
const modalStatus = ref("");

const stepKeys = ["种植", "加工", "仓储", "运输", "销售", "已完成"];

const categoryOptions = PRODUCT_CATEGORY_OPTIONS;
const checkResultOptions = ["合格", "不合格"];

function normalizeCheckResult(v) {
  const s = String(v || "").trim();
  return s === "合格" || s === "不合格" ? s : "合格";
}

function todayLocalDate() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

const productForm = ref({
  id: null,
  product_id: "",
  rfid_id: "",
  product_name: "",
  product_address: "",
  plant_time: "",
  check_result: "合格",
  plot_no: "",
  variety: "",
  category: "其他",
});

const qrUrl = ref("");
const qrDataUrl = ref("");
const qrForRfid = ref("");
const reviewProduct = ref(null);

function btnClass(st) {
  if (st === "active") return "ft-step-active";
  if (st === "completed") return "ft-step-completed";
  return "ft-step-neutral";
}

async function refresh() {
  const data = await getProductStepMeta();
  items.value = data.items || [];
}

onMounted(async () => {
  try {
    await refresh();
  } catch {
    forbidden.value = true;
  } finally {
    loading.value = false;
  }
  await nextTick();
  if (!forbidden.value && productModalRef.value) {
    productModal = new Modal(productModalRef.value);
  }
  if (qrModalRef.value) qrModal = new Modal(qrModalRef.value);
  if (reviewModalRef.value) reviewModal = new Modal(reviewModalRef.value);
});

onUnmounted(() => {
  reviewChart?.dispose();
});

function openStep(row, step) {
  const st = row.steps[step];
  if (st === "later") {
    showToast("请先完成前面的环节", "warning");
    return;
  }
  if (st === "skipped") {
    showToast("该环节已跳过，无法再填写该环节数据。", "warning");
    return;
  }
  modalRfid.value = row.product.rfid_id;
  modalStep.value = step;
  modalStatus.value = st;
  stepModalRef.value?.show();
}

function openAdd() {
  productForm.value = {
    id: null,
    product_id: "",
    rfid_id: "",
    product_name: "",
    product_address: "",
    plant_time: todayLocalDate(),
    check_result: "合格",
    plot_no: "",
    variety: "",
    category: "其他",
  };
  nextTick(() => productModal?.show());
}

function openEdit(p) {
  productForm.value = {
    id: p.product_id,
    product_id: p.product_id,
    rfid_id: p.rfid_id,
    product_name: p.product_name,
    product_address: p.product_address || "",
    plant_time: (p.plant_time || "").slice(0, 10),
    check_result: normalizeCheckResult(p.check_result),
    plot_no: p.plot_no || "",
    variety: p.variety || "",
    category: p.category || "其他",
  };
  productModal?.show();
}

function validateProductForm(f) {
  const name = (f.product_name || "").trim();
  const addr = (f.product_address || "").trim();
  const check = (f.check_result || "").trim();
  const plot = (f.plot_no || "").trim();
  const variety = (f.variety || "").trim();
  const pt = (f.plant_time || "").trim();
  if (!name || !addr || !check || !plot || !variety || !pt) {
    showToast("请填写所有必填项", "warning");
    return false;
  }
  return true;
}

async function saveProduct() {
  const f = productForm.value;
  if (!validateProductForm(f)) return;
  saveProductLoading.value = true;
  try {
    if (!f.id) {
      await addProduct({
        product_name: f.product_name.trim(),
        product_address: f.product_address.trim(),
        plant_time: f.plant_time,
        check_result: f.check_result.trim(),
        plot_no: f.plot_no.trim(),
        variety: f.variety.trim(),
        category: f.category || "其他",
      });
    } else {
      await editProduct(f.id, {
        product_name: f.product_name.trim(),
        product_address: f.product_address.trim(),
        plant_time: f.plant_time,
        check_result: f.check_result.trim(),
        plot_no: f.plot_no.trim(),
        variety: f.variety.trim(),
        category: f.category || "其他",
      });
    }
    productModal?.hide();
    await refresh();
  } catch {
    /* 拦截器已提示 */
  } finally {
    saveProductLoading.value = false;
  }
}

async function remove(p) {
  if (!confirm(`确定删除产品 ${p.product_id}？将同时删除所有关联溯源与评论数据。`)) return;
  deletingId.value = p.product_id;
  try {
    await deleteProduct(p.product_id);
    await refresh();
  } catch {
    /* 拦截器 */
  } finally {
    deletingId.value = null;
  }
}

async function openQr(p) {
  qrForRfid.value = p.rfid_id;
  const url = `${window.location.origin}/trace?rfid=${encodeURIComponent(p.rfid_id)}`;
  qrUrl.value = url;
  qrDataUrl.value = await QRCode.toDataURL(url, {
    width: 280,
    margin: 2,
    color: { dark: "#4a2c2f" },
  });
  qrModal?.show();
}

function downloadQr() {
  if (!qrDataUrl.value) return;
  const a = document.createElement("a");
  a.href = qrDataUrl.value;
  a.download = `trace-${qrForRfid.value || "qr"}.png`;
  a.click();
}

async function openReviews(p) {
  reviewProduct.value = p;
  reviewModal?.show();
  await nextTick();
  try {
    const { distribution } = await getCommentScores(p.rfid_id);
    await nextTick();
    if (!reviewChartRef.value) return;
    if (reviewChart) {
      reviewChart.dispose();
      reviewChart = null;
    }
    reviewChart = echarts.init(reviewChartRef.value);
    const keys = [1, 2, 3, 4, 5];
    reviewChart.setOption({
      color: ["#e89aa5"],
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: keys.map((k) => `${k} 星`) },
      yAxis: { type: "value", minInterval: 1 },
      series: [{ type: "bar", data: keys.map((k) => distribution[k] || 0) }],
      grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    });
    setTimeout(() => reviewChart?.resize(), 200);
  } catch {
    /* 拦截器 */
  }
}
</script>
