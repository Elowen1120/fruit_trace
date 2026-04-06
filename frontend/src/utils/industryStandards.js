/**
 * 行业标准对比（参考《食品安全国家标准》《农产品冷链运输技术规范》等）
 */

export function judgeRange(value, min, max) {
  if (value === null || value === undefined || value === "") return null;
  const v = Number(value);
  if (Number.isNaN(v)) return null;
  if (v > max) return { level: "high", icon: "⚠️", text: "超出标准" };
  if (v < min) return { level: "low", icon: "❌", text: "低于标准" };
  return { level: "ok", icon: "✅", text: "达标" };
}

export function formatWithStandard(label, value, unit, min, max, digits = 0) {
  const j = judgeRange(value, min, max);
  const v =
    value === null || value === undefined || value === ""
      ? "—"
      : digits > 0
        ? Number(value).toFixed(digits)
        : value;
  const std = `标准：${min}-${max}${unit}`;
  if (!j) {
    return `${label}：${v}${unit}（${std}）`;
  }
  return `${label}：${v}${unit}（${std} ${j.icon}${j.text}）`;
}
