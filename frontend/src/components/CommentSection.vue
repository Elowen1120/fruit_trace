<template>
  <section class="mt-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
      <h5 class="mb-0">用户评价</h5>
      <div class="d-flex flex-wrap align-items-center gap-2">
        <button
          type="button"
          class="btn btn-sm btn-outline-primary ft-btn-press"
          @click="onClickComment"
        >
          评价
        </button>
        <button
          v-if="showComplaint"
          type="button"
          class="btn btn-sm btn-outline-danger ft-btn-press"
          @click="$emit('open-complaint')"
        >
          投诉该产品
        </button>
      </div>
    </div>

    <div v-if="!comments.length" class="text-muted">暂无评论</div>
    <div v-else class="vstack gap-3">
      <div v-for="c in comments" :key="c.id" class="ft-card p-3">
        <div class="d-flex justify-content-between flex-wrap gap-2">
          <strong>{{ c.username }}</strong>
          <span class="text-warning">★ {{ c.score }}</span>
        </div>
        <p class="mb-2 mt-2">{{ c.content }}</p>
        <div v-if="c.media && c.media.length" class="d-flex flex-wrap gap-2">
          <template v-for="(m, idx) in mediaList(c.media)" :key="idx">
            <img
              v-if="m && m.startsWith('data:image')"
              :src="m"
              alt=""
              class="rounded border"
              style="max-width: 160px; max-height: 120px; object-fit: cover"
            />
            <video
              v-else-if="m && m.startsWith('data:video')"
              :src="m"
              controls
              class="rounded border"
              style="max-width: 220px"
            />
            <a v-else-if="m && m.startsWith('http')" :href="m" target="_blank" rel="noopener"
              >附件</a
            >
          </template>
        </div>
        <div class="d-flex justify-content-between align-items-end gap-2 mt-2">
          <div class="small text-muted">{{ formatIsoTimeForDisplay(c.create_time) }}</div>
          <button
            v-if="canDeleteOwn(c)"
            type="button"
            class="comment-delete-btn small text-muted"
            @click="confirmDelete(c)"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { deleteMyComment } from "../api.js";
import { currentUser as currentUserRef } from "../auth/user.js";
import { formatIsoTimeForDisplay } from "../utils/formatTime.js";
import { mediaList } from "../utils/mediaList.js";
import { showToast } from "../utils/toast.js";
const props = defineProps({
  rfid: { type: String, required: true },
  comments: { type: Array, default: () => [] },
  showComplaint: { type: Boolean, default: false },
});

const emit = defineEmits(["submitted", "open-complaint", "need-login", "open-comment"]);

const currentUser = computed(() => currentUserRef.value);

function onClickComment() {
  if (!currentUser.value) {
    emit("need-login");
    return;
  }
  emit("open-comment");
}

function canDeleteOwn(c) {
  const u = currentUser.value;
  if (!u || c.user_id == null || c.user_id === "") return false;
  return Number(c.user_id) === Number(u.id);
}

async function confirmDelete(c) {
  if (!confirm("确定删除这条评价吗？")) return;
  try {
    const data = await deleteMyComment(c.id);
    if (!data?.ok) {
      showToast(data?.error || "删除失败", "error");
      return;
    }
    emit("submitted");
  } catch (e) {
    showToast(e.response?.data?.error || "删除失败", "error");
  }
}
</script>

<style scoped>
.comment-delete-btn {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  box-shadow: none;
  line-height: inherit;
  flex-shrink: 0;
}
.comment-delete-btn:hover {
  text-decoration: underline;
  color: #6c757d !important;
}
</style>
