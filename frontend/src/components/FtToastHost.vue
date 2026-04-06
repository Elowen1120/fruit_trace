<template>
  <div
    class="ft-toast-host position-fixed bottom-0 end-0 p-3"
    style="z-index: 1090; max-width: min(100vw, 360px); pointer-events: none"
    aria-live="polite"
  >
    <TransitionGroup name="ft-toast" tag="div" class="d-flex flex-column gap-2 align-items-end">
      <div
        v-for="t in items"
        :key="t.id"
        class="ft-toast-item shadow border-0 rounded-3 px-3 py-2 small fw-medium"
        :class="toastClass(t.type)"
        style="pointer-events: auto"
        role="status"
      >
        {{ t.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { FT_TOAST_EVENT } from "../utils/toast.js";

const AUTO_MS = 2600;
const items = ref([]);
let seq = 0;

function toastClass(type) {
  if (type === "success") return "text-white bg-success";
  if (type === "warning") return "text-dark bg-warning";
  return "text-white bg-danger";
}

function push(detail) {
  const message = detail?.message ?? "";
  const type = ["success", "error", "warning"].includes(detail?.type)
    ? detail.type
    : "error";
  const id = ++seq;
  items.value = [...items.value, { id, message, type }];
  window.setTimeout(() => {
    items.value = items.value.filter((x) => x.id !== id);
  }, AUTO_MS);
}

function onToast(ev) {
  if (ev?.detail) push(ev.detail);
}

onMounted(() => {
  window.addEventListener(FT_TOAST_EVENT, onToast);
});
onUnmounted(() => {
  window.removeEventListener(FT_TOAST_EVENT, onToast);
});
</script>

<style scoped>
.ft-toast-enter-active,
.ft-toast-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}
.ft-toast-enter-from,
.ft-toast-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
.ft-toast-move {
  transition: transform 0.2s ease;
}
</style>
