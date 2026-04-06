-- 从旧版本升级（在 fruit_trace 库中按需执行；若列已存在会报错，可忽略对应语句）
USE fruit_trace;

ALTER TABLE product_info ADD COLUMN harvest_batch VARCHAR(20) DEFAULT NULL;

-- 果蔬大类（新鲜度按品类适宜温区判断）；存量行自动为「其他」
ALTER TABLE product_info ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT '其他';
ALTER TABLE planting_data ADD COLUMN plot_no VARCHAR(50) DEFAULT NULL;

-- 已移除查询次数功能：删除 trace_log 表（若不存在则无影响）
DROP TABLE IF EXISTS trace_log;
