CREATE DATABASE IF NOT EXISTS good
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;

USE good;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  role ENUM('elder', 'child') NOT NULL,
  phone VARCHAR(20) NULL,
  openid VARCHAR(128) NULL,
  name VARCHAR(50) NOT NULL DEFAULT '',
  emergency_phone VARCHAR(20) NULL,
  last_heartbeat_at DATETIME(6) NULL,
  last_operation_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_phone (role, phone),
  UNIQUE KEY uk_role_openid (role, openid),
  KEY idx_users_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS verification_codes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  phone VARCHAR(20) NOT NULL,
  purpose VARCHAR(32) NOT NULL,
  code_hash CHAR(64) NOT NULL,
  expires_at DATETIME(6) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  used TINYINT(1) NOT NULL DEFAULT 0,
  used_at DATETIME(6) NULL,
  PRIMARY KEY (id),
  KEY idx_code_lookup (phone, purpose, id),
  KEY idx_code_expire (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS binding_codes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  elder_id BIGINT UNSIGNED NOT NULL,
  code_hash CHAR(64) NOT NULL,
  expires_at DATETIME(6) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  used TINYINT(1) NOT NULL DEFAULT 0,
  used_at DATETIME(6) NULL,
  PRIMARY KEY (id),
  KEY idx_binding_code_lookup (elder_id, id),
  KEY idx_binding_code_expire (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bindings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  elder_id BIGINT UNSIGNED NOT NULL,
  child_id BIGINT UNSIGNED NOT NULL,
  status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_elder_child (elder_id, child_id),
  KEY idx_child_status (child_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS heartbeats (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  elder_id BIGINT UNSIGNED NOT NULL,
  event_type ENUM('heartbeat', 'checkin') NOT NULL DEFAULT 'heartbeat',
  battery_level TINYINT UNSIGNED NULL,
  latitude DECIMAL(10, 6) NULL,
  longitude DECIMAL(10, 6) NULL,
  created_at DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_heartbeat_elder_time (elder_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sos_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  elder_id BIGINT UNSIGNED NOT NULL,
  audio_key VARCHAR(255) NULL,
  audio_url VARCHAR(512) NULL,
  latitude DECIMAL(10, 6) NULL,
  longitude DECIMAL(10, 6) NULL,
  address VARCHAR(255) NULL,
  created_at DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_sos_elder_time (elder_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS risk_alerts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  elder_id BIGINT UNSIGNED NOT NULL,
  alert_type VARCHAR(50) NOT NULL,
  message VARCHAR(255) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_alert_lookup (elder_id, alert_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

