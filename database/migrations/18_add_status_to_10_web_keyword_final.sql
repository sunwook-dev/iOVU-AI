-- ============================================
-- Migration: Add status column to 10_web_keyword_final
-- Date: 2025-07-26
-- Description: status 컬럼 추가 (0: 일반, 1: 중요(title), 2: cleaned_text)
-- ============================================

USE modular_agents_db;

-- 1. Add status column
ALTER TABLE `10_web_keyword_final`
ADD COLUMN `status` TINYINT DEFAULT 0 COMMENT '0: 일반, 1: 중요(title), 2: cleaned_text' AFTER `source`;

-- 2. Add index for status
ALTER TABLE `10_web_keyword_final`
ADD INDEX idx_status (status);

-- 3. Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('18', 'Add status column to 10_web_keyword_final', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();