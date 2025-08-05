-- ============================================
-- Migration: Add cleaned_text_v2 column to 06_refined_web_data
-- Date: 2025-07-26
-- Description: 자동 정규화된 텍스트를 저장할 cleaned_text_v2 컬럼 추가
-- ============================================

USE modular_agents_db;

-- Add cleaned_text_v2 column
ALTER TABLE `06_refined_web_data` 
ADD COLUMN `cleaned_text_v2` TEXT COMMENT '자동 정규화된 텍스트' AFTER `cleaned_text`,
ADD COLUMN `v2_cleaning_version` VARCHAR(20) DEFAULT NULL COMMENT '자동 정규화 버전' AFTER `cleaned_text_v2`,
ADD COLUMN `v2_patterns_used` JSON DEFAULT NULL COMMENT '사용된 정규화 패턴' AFTER `v2_cleaning_version`,
ADD COLUMN `v2_cleaned_at` DATETIME DEFAULT NULL COMMENT '자동 정규화 시각' AFTER `v2_patterns_used`;

-- Add index for v2 cleaning tracking
ALTER TABLE `06_refined_web_data`
ADD INDEX `idx_v2_cleaned_at` (`v2_cleaned_at`);