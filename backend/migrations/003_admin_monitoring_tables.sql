-- Phase 3: Admin Monitoring & Tracking Tables
-- Migration: 003_admin_monitoring_tables.sql

-- 1. Login History Table
CREATE TABLE IF NOT EXISTS login_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    failure_reason VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_login_at (login_at),
    INDEX idx_success (success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Active Sessions Table
CREATE TABLE IF NOT EXISTS active_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_token (session_token),
    INDEX idx_user_id (user_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Traffic Analytics Table (Hourly Aggregation)
CREATE TABLE IF NOT EXISTS traffic_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    hour_timestamp TIMESTAMP NOT NULL,
    total_requests INT DEFAULT 0,
    unique_ips INT DEFAULT 0,
    total_analyses INT DEFAULT 0,
    unique_users INT DEFAULT 0,
    avg_latency_ms INT DEFAULT 0,
    error_count INT DEFAULT 0,
    UNIQUE KEY unique_hour (hour_timestamp),
    INDEX idx_hour_timestamp (hour_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Email Queue Table
CREATE TABLE IF NOT EXISTS email_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    email_to VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    body TEXT,
    email_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_email_type (email_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Verify tables created
SELECT 
    'login_history' as table_name, COUNT(*) as row_count FROM login_history
UNION ALL
SELECT 'active_sessions', COUNT(*) FROM active_sessions
UNION ALL
SELECT 'traffic_stats', COUNT(*) FROM traffic_stats
UNION ALL
SELECT 'email_queue', COUNT(*) FROM email_queue;
