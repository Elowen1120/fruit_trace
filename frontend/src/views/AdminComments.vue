<template>
  <div>
    <div class="d-flex flex-wrap gap-2 justify-content-between align-items-center mb-3">
      <h1 class="h4 mb-0">评价管理</h1>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-danger" role="status"></div>
      <p class="mt-2 text-muted small">加载中…</p>
    </div>
    <div v-else class="table-responsive ft-card p-2">
      <table class="table table-sm align-middle mb-0">
        <thead>
          <tr>
            <th>评价人</th>
            <th>产品信息</th>
            <th>评分</th>
            <th>内容</th>
            <th style="min-width: 160px">附件</th>
            <th>评价时间</th>
            <th style="min-width: 88px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in items" :key="c.id">
            <td>{{ c.username || "—" }}</td>
            <td class="small" style="min-width: 140px">
              <div>{{ c.product_name || "—" }}</div>
              <div class="text-muted"><code>{{ c.product_id || c.rfid_id || "—" }}</code></div>
            </td>
            <td>{{ c.score }}</td>
            <td class="small" style="max-width: 260px">{{ c.content }}</td>
            <td class="small">
              <template v-if="mediaList(c.media).length">
                <div class="d-flex flex-wrap gap-1">
                  <template v-for="(m, idx) in mediaList(c.media)" :key="idx">
                    <img
                      v-if="m && m.startsWith('data:image')"
                      :src="m"
                      alt=""
                      class="rounded border admin-comment-thumb"
                    />
                    <video
                      v-else-if="m && m.startsWith('data:video')"
                      :src="m"
                      controls
                      class="rounded border admin-comment-video"
                    />
                    <a
                      v-else-if="m && m.startsWith('http')"
                      :href="m"
                      target="_blank"
                      rel="noopener"
                    >链接</a>
                  </template>
                </div>
              </template>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="small text-nowrap">{{ formatIsoTimeForDisplay(c.create_time) }}</td>
            <td>
              <button
                type="button"
                class="btn btn-sm btn-outline-danger"
                :disabled="deletingId === c.id"
                @click="remove(c)"
              >
                {{ deletingId === c.id ? "删除中…" : "删除" }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!items.length" class="text-center text-muted py-4">暂无评价</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { deleteAdminComment, getAdminComments } from "../api.js";
import { formatIsoTimeForDisplay } from "../utils/formatTime.js";
import { mediaList } from "../utils/mediaList.js";
import { showToast } from "../utils/toast.js";

const loading = ref(true);
const items = ref([]);
const deletingId = ref(null);

async function refresh() {
  const data = await getAdminComments();
  items.value = data.items || [];
}

onMounted(async () => {
  try {
    await refresh();
  } catch (e) {
    showToast(e.response?.data?.error || "加载失败", "error");
  } finally {
    loading.value = false;
  }
});

async function remove(c) {
  if (!confirm("确定删除该评价？")) return;
  deletingId.value = c.id;
  try {
    const data = await deleteAdminComment(c.id);
    if (!data?.ok) {
      showToast(data?.error || "删除失败", "error");
      return;
    }
    await refresh();
  } catch (e) {
    showToast(e.response?.data?.error || "删除失败", "error");
  } finally {
    deletingId.value = null;
  }
}
</script>

<style scoped>
.admin-comment-thumb {
  max-width: 72px;
  max-height: 54px;
  object-fit: cover;
}
.admin-comment-video {
  max-width: 140px;
  max-height: 90px;
}
</style>
