/** 解析评论/投诉中的 media 字段（JSON 数组或单条 data URL / URL） */
export function mediaList(media) {
  if (Array.isArray(media)) return media;
  if (typeof media === "string") {
    try {
      const j = JSON.parse(media);
      if (Array.isArray(j)) return j;
    } catch {
      /* ignore */
    }
    return [media];
  }
  return [];
}
