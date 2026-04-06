<template>
  <div>
    <div class="d-flex flex-wrap gap-2 justify-content-between align-items-center mb-3">
      <h1 class="h4 mb-0">投诉管理</h1>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-danger" role="status"></div>
      <p class="mt-2 text-muted small">加载中…</p>
    </div>
    <div v-else class="table-responsive ft-card p-2">
      <table class="table table-sm align-middle mb-0">
        <thead>
          <tr>
            <th>ID</th>
            <th>RFID</th>
            <th>投诉人</th>
            <th>类型</th>
            <th>内容</th>
            <th>联系方式</th>
            <th style="min-width: 180px">附件</th>
            <th>状态</th>
            <th>时间</th>
            <th style="min-width: 140px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in items"
            :key="c.id"
            :class="{ 'table-danger-subtle': c.status === '待处理' }"
          >
            <td>{{ c.id }}</td>
            <td><code>{{ c.rfid_id }}</code></td>
            <td>{{ c.user_username || "—" }}</td>
            <td>{{ c.complaint_type }}</td>
            <td class="small" style="max-width: 220px">{{ c.content }}</td>
            <td class="small">{{ c.contact || "—" }}</td>
            <td class="small">
              <template v-if="mediaList(c.media).length">
                <div class="d-flex flex-wrap gap-1 complaint-media">
                  <template v-for="(m, idx) in mediaList(c.media)" :key="idx">
                    <img
                      v-if="m && m.startsWith('data:image')"
                      :src="m"
                      alt=""
                      class="rounded border complaint-thumb"
                    />
                    <video
                      v-else-if="m && m.startsWith('data:video')"
                      :src="m"
                      controls
                      class="rounded border complaint-video"
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
            <td>{{ c.status }}</td>
            <td class="small text-nowrap">{{ formatIsoTimeForDisplay(c.create_time) }}</td>
            <td>
              <button
                type="button"
                class="btn btn-sm btn-outline-primary me-1"
                :disabled="c.status === '已处理' || processingId === c.id"
                @click="markDone(c)"
              >
                {{ processingId === c.id ? "处理中…" : "标记已处理" }}
              </button>
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
      <div v-if="!items.length" class="text-center text-muted py-4">暂无投诉</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { getComplaints, processComplaint, deleteComplaint } from "../api.js";
import { formatIsoTimeForDisplay } from "../utils/formatTime.js";
import { mediaList } from "../utils/mediaList.js";
import { showToast } from "../utils/toast.js";

const loading = ref(true);
const items = ref([]);
const processingId = ref(null);
const deletingId = ref(null);

async function refresh() {
  const data = await getComplaints();
  items.value = data.items || [];
}

onMounted(async () => {
  try {
    await refresh();
  } finally {
    loading.value = false;
  }
});

async function markDone(c) {
  processingId.value = c.id;
  try {
    await processComplaint(c.id);
    await refresh();
  } catch (e) {
    showToast(e.response?.data?.error || "操作失败", "error");
  } finally {
    processingId.value = null;
  }
}

async function remove(c) {
  if (!confirm("确定删除该投诉？")) return;
  deletingId.value = c.id;
  try {
    await deleteComplaint(c.id);
    await refresh();
  } catch (e) {
    showToast(e.response?.data?.error || "删除失败", "error");
  } finally {
    deletingId.value = null;
  }
}
</script>

<style scoped>
.table-danger-subtle {
  background-color: #ffecec !important;
}
.complaint-thumb {
  max-width: 72px;
  max-height: 54px;
  object-fit: cover;
}
.complaint-video {
  max-width: 140px;
  max-height: 90px;
}
</style>
