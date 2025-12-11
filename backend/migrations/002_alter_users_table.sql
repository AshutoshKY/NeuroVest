-- Migration: Fix for ALTER TABLE - MySQL doesn't support IF NOT EXISTS for ADD COLUMN
-- Date: 2025-12-09
-- Purpose: Safely add columns to users table

-- Add columns to users table (will fail if already exists, which is fine)
SET @query1 = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema='stockmarket_db' AND table_name='users' AND column_name='theme') = 0,
    'ALTER TABLE users ADD COLUMN theme VARCHAR(20) DEFAULT ''dark'' COMMENT ''UI theme preference''',
    'SELECT ''Column theme already exists'' AS message');
PREPARE stmt1 FROM @query1;
EXECUTE stmt1;
DEALLOCATE PREPARE stmt1;

SET @query2 = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema='stockmarket_db' AND table_name='users' AND column_name='default_country') = 0,
    'ALTER TABLE users ADD COLUMN default_country VARCHAR(10) DEFAULT ''IN'' COMMENT ''Default country for stocks''',
    'SELECT ''Column default_country already exists'' AS message');
PREPARE stmt2 FROM @query2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

SET @query3 = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema='stockmarket_db' AND table_name='users' AND column_name='email_notifications') = 0,
    'ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT FALSE COMMENT ''Email notifications enabled''',
    'SELECT ''Column email_notifications already exists'' AS message');
PREPARE stmt3 FROM @query3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

SET @query4 = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema='stockmarket_db' AND table_name='users' AND column_name='daily_analysis_limit') = 0,
    'ALTER TABLE users ADD COLUMN daily_analysis_limit INT DEFAULT 5 COMMENT ''Customizable daily analysis limit (admin can change 5-30)''',
    'SELECT ''Column daily_analysis_limit already exists'' AS message');
PREPARE stmt4 FROM @query4;
EXECUTE stmt4;
DEALLOCATE PREPARE stmt4;

SET @query5 = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema='stockmarket_db' AND table_name='users' AND column_name='deleted_at') = 0,
    'ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL COMMENT ''Soft delete timestamp''',
    'SELECT ''Column deleted_at already exists'' AS message');
PREPARE stmt5 FROM @query5;
EXECUTE stmt5;
DEALLOCATE PREPARE stmt5;

-- Add index for deleted_at if not exists
SET @query6 = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE table_schema='stockmarket_db' AND table_name='users' AND index_name='idx_deleted_at') = 0,
    'ALTER TABLE users ADD INDEX idx_deleted_at (deleted_at)',
    'SELECT ''Index idx_deleted_at already exists'' AS message');
PREPARE stmt6 FROM @query6;
EXECUTE stmt6;
DEALLOCATE PREPARE stmt6;

SELECT 'User table columns added successfully' AS status;
