-- 论文字段：process_method（加工方式）
-- 在 fruit_trace 库执行：
--   USE fruit_trace;
--   SET NAMES utf8mb4;
--   该脚本不保证可重复执行；若列已存在会报错。

USE fruit_trace;

SET NAMES utf8mb4;

ALTER TABLE process_data ADD COLUMN process_method VARCHAR(50) DEFAULT NULL;

