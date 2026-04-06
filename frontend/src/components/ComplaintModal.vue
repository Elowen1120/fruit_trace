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
          <h5 class="modal-title">投诉该产品</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="mb-2">
            <label class="form-label">问题类型</label>
            <select v-model="form.complaint_type" class="form-select">
              <option value="变质">变质</option>
              <option value="包装破损">包装破损</option>
              <option value="疑似假货">疑似假货</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="mb-2">
            <label class="form-label">投诉内容（必填）</label>
            <textarea v-model="form.content" class="form-control" rows="4"></textarea>
          </div>
          <div class="mb-2">
            <label class="form-label">联系方式（可选）</label>
            <input
              v-model="form.contact"
              class="form-control"
              placeholder="手机号码或邮箱"
              maxlength="100"
            />
          </div>
          <div class="mb-0">
            <Base64MediaInput
              v-model="filePayload"
              only-jpg-png-mp4
              :image-max-m-b="5"
              :video-max-m-b="20"
              label="图片 / 视频（可选）"
              hint="支持 JPG、PNG、MP4；图片单文件 ≤ 5MB，视频单文件 ≤ 20MB。"
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
import { postComplaint } from "../api.js";
import { showToast } from "../utils/toast.js";
import { validateComplaintContact } from "../utils/complaintContact.js";
import Base64MediaInput from "./Base64MediaInput.vue";

const props = defineProps({
  /** 须为 product_info.rfid_id（如 RFID002），与路由上的 P002 无关 */
  rfid: { type: String, required: true },
});

const emit = defineEmits(["submitted"]);

const modalRef = ref(null);
const submitting = ref(false);
const filePayload = ref([]);
let modal = null;

const form = ref({
  complaint_type: "变质",
  content: "",
  contact: "",
});

onMounted(async () => {
  await nextTick();
  if (modalRef.value) {
    modal = new Modal(modalRef.value);
  }
});

watch(
  () => props.rfid,
  () => {
    form.value = { complaint_type: "变质", content: "", contact: "" };
    filePayload.value = [];
  }
);

function resetForm() {
  form.value = { complaint_type: "变质", content: "", contact: "" };
  filePayload.value = [];
}

function show() {
  resetForm();
  modal?.show();
}

async function submit() {
  if (!form.value.content.trim()) {
    showToast("请填写投诉内容", "warning");
    return;
  }
  const contactCheck = validateComplaintContact(form.value.contact);
  if (!contactCheck.ok) {
    showToast("请填写正确的手机号或邮箱", "warning");
    return;
  }
  submitting.value = true;
  try {
    const payload = {
      rfid_id: props.rfid,
      complaint_type: form.value.complaint_type,
      content: form.value.content.trim(),
      contact: contactCheck.value || undefined,
    };
    if (filePayload.value.length) {
      payload.media = JSON.stringify(filePayload.value);
    }
    const data = await postComplaint(payload);
    if (!data?.ok) {
      showToast(data?.error || "提交失败", "error");
      return;
    }
    modal?.hide();
    showToast("投诉已提交，我们会尽快处理", "success");
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
</style>
