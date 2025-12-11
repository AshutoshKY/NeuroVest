-- Migration: Add authentication tables and fields
-- Created: 2025-12-06
-- Description: Adds role-based access control, email verification, account lockout, and refresh tokens

-- Add new columns to existing users table
ALTER TABLE users
ADD COLUMN role ENUM('user', 'admin') DEFAULT 'user' NOT NULL AFTER hashed_password,
ADD COLUMN is_verified BOOLEAN DEFAULT FALSE NOT NULL AFTER role,
ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL AFTER is_verified,
ADD COLUMN failed_login_attempts INT DEFAULT 0 NOT NULL AFTER is_active,
ADD COLUMN locked_until TIMESTAMP NULL AFTER failed_login_attempts,
ADD INDEX idx_role (role);

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_user_id (user_id),
    UNIQUE KEY unique_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create first admin user (password: Admin@123)
-- You should change this password immediately after first login!
INSERT INTO users (email, hashed_password, role, is_verified, full_name)
VALUES (
    'admin@stockmarket.com',
    '$2b$12$LHvE5h9jR/mLvQWxKwYGNOqL7p4k6zN8V.8yPBxJf2Q7qYZeJKfP6',  -- Admin@123
    'admin',
    TRUE,
    'System Administrator'
)
ON DUPLICATE KEY UPDATE 
    role = 'admin',
    is_verified = TRUE;

-- Verify migration
SELECT 'Migration completed successfully!' AS status;
SELECT 'Users table columns:' AS info;
SHOW COLUMNS FROM users;
SELECT 'Refresh tokens table created:' AS info;
SHOW TABLES LIKE 'refresh_tokens';
