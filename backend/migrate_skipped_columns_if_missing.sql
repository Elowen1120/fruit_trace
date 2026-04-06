-- 管理端“跳过此环节”：skipped 字段（可重复执行版）
-- 说明：通过 information_schema 判断列是否存在，避免重复执行时报错

USE fruit_trace;
SET NAMES utf8mb4;

SET @db = DATABASE();

-- process_data.skipped
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'process_data'
    AND COLUMN_NAME = 'skipped'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE process_data ADD COLUMN skipped TINYINT(1) NOT NULL DEFAULT 0',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- storage_data.skipped
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'storage_data'
    AND COLUMN_NAME = 'skipped'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE storage_data ADD COLUMN skipped TINYINT(1) NOT NULL DEFAULT 0',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- transport_data.skipped
SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'transport_data'
    AND COLUMN_NAME = 'skipped'
);
SET @sql = IF(@exists = 0,
  'ALTER TABLE transport_data ADD COLUMN skipped TINYINT(1) NOT NULL DEFAULT 0',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

