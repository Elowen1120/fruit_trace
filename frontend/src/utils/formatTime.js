/** 将后端 isoformat 字符串中的 T 换为空格，便于阅读 */
export function formatIsoTimeForDisplay(iso) {
  if (iso == null || typeof iso !== "string") return iso ?? "";
  return iso.replace("T", " ");
}

/**
 * 将 ISO / datetime-local 字符串格式化为 YYYY-MM-DD HH:MM（分钟精度）。
 * 空值或无法解析时返回空字符串。
 */
export function formatOperateTimeMinute(iso) {
  if (iso == null || iso === "") return "";
  const s = String(iso).trim();
  if (!s) return "";
  const noMs = s.includes(".") ? s.split(".")[0] : s;
  const normalized = noMs.replace(" ", "T");
  const d = new Date(normalized);
  if (!Number.isNaN(d.getTime())) {
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
  if (s.includes("T")) {
    return s.replace("T", " ").slice(0, 16);
  }
  return s.slice(0, 16);
}
