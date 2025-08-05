-- ============================================
-- Migration: Create 10_web_keyword_final table
-- Date: 2025-07-26
-- Description: 모든 키워드를 통합한 최종 테이블
-- ============================================

USE modular_agents_db;

-- 1. Create final keyword table
CREATE TABLE IF NOT EXISTS `10_web_keyword_final` (
    `key` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '자동 증가 ID',
    `keyword` VARCHAR(255) UNIQUE NOT NULL COMMENT '통합된 키워드',
    `source` VARCHAR(50) NOT NULL COMMENT '출처: title, cleaned_text, both',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
    
    -- Indexes
    UNIQUE INDEX uk_keyword (keyword),
    INDEX idx_source (source),
    INDEX idx_created_at (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='타이틀과 cleaned_text에서 추출한 모든 키워드 통합 (중복 제거)';

-- 2. Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('17', 'Create 10_web_keyword_final table for combined keywords', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();