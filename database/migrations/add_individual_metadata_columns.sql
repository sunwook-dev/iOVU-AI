-- ============================================
-- Migration: Add individual metadata columns
-- ============================================
-- Description: Replace cleaned_metadata with individual columns
-- Version: 1.0.0
-- Date: 2025-07-25
-- ============================================

USE modular_agents_db;

-- Add new metadata columns to cleaned_web_text table
ALTER TABLE cleaned_web_text 
ADD COLUMN cleaned_meta_description TEXT COMMENT '정제된 메타 설명' AFTER cleaned_text,
ADD COLUMN cleaned_meta_keywords JSON COMMENT '정제된 키워드 배열' AFTER cleaned_meta_description,
ADD COLUMN cleaned_og_data JSON COMMENT '정제된 OG 데이터' AFTER cleaned_meta_keywords,
ADD COLUMN cleaned_structured_data JSON COMMENT '정제된 구조화 데이터' AFTER cleaned_og_data;

-- Add indexes for JSON columns
ALTER TABLE cleaned_web_text
ADD INDEX idx_cleaned_keywords (cleaned_meta_keywords),
ADD INDEX idx_cleaned_og_data (cleaned_og_data);

-- Add migration record
INSERT INTO migration_history (migration_name, version, description, status) 
VALUES ('add_individual_metadata_columns.sql', '1.0.0', 'Add individual metadata columns', 'completed');