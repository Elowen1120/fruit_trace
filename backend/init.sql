-- 果蔬溯源 MySQL 初始化脚本（需先创建数据库：CREATE DATABASE fruit_trace CHARACTER SET utf8mb4;）
-- 说明：product_info 增加 rfid_id 字段，用于 RFID 溯源关联（业务必需）

USE fruit_trace;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS product_info (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product_id VARCHAR(50) NOT NULL UNIQUE,
  rfid_id VARCHAR(50) NOT NULL UNIQUE,
  product_name VARCHAR(100) NOT NULL,
  product_address VARCHAR(200) DEFAULT NULL,
  plant_time DATE DEFAULT NULL,
  check_result VARCHAR(20) DEFAULT NULL,
  plot_no VARCHAR(50) DEFAULT NULL,
  variety VARCHAR(50) DEFAULT NULL,
  category VARCHAR(50) NOT NULL DEFAULT '其他',
  create_time DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS rfid_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL UNIQUE,
  step VARCHAR(20) NOT NULL,
  create_time DATETIME DEFAULT NULL,
  INDEX idx_rfid (rfid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS planting_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  daily_water INT DEFAULT NULL,
  light_hour INT DEFAULT NULL,
  temp DECIMAL(4,1) DEFAULT NULL,
  soil_humidity INT DEFAULT NULL,
  fertilizer VARCHAR(100) DEFAULT NULL,
  pesticide VARCHAR(200) DEFAULT NULL,
  manager VARCHAR(50) DEFAULT NULL,
  operate_time DATETIME DEFAULT NULL,
  harvest_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT NULL,
  INDEX idx_rfid (rfid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS process_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  skipped TINYINT(1) NOT NULL DEFAULT 0,
  workshop VARCHAR(50) DEFAULT NULL,
  clean_method VARCHAR(50) DEFAULT NULL,
  process_method VARCHAR(50) DEFAULT NULL,
  package_material VARCHAR(50) DEFAULT NULL,
  quality_result VARCHAR(20) DEFAULT NULL,
  report_img TEXT,
  operate_time DATETIME DEFAULT NULL,
  process_start_time DATETIME DEFAULT NULL,
  process_end_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT NULL,
  INDEX idx_rfid (rfid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS storage_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  skipped TINYINT(1) NOT NULL DEFAULT 0,
  warehouse_addr VARCHAR(100) DEFAULT NULL,
  storage_temp DECIMAL(4,1) DEFAULT NULL,
  storage_humidity INT DEFAULT NULL,
  shelf_life INT DEFAULT NULL,
  storekeeper VARCHAR(50) DEFAULT NULL,
  operate_time DATETIME DEFAULT NULL,
  in_time DATETIME DEFAULT NULL,
  out_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT NULL,
  INDEX idx_rfid (rfid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS transport_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  skipped TINYINT(1) NOT NULL DEFAULT 0,
  transport_company VARCHAR(50) DEFAULT NULL,
  waybill_no VARCHAR(50) DEFAULT NULL,
  transport_temp DECIMAL(4,1) DEFAULT NULL,
  receiver VARCHAR(50) DEFAULT NULL,
  track_img TEXT,
  operate_time DATETIME DEFAULT NULL,
  departure_time DATETIME DEFAULT NULL,
  arrive_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT NULL,
  INDEX idx_rfid (rfid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sales_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  store_name VARCHAR(100) DEFAULT NULL,
  price DECIMAL(8,2) DEFAULT NULL,
  seller VARCHAR(50) DEFAULT NULL,
  sale_end_date DATE DEFAULT NULL,
  voucher_img TEXT,
  operate_time DATETIME DEFAULT NULL,
  listing_time DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT NULL,
  INDEX idx_rfid (rfid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(10) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT NULL,
  INDEX idx_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  user_id INT DEFAULT NULL,
  username VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  score INT NOT NULL,
  media TEXT,
  create_time DATETIME DEFAULT NULL,
  INDEX idx_rfid (rfid_id),
  INDEX idx_comments_user (user_id),
  CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS complaints (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  user_id INT DEFAULT NULL,
  complaint_type VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  contact VARCHAR(100) DEFAULT NULL,
  media TEXT DEFAULT NULL,
  status VARCHAR(20) DEFAULT '待处理',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_rfid_comp (rfid_id),
  INDEX idx_complaints_user (user_id),
  CONSTRAINT fk_complaints_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS env_readings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rfid_id VARCHAR(50) NOT NULL,
  stage VARCHAR(20) NOT NULL,
  point_label VARCHAR(50) DEFAULT NULL,
  temp DECIMAL(5,2) DEFAULT NULL,
  humidity INT DEFAULT NULL,
  sort_order INT DEFAULT 0,
  INDEX idx_rfid_env (rfid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 示例：P001 温湿度波动（若已有同编号产品可跳过插入）
INSERT IGNORE INTO product_info (
  product_id, rfid_id, product_name, product_address, plant_time, check_result, plot_no, variety, category, create_time
) VALUES (
  'P001', 'RFID001', '示例富士苹果', '山东烟台', '2024-03-01', '合格', 'A-01', '红富士', '温带水果', NOW()
);

INSERT IGNORE INTO env_readings (rfid_id, stage, point_label, temp, humidity, sort_order) VALUES
('RFID001', '种植', '第1天', 23.5, 65, 1),
('RFID001', '种植', '第2天', 24.0, 63, 2),
('RFID001', '种植', '第3天', 22.5, 68, 3),
('RFID001', '仓储', '入库', 2.5, 85, 1),
('RFID001', '仓储', '24小时后', 2.8, 84, 2),
('RFID001', '运输', '装车', 3.0, NULL, 1),
('RFID001', '运输', '到货', 3.5, NULL, 2);
