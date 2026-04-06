import axios from "axios";
import { showToast } from "./utils/toast.js";

const http = axios.create({
  baseURL: "",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.config?.silent) {
      return Promise.reject(err);
    }
    const msg =
      err.response?.data?.error ||
      err.response?.data?.message ||
      (err.message === "Network Error" ? "网络异常，请检查服务是否启动" : null) ||
      `请求失败 (${err.response?.status || "错误"})`;
    if (typeof window !== "undefined" && msg) {
      showToast(msg, "error");
    }
    return Promise.reject(err);
  }
);

export async function getTrace(rfid) {
  const { data } = await http.get("/api/trace", {
    params: { rfid },
    silent: true,
  });
  return data;
}

/**
 * 首页预检：始终解析 HTTP 响应（含 404），避免把「未找到」与「服务异常」混成同一提示。
 * 返回 { ok, data, status }；网络失败时仍抛错。
 */
export async function checkTraceExists(code) {
  const res = await http.get("/api/trace", {
    params: { rfid: code },
    silent: true,
    validateStatus: () => true,
  });
  return {
    ok: Boolean(res.data?.ok),
    data: res.data,
    status: res.status,
  };
}

/** 管理登录：silent 避免与页面内错误提示重复弹全局 alert */
export async function adminLogin(username, password) {
  const { data } = await http.post(
    "/admin/login",
    { username, password },
    { silent: true }
  );
  return data;
}

export async function postComment(body) {
  const { data } = await http.post("/api/comment", body, { silent: true });
  return data;
}

export async function deleteMyComment(id) {
  const { data } = await http.delete(`/api/comment/${id}`, { silent: true });
  return data;
}

export async function deleteAdminComment(id) {
  const { data } = await http.delete(`/api/admin/comment/${id}`, { silent: true });
  return data;
}

export async function postComplaint(body) {
  const { data } = await http.post("/api/complaint", body, { silent: true });
  return data;
}

export async function userRegister(username, password) {
  const { data } = await http.post(
    "/api/auth/register",
    { username, password },
    { silent: true }
  );
  return data;
}

export async function userLogin(username, password) {
  const { data } = await http.post(
    "/api/auth/login",
    { username, password },
    { silent: true }
  );
  return data;
}

export async function userLogout() {
  const { data } = await http.post("/api/auth/logout", {}, { silent: true });
  return data;
}

export async function getAdminComments() {
  const { data } = await http.get("/api/admin/comments", { silent: true });
  return data;
}

export async function getProducts() {
  const { data } = await http.get("/api/products");
  return data;
}

export async function adminLogout() {
  const { data } = await http.post("/admin/logout");
  return data;
}

export async function getDashboardStats() {
  const { data } = await http.get("/api/dashboard/stats", { silent: true });
  return data;
}

export async function getProductStepMeta() {
  const { data } = await http.get("/api/product/step_meta");
  return data;
}

export async function getComplaints() {
  const { data } = await http.get("/api/complaints", { silent: true });
  return data;
}

export async function processComplaint(id) {
  const { data } = await http.post(`/api/complaint/process/${id}`, { silent: true });
  return data;
}

export async function deleteComplaint(id) {
  const { data } = await http.delete(`/api/complaint/${id}`, { silent: true });
  return data;
}

export async function getCommentScores(rfid) {
  const { data } = await http.get(
    `/api/product/comment_scores/${encodeURIComponent(rfid)}`
  );
  return data;
}

export async function addProduct(payload) {
  const { data } = await http.post("/api/product/add", payload);
  return data;
}

export async function editProduct(productId, payload) {
  const { data } = await http.post(`/api/product/edit/${productId}`, payload);
  return data;
}

export async function deleteProduct(productId) {
  const { data } = await http.delete(`/api/product/del/${productId}`);
  return data;
}

export async function getStepData(rfid, step) {
  const { data } = await http.get("/api/get_step_data", {
    params: { rfid, step },
    silent: true,
  });
  return data;
}

export async function saveStep(rfid, step, payload) {
  const map = {
    种植: `/api/planting/${encodeURIComponent(rfid)}`,
    加工: `/api/process/${encodeURIComponent(rfid)}`,
    仓储: `/api/storage/${encodeURIComponent(rfid)}`,
    运输: `/api/transport/${encodeURIComponent(rfid)}`,
    销售: `/api/sales/${encodeURIComponent(rfid)}`,
  };
  const url = map[step];
  if (!url) throw new Error("未知环节");
  const { data } = await http.post(url, payload);
  return data;
}

export async function skipStep(rfid, step) {
  // 管理端跳过：只允许加工/仓储/运输
  const url = `/api/skip/${encodeURIComponent(rfid)}/${encodeURIComponent(step)}`;
  const { data } = await http.post(url, {});
  return data;
}

/** 加工/运输/销售：multipart 上传（勿手动设置 Content-Type，以便带 boundary） */
export async function saveStepFormData(rfid, step, formData) {
  const map = {
    加工: `/api/process/${encodeURIComponent(rfid)}`,
    运输: `/api/transport/${encodeURIComponent(rfid)}`,
    销售: `/api/sales/${encodeURIComponent(rfid)}`,
  };
  const url = map[step];
  if (!url) throw new Error("未知环节");
  const { data } = await http.post(url, formData, {
    transformRequest: [
      (body, headers) => {
        if (body instanceof FormData) {
          delete headers["Content-Type"];
        }
        return body;
      },
    ],
  });
  return data;
}

export async function completeFlow(rfid) {
  const { data } = await http.post(
    `/api/complete/${encodeURIComponent(rfid)}`,
    {}
  );
  return data;
}

export { http };
