-- 论文字段时间列迁移（可重复执行版）
-- 通过 information_schema 判断列是否存在，避免重复执行时报错

USE fruit_trace;

SET NAMES utf8mb4;

SET @db = DATABASE();

-- planting_data.harvest_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'planting_data' AND COLUMN_NAME = 'harvest_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE planting_data ADD COLUMN harvest_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- process_data.process_start_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'process_data' AND COLUMN_NAME = 'process_start_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE process_data ADD COLUMN process_start_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- process_data.process_end_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'process_data' AND COLUMN_NAME = 'process_end_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE process_data ADD COLUMN process_end_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- storage_data.in_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'storage_data' AND COLUMN_NAME = 'in_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE storage_data ADD COLUMN in_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- storage_data.out_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'storage_data' AND COLUMN_NAME = 'out_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE storage_data ADD COLUMN out_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- transport_data.departure_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'transport_data' AND COLUMN_NAME = 'departure_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE transport_data ADD COLUMN departure_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- transport_data.arrive_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'transport_data' AND COLUMN_NAME = 'arrive_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE transport_data ADD COLUMN arrive_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- sales_data.listing_time
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'sales_data' AND COLUMN_NAME = 'listing_time'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE sales_data ADD COLUMN listing_time DATETIME DEFAULT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

