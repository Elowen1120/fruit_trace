-- 为 planting_data / process_data / storage_data / transport_data / sales_data
-- 添加 operate_time 列（仅当列不存在时执行，可重复执行不报错）
-- 使用前请先：USE fruit_trace; （或替换下方库名逻辑为当前库）

SET NAMES utf8mb4;

SET @db = DATABASE();

-- planting_data
SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'planting_data' AND COLUMN_NAME = 'operate_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE planting_data ADD COLUMN operate_time DATETIME DEFAULT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- process_data
SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'process_data' AND COLUMN_NAME = 'operate_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE process_data ADD COLUMN operate_time DATETIME DEFAULT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- storage_data
SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'storage_data' AND COLUMN_NAME = 'operate_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE storage_data ADD COLUMN operate_time DATETIME DEFAULT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- transport_data
SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'transport_data' AND COLUMN_NAME = 'operate_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE transport_data ADD COLUMN operate_time DATETIME DEFAULT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- sales_data
SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'sales_data' AND COLUMN_NAME = 'operate_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE sales_data ADD COLUMN operate_time DATETIME DEFAULT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
