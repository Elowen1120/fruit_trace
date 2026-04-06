-- 将「物流」相关库结构统一为「运输」（logistics → transport）
-- 在已有 fruit_trace 库上执行一次；执行前请备份数据库。
-- 若已执行过或表已为 transport_data，请跳过会报错的语句。

USE fruit_trace;

SET NAMES utf8mb4;

-- 1. 业务表重命名与列重命名（旧表 logistics_data → transport_data）
RENAME TABLE logistics_data TO transport_data;

ALTER TABLE transport_data
  CHANGE COLUMN logistics_company transport_company VARCHAR(50) DEFAULT NULL;

-- 2. 环节名称：rfid_data 当前步骤
UPDATE rfid_data SET step = '运输' WHERE step = '物流';

-- 3. 环境曲线：env_readings.stage
UPDATE env_readings SET stage = '运输' WHERE stage = '物流';
