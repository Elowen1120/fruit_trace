/** 后端 Flask 根地址（端口 5000），API 为 `${API_ROOT}/api` */
export const API_ROOT =
  import.meta.env.VITE_API_ROOT || "http://localhost:5000";

export const API_BASE = `${API_ROOT}/api`;

/** 将相对上传路径转为可跨域访问的绝对地址 */
export function resolveUploadUrl(path) {
  if (!path || typeof path !== "string") return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  if (path.startsWith("/uploads")) return `${API_ROOT}${path}`;
  return path;
}
