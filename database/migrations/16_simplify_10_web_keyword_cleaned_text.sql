-- ============================================
-- Migration: Simplify 10_web_keyword_cleaned_text table
-- Date: 2025-07-26
-- Description: 테이블 구조를 단순화하여 keyword, key, created_at만 유지
-- ============================================

USE modular_agents_db;

-- 1. Drop existing table
DROP TABLE IF EXISTS `10_web_keyword_cleaned_text`;

-- 2. Create new simplified table
CREATE TABLE `10_web_keyword_cleaned_text` (
    `key` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '자동 증가 ID',
    `keyword` VARCHAR(255) UNIQUE NOT NULL COMMENT '추출된 키워드',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
    
    -- Indexes
    UNIQUE INDEX uk_keyword (keyword),
    INDEX idx_created_at (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='GPT-4 mini로 추출한 cleaned_text 키워드 (중복 제거)';

-- 3. Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('16', 'Simplify 10_web_keyword_cleaned_text table structure', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();