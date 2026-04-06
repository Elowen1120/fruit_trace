/**
 * 冷链温湿度曲线：优先使用 env_readings（environment_series），
 * 无数据时根据环节表单点在前端生成模拟序列（不写库）。
 */

const POINT_COUNT = 5;

/** 温度在基准值 ±0.5℃ 内波动（确定性，避免重渲染抖动） */
const TEMP_OFFSETS = [-0.4, -0.2, 0, 0.2, 0.4];

/** 湿度在基准值 ±3% 内波动 */
const HUM_OFFSETS = [-2.5, -1.25, 0, 1.25, 2.5];

function parseIsoMs(s) {
  if (s == null || s === "") return null;
  const n = String(s).trim();
  if (!n) return null;
  const normalized = n.includes("T") ? n : n.replace(" ", "T");
  const d = new Date(normalized);
  const t = d.getTime();
  return Number.isNaN(t) ? null : t;
}

function formatMsLabel(ms) {
  const d = new Date(ms);
  const pad = (x) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function clampTempOffset(off, base) {
  const v = base + off;
  return Math.round(v * 10) / 10;
}

function clampHumOffset(off, base) {
  const v = base + off;
  return Math.round(v);
}

/**
 * @param {number} startMs
 * @param {number} endMs
 * @returns {{ ms: number, label: string }[]}
 */
function fiveEvenlySpacedLabels(startMs, endMs) {
  let s = startMs;
  let e = endMs;
  if (e <= s) e = s + 3600000;
  const out = [];
  for (let i = 0; i < POINT_COUNT; i++) {
    const ms = s + (i / (POINT_COUNT - 1)) * (e - s);
    out.push({ ms, label: formatMsLabel(ms) });
  }
  return out;
}

/**
 * @param {Array<{label?:string,temp?:*,humidity?:*}>|undefined} envSeries
 * @param {object|null|undefined} storageRow storage_data 对应对象
 * @returns {Array<{label:string,temp:number,humidity:number|null}>}
 */
export function resolveStorageChartRecords(envSeries, storageRow) {
  if (Array.isArray(envSeries) && envSeries.length > 0) {
    return envSeries.map((r) => ({ ...r }));
  }
  if (!storageRow) return [];

  const baseT = Number(storageRow.storage_temp);
  if (!Number.isFinite(baseT)) return [];

  const baseHRaw = storageRow.storage_humidity;
  const hasH =
    baseHRaw != null &&
    baseHRaw !== "" &&
    Number.isFinite(Number(baseHRaw));
  const baseH = hasH ? Number(baseHRaw) : null;

  const inMs = parseIsoMs(storageRow.in_time);
  const outMs = parseIsoMs(storageRow.out_time);
  const opMs = parseIsoMs(storageRow.operate_time);

  let startMs = inMs;
  let endMs = outMs;

  if (startMs != null && endMs != null && endMs > startMs) {
    /* use in→out */
  } else if (startMs != null) {
    endMs = startMs + 24 * 3600000;
  } else if (endMs != null) {
    startMs = endMs - 24 * 3600000;
  } else if (opMs != null) {
    startMs = opMs;
    endMs = opMs + 24 * 3600000;
  } else {
    return buildStorageGeneric(baseT, baseH, hasH);
  }

  if (endMs <= startMs) endMs = startMs + 3600000;

  const slots = fiveEvenlySpacedLabels(startMs, endMs);
  return slots.map((slot, i) => ({
    label: slot.label,
    temp: clampTempOffset(TEMP_OFFSETS[i], baseT),
    humidity: hasH ? clampHumOffset(HUM_OFFSETS[i], baseH) : null,
  }));
}

function buildStorageGeneric(baseT, baseH, hasH) {
  const out = [];
  for (let i = 0; i < POINT_COUNT; i++) {
    out.push({
      label: `监测点${i + 1}`,
      temp: clampTempOffset(TEMP_OFFSETS[i], baseT),
      humidity: hasH ? clampHumOffset(HUM_OFFSETS[i], baseH) : null,
    });
  }
  return out;
}

/**
 * @param {Array<{label?:string,temp?:*,humidity?:*}>|undefined} envSeries
 * @param {object|null|undefined} transportRow transport_data 对应对象
 * @returns {Array<{label:string,temp:number,humidity:number|null}>}
 */
export function resolveTransportChartRecords(envSeries, transportRow) {
  if (Array.isArray(envSeries) && envSeries.length > 0) {
    return envSeries.map((r) => ({ ...r }));
  }
  if (!transportRow) return [];

  const baseT = Number(transportRow.transport_temp);
  if (!Number.isFinite(baseT)) return [];

  const depMs = parseIsoMs(transportRow.departure_time);
  const arrMs = parseIsoMs(transportRow.arrive_time);
  const opMs = parseIsoMs(transportRow.operate_time);

  let startMs = depMs;
  let endMs = arrMs;

  if (startMs != null && endMs != null && endMs > startMs) {
    /* 发货→到达 */
  } else if (startMs != null) {
    endMs = startMs + 24 * 3600000;
  } else if (arrMs != null) {
    startMs = arrMs - 24 * 3600000;
  } else if (opMs != null) {
    startMs = opMs;
    endMs = opMs + 24 * 3600000;
  } else {
    return buildTransportGeneric(baseT);
  }

  if (endMs <= startMs) endMs = startMs + 3600000;

  const slots = fiveEvenlySpacedLabels(startMs, endMs);
  return slots.map((slot, i) => ({
    label: slot.label,
    temp: clampTempOffset(TEMP_OFFSETS[i], baseT),
    humidity: null,
  }));
}

function buildTransportGeneric(baseT) {
  const out = [];
  for (let i = 0; i < POINT_COUNT; i++) {
    out.push({
      label: `监测点${i + 1}`,
      temp: clampTempOffset(TEMP_OFFSETS[i], baseT),
      humidity: null,
    });
  }
  return out;
}
