-- ============================================
-- Migration: Rename web_keyword_02 to 10_web_keyword_cleaned_text
-- Date: 2025-07-26
-- Description: 테이블 이름을 더 명확하게 변경하고 번호 체계 통일
-- ============================================

USE modular_agents_db;

-- 1. Rename the table
ALTER TABLE `web_keyword_02` 
RENAME TO `10_web_keyword_cleaned_text`;

-- 2. Update any foreign key constraints if they exist
-- Note: This table doesn't have explicit foreign key constraints defined

-- 3. Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('15', 'Rename web_keyword_02 to 10_web_keyword_cleaned_text', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();