-- Migration: Create new tables for watchlist, favorites, audit logs, IP blacklist, etc.
-- Date: 2025-12-09
-- Purpose: Add missing tables required for full functionality

-- 1. User Watchlist
CREATE TABLE IF NOT EXISTS user_watchlist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    position INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ticker (user_id, ticker),
    INDEX idx_user_id (user_id),
    INDEX idx_ticker (ticker)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. User Favorites
CREATE TABLE IF NOT EXISTS user_favorites (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    position INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_ticker (user_id, ticker),
    INDEX idx_user_id (user_id),
    INDEX idx_ticker (ticker)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Admin Audit Logs
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_user_id INT NOT NULL,
    action VARCHAR(255) NOT NULL COMMENT 'disable_user, block_ip, toggle_maintenance, etc.',
    target VARCHAR(255) COMMENT 'user_id, IP address, etc.',
    changes JSON COMMENT '{"old": ..., "new": ...}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT,
    FOREIGN KEY (admin_user_id) REFERENCES users(id),
    INDEX idx_admin_user_id (admin_user_id),
    INDEX idx_action (action),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. IP Blacklist
CREATE TABLE IF NOT EXISTS ip_blacklist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(50) UNIQUE NOT NULL,
    reason VARCHAR(255),
    blocked_by_user_id INT COMMENT 'Admin who blocked it, NULL for auto-block',
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    auto_flagged BOOLEAN DEFAULT FALSE COMMENT 'TRUE if auto-blocked by system',
    unblocked_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (blocked_by_user_id) REFERENCES users(id),
    INDEX idx_ip_address (ip_address),
    INDEX idx_is_active (is_active),
    INDEX idx_blocked_at (blocked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Failed Login Attempts
CREATE TABLE IF NOT EXISTS failed_login_attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    failure_reason VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    INDEX idx_ip_timestamp (ip_address, timestamp),
    INDEX idx_timestamp (timestamp),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Analysis History (for admin view of all analyses)
CREATE TABLE IF NOT EXISTS analysis_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticker VARCHAR(20) NOT NULL,
    user_id INT COMMENT 'NULL for guest users',
    ip_address VARCHAR(50),
    device_fingerprint VARCHAR(255),
    sentiment VARCHAR(20) COMMENT 'bullish, neutral, bearish',
    success BOOLEAN DEFAULT TRUE,
    cached BOOLEAN DEFAULT FALSE,
    latency_ms INT COMMENT 'Analysis latency in milliseconds',
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_ticker (ticker),
    INDEX idx_user_id (user_id),
    INDEX idx_success (success),
    INDEX idx_ip_address (ip_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Alter users table to add new columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS theme VARCHAR(20) DEFAULT 'dark' COMMENT 'UI theme preference',
ADD COLUMN IF NOT EXISTS default_country VARCHAR(10) DEFAULT 'IN' COMMENT 'Default country for stocks',
ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT FALSE COMMENT 'Email notifications enabled',
ADD COLUMN IF NOT EXISTS daily_analysis_limit INT DEFAULT 5 COMMENT 'Customizable daily analysis limit (admin can change 5-30)',
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL COMMENT 'Soft delete timestamp',
ADD INDEX idx_deleted_at (deleted_at);

-- Verify tables created
SELECT 'Migration completed successfully' AS status;
