-- 论文字段时间列迁移：添加 harvest_time / process_start_time / process_end_time / in_time / out_time
--                           / departure_time / arrive_time / listing_time
-- 使用前：USE fruit_trace;（建议）
-- 若列已存在会报错，请按需只执行一次或改用 *_if_missing.sql

USE fruit_trace;

SET NAMES utf8mb4;

ALTER TABLE planting_data ADD COLUMN harvest_time DATETIME DEFAULT NULL;

ALTER TABLE process_data ADD COLUMN process_start_time DATETIME DEFAULT NULL;
ALTER TABLE process_data ADD COLUMN process_end_time DATETIME DEFAULT NULL;

ALTER TABLE storage_data ADD COLUMN in_time DATETIME DEFAULT NULL;
ALTER TABLE storage_data ADD COLUMN out_time DATETIME DEFAULT NULL;

ALTER TABLE transport_data ADD COLUMN departure_time DATETIME DEFAULT NULL;
ALTER TABLE transport_data ADD COLUMN arrive_time DATETIME DEFAULT NULL;

ALTER TABLE sales_data ADD COLUMN listing_time DATETIME DEFAULT NULL;

