<template>
  <div
    class="modal fade"
    tabindex="-1"
    ref="modalRef"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-lg">
      <div class="modal-content ft-modal-anim">
        <div class="modal-header">
          <h5 class="modal-title">发表评价</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label mb-2">评分</label>
            <div class="d-flex align-items-center flex-wrap gap-0" role="group" aria-label="评分 1 至 5 星">
              <button
                v-for="n in 5"
                :key="n"
                type="button"
                class="btn btn-link px-1 py-0 text-decoration-none comment-star-btn"
                :aria-pressed="n <= score"
                @click="score = n"
              >
                <span class="fs-2 lh-1" :class="n <= score ? 'text-warning' : 'text-secondary'">★</span>
              </button>
              <span class="small text-muted ms-1">{{ score }} 星</span>
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label">评价内容（必填）</label>
            <textarea
              v-model="content"
              class="form-control"
              rows="4"
              placeholder="请输入评价内容"
            ></textarea>
          </div>
          <div class="mb-0">
            <Base64MediaInput
              v-model="filePayload"
              label="图片 / 视频（可选）"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
          <button
            type="button"
            class="btn btn-ft-primary"
            :disabled="submitting"
            @click="submit"
          >
            {{ submitting ? "提交中…" : "提交" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Modal } from "bootstrap";
import { nextTick, onMounted, ref, watch } from "vue";
import { postComment } from "../api.js";
import { showToast } from "../utils/toast.js";
import Base64MediaInput from "./Base64MediaInput.vue";

const props = defineProps({
  rfid: { type: String, required: true },
});

const emit = defineEmits(["submitted"]);

const modalRef = ref(null);
const submitting = ref(false);
const score = ref(5);
const content = ref("");
const filePayload = ref([]);
let modal = null;

onMounted(async () => {
  await nextTick();
  if (modalRef.value) {
    modal = new Modal(modalRef.value);
  }
});

watch(
  () => props.rfid,
  () => {
    resetForm();
  }
);

function resetForm() {
  score.value = 5;
  content.value = "";
  filePayload.value = [];
}

function show() {
  resetForm();
  modal?.show();
}

async function submit() {
  if (!content.value.trim()) {
    showToast("请填写评价内容", "warning");
    return;
  }
  submitting.value = true;
  try {
    const body = {
      rfid_id: props.rfid,
      content: content.value.trim(),
      score: score.value,
    };
    if (filePayload.value.length) {
      body.media = JSON.stringify(filePayload.value);
    }
    const data = await postComment(body);
    if (!data?.ok) {
      showToast(data?.error || "提交失败", "error");
      return;
    }
    modal?.hide();
    showToast("评价已提交", "success");
    emit("submitted");
  } catch (e) {
    showToast(e.response?.data?.error || "提交失败", "error");
  } finally {
    submitting.value = false;
  }
}

defineExpose({ show });
</script>

<style scoped>
.ft-modal-anim {
  animation: ftModalIn 0.35s ease;
}
@keyframes ftModalIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.comment-star-btn:focus {
  box-shadow: none;
}
</style>
