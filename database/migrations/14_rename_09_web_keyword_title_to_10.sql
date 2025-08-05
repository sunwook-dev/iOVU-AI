-- ============================================
-- Migration: Rename 09_web_keyword_title to 10_web_keyword_title
-- Date: 2025-07-26
-- Description: 테이블 번호 체계 업데이트
-- ============================================

USE modular_agents_db;

-- 1. Rename the table
ALTER TABLE `09_web_keyword_title` 
RENAME TO `10_web_keyword_title`;

-- 2. Update any foreign key constraints if they exist
-- Note: This table doesn't have explicit foreign key constraints defined

-- 3. Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('14', 'Rename 09_web_keyword_title to 10_web_keyword_title', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();