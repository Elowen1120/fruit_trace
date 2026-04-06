-- 为各环节业务表增加 operate_time（操作时间）
-- 在 fruit_trace 库中执行；若列已存在会报错，可忽略对应语句。
-- 需可重复执行时请用：migrate_operate_time_if_missing.sql
-- 应用启动时也会尝试补列（app.ensure_operate_time_columns）。

USE fruit_trace;

SET NAMES utf8mb4;

ALTER TABLE planting_data ADD COLUMN operate_time DATETIME DEFAULT NULL;
ALTER TABLE process_data ADD COLUMN operate_time DATETIME DEFAULT NULL;
ALTER TABLE storage_data ADD COLUMN operate_time DATETIME DEFAULT NULL;
ALTER TABLE transport_data ADD COLUMN operate_time DATETIME DEFAULT NULL;
ALTER TABLE sales_data ADD COLUMN operate_time DATETIME DEFAULT NULL;
