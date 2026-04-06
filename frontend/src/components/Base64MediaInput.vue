<template>
  <div>
    <label v-if="label" class="form-label">{{ label }}</label>
    <input
      ref="inputRef"
      type="file"
      class="form-control"
      :multiple="multiple"
      :accept="acceptAttr"
      @change="onChange"
    />
    <div v-if="hint" class="small text-muted mt-1">{{ hint }}</div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { showToast } from "../utils/toast.js";

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  /** 投诉：仅 JPG/PNG/MP4；评价：任意图片/视频 */
  onlyJpgPngMp4: { type: Boolean, default: false },
  /** null 表示不限制 */
  imageMaxMB: { type: Number, default: null },
  videoMaxMB: { type: Number, default: null },
  multiple: { type: Boolean, default: true },
  label: { type: String, default: "" },
  hint: { type: String, default: "" },
});

const emit = defineEmits(["update:modelValue"]);

const inputRef = ref(null);

const acceptAttr = computed(() =>
  props.onlyJpgPngMp4
    ? ".jpg,.jpeg,.png,.mp4,image/jpeg,image/png,video/mp4"
    : "image/*,video/*"
);

function fileKind(file) {
  const t = (file.type || "").toLowerCase();
  const name = (file.name || "").toLowerCase();
  if (props.onlyJpgPngMp4) {
    if (
      t === "image/jpeg" ||
      t === "image/jpg" ||
      name.endsWith(".jpg") ||
      name.endsWith(".jpeg")
    ) {
      return "image";
    }
    if (t === "image/png" || name.endsWith(".png")) return "image";
    if (t === "video/mp4" || name.endsWith(".mp4")) return "video";
    return null;
  }
  if (t.startsWith("image/")) return "image";
  if (t.startsWith("video/")) return "video";
  return null;
}

function maxBytes(kind) {
  if (kind === "image" && props.imageMaxMB != null) {
    return props.imageMaxMB * 1024 * 1024;
  }
  if (kind === "video" && props.videoMaxMB != null) {
    return props.videoMaxMB * 1024 * 1024;
  }
  return Number.POSITIVE_INFINITY;
}

function onChange(e) {
  const files = Array.from(e.target.files || []);
  if (inputRef.value) inputRef.value.value = "";
  if (!files.length) {
    emit("update:modelValue", []);
    return;
  }
  for (const file of files) {
    const kind = fileKind(file);
    if (!kind) {
      showToast(
        props.onlyJpgPngMp4
          ? "仅支持 JPG、PNG 图片或 MP4 视频"
          : "请选择图片或视频文件",
        "warning"
      );
      return;
    }
    const max = maxBytes(kind);
    if (file.size > max) {
      showToast(
        kind === "image"
          ? `单张图片不能超过 ${props.imageMaxMB}MB`
          : `单个视频不能超过 ${props.videoMaxMB}MB`,
        "warning"
      );
      return;
    }
  }
  const readers = files.map(
    (file) =>
      new Promise((resolve, reject) => {
        const r = new FileReader();
        r.onload = () => resolve(r.result);
        r.onerror = () => reject(new Error("read"));
        r.readAsDataURL(file);
      })
  );
  Promise.all(readers)
    .then((urls) => emit("update:modelValue", urls))
    .catch(() => showToast("文件读取失败，请重试", "error"));
}
</script>
