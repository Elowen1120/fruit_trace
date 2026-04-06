/** 管理端与溯源新鲜度：果蔬大类选项及适宜仓储温度带（℃） */

export const PRODUCT_CATEGORY_OPTIONS = [
  "热带水果",
  "温带水果",
  "柑橘类",
  "叶菜类",
  "根茎类",
  "瓜果类",
  "浆果类",
  "其他",
];

/** @type {Record<string, { minTemp: number; maxTemp: number }>} */
export const FRESHNESS_TEMP_RANGE_BY_CATEGORY = {
  热带水果: { minTemp: 10, maxTemp: 15 },
  温带水果: { minTemp: -1, maxTemp: 4 },
  柑橘类: { minTemp: 5, maxTemp: 10 },
  叶菜类: { minTemp: 0, maxTemp: 4 },
  根茎类: { minTemp: 4, maxTemp: 8 },
  瓜果类: { minTemp: 8, maxTemp: 12 },
  浆果类: { minTemp: 0, maxTemp: 2 },
  其他: { minTemp: -2, maxTemp: 8 },
};

export function getFreshnessTempRange(category) {
  const key = category && FRESHNESS_TEMP_RANGE_BY_CATEGORY[category] ? category : "其他";
  return FRESHNESS_TEMP_RANGE_BY_CATEGORY[key];
}
