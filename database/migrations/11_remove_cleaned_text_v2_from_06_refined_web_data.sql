-- ============================================
-- Migration: Remove cleaned_text_v2 columns from 06_refined_web_data
-- Date: 2025-07-26
-- Description: 2차 정규화 기능 제거에 따른 관련 컬럼 삭제
-- ============================================

USE modular_agents_db;

-- Drop index first
ALTER TABLE `06_refined_web_data`
DROP INDEX `idx_v2_cleaned_at`;

-- Drop columns
ALTER TABLE `06_refined_web_data`
DROP COLUMN `cleaned_text_v2`,
DROP COLUMN `v2_cleaning_version`,
DROP COLUMN `v2_patterns_used`,
DROP COLUMN `v2_cleaned_at`;

-- Note: This migration removes the secondary refiner (v2) functionality
-- To rollback, use migration 10_add_cleaned_text_v2_to_06_refined_web_data.sql