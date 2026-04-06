/** 与后端 validate_complaint_contact 一致：空为合法；否则 11 位 1 开头手机号或邮箱 */
export function validateComplaintContact(raw) {
  const s = (raw || "").trim();
  if (!s) return { ok: true, value: "" };
  if (/^1\d{10}$/.test(s)) return { ok: true, value: s };
  if (/^[^@\s]+@[^@\s]+$/.test(s)) return { ok: true, value: s };
  return { ok: false };
}
