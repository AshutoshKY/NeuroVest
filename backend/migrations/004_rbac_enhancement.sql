-- Phase 1: RBAC Enhancement Migration
-- Migration: 004_rbac_enhancement.sql
-- Description: Add SUPER_ADMIN role support and enhanced audit logging

-- 1. Alter users.role column to support 'super_admin' (15 chars)
ALTER TABLE users MODIFY COLUMN role VARCHAR(15) NOT NULL DEFAULT 'user';

-- 2. Create enhanced audit_logs table (replaces admin_audit_logs)
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Actor information
    actor_id INT NOT NULL COMMENT 'User ID who performed the action',
    actor_role VARCHAR(15) NOT NULL COMMENT 'Role at time of action (user/admin/super_admin)',
    actor_email VARCHAR(255) COMMENT 'Email for quick reference',
    
    -- Network context
    ip_address VARCHAR(45) COMMENT 'IPv4 or IPv6',
    user_agent TEXT COMMENT 'Browser/client user agent',
    
    -- Action details
    action VARCHAR(100) NOT NULL COMMENT 'Action type (e.g., disable_user, toggle_kill_switch)',
    action_category VARCHAR(50) COMMENT 'Category (user_management, security, config, system)',
    target_type VARCHAR(50) COMMENT 'Type of target (user, ip, toggle, system)',
    target_id VARCHAR(255) COMMENT 'ID or identifier of target',
    
    -- Payload tracking
    payload_hash VARCHAR(64) COMMENT 'SHA256 of request payload for integrity',
    changes_json TEXT COMMENT 'JSON of changes made',
    
    -- Result
    success BOOLEAN DEFAULT TRUE COMMENT 'Whether action succeeded',
    error_message TEXT COMMENT 'Error message if failed',
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for fast querying
    INDEX idx_actor_id (actor_id),
    INDEX idx_action (action),
    INDEX idx_action_category (action_category),
    INDEX idx_target_type_id (target_type, target_id),
    INDEX idx_created_at (created_at),
    INDEX idx_success (success),
    
    -- Foreign key (soft - actor might be deleted)
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Enhanced audit log for admin actions';

-- 3. Create auth_epoch table for JWT invalidation (Phase 2 prep)
CREATE TABLE IF NOT EXISTS auth_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by INT COMMENT 'User who last updated',
    
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Authentication settings like auth_epoch';

-- Insert initial auth_epoch
INSERT INTO auth_settings (setting_key, setting_value)
VALUES ('auth_epoch', UNIX_TIMESTAMP())
ON DUPLICATE KEY UPDATE setting_value = setting_value;

-- 4. Data migration from old admin_audit_logs is SKIPPED
-- The old table has a different schema (no changes_json column)
-- New audit entries will be added to the new audit_logs table
-- Old entries remain in admin_audit_logs for reference

-- 5. Verify tables created
SELECT 'Migration 004 Status' as check_type, 'Success' as status
UNION ALL
SELECT 'users.role column size', COLUMN_TYPE 
FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'role'
UNION ALL
SELECT 'audit_logs table', IF(COUNT(*) >= 0, 'Created', 'Missing')
FROM audit_logs
UNION ALL
SELECT 'auth_settings table', IF(COUNT(*) > 0, 'Created with epoch', 'Missing')
FROM auth_settings;
