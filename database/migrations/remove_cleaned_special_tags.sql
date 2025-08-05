-- ============================================
-- Migration: Remove cleaned_special_tags column
-- ============================================
-- Description: Removes unused cleaned_special_tags column from cleaned_web_text table
-- Version: 1.0.0
-- Date: 2025-07-25
-- ============================================

USE modular_agents_db;

-- Remove cleaned_special_tags column from cleaned_web_text table
ALTER TABLE cleaned_web_text 
DROP COLUMN cleaned_special_tags;

-- Add migration record
INSERT INTO migration_history (migration_name, version, description, status) 
VALUES ('remove_cleaned_special_tags.sql', '1.0.0', 'Remove unused cleaned_special_tags column', 'completed');