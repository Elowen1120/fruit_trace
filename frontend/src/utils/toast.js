/** 全局 Toast：由 FtToastHost 监听并展示（成功 / 错误 / 警告） */
export const FT_TOAST_EVENT = "ft-toast";

/**
 * @param {string} message
 * @param {"success" | "error" | "warning"} [type]
 */
export function showToast(message, type = "error") {
  if (typeof window === "undefined") return;
  const text = String(message ?? "").trim() || (type === "success" ? "操作成功" : "提示");
  window.dispatchEvent(
    new CustomEvent(FT_TOAST_EVENT, {
      detail: { message: text, type },
    })
  );
}
