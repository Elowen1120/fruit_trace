<template>
  <div
    class="modal fade"
    ref="modalRef"
    tabindex="-1"
    aria-hidden="true"
    aria-labelledby="loginRequiredTitle"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 id="loginRequiredTitle" class="modal-title">提示</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭"></button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ loginPromptText }}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
          <button type="button" class="btn btn-ft-primary" @click="goLogin">去登录</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Modal } from "bootstrap";
import { nextTick, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const DEFAULT_MESSAGE = "请登录后再操作";
const loginPromptText = ref(DEFAULT_MESSAGE);

const router = useRouter();
const modalRef = ref(null);
let modal = null;
let redirectAfterLogin = "/";

onMounted(async () => {
  await nextTick();
  if (modalRef.value) {
    modal = new Modal(modalRef.value);
  }
});

function show(redirect, message) {
  const r = redirect != null ? String(redirect).trim() : "";
  redirectAfterLogin = r || "/";
  loginPromptText.value =
    message != null && String(message).trim() ? String(message).trim() : DEFAULT_MESSAGE;
  modal?.show();
}

function hide() {
  modal?.hide();
}

function goLogin() {
  hide();
  router.push({
    path: "/login",
    query: { redirect: redirectAfterLogin },
  });
}

defineExpose({ show, hide });
</script>
