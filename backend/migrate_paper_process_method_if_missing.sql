-- 论文字段：process_method（可重复执行版）

USE fruit_trace;

SET NAMES utf8mb4;

SET @db = DATABASE();

SET @exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'process_data'
    AND COLUMN_NAME = 'process_method'
);

SET @sql = IF(
  @exists = 0,
  'ALTER TABLE process_data ADD COLUMN process_method VARCHAR(50) DEFAULT NULL',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

