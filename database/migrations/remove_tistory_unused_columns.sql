-- ============================================
-- Migration: Remove unused columns from raw_tistory_data
-- Date: 2025-01-25
-- Description: Removes columns that are not being used or populated:
--   - has_code_block, code_languages (handled by refiner)
--   - view_count, like_count, comment_count (no API access)
--   - is_private, modified_at (not available/used)
-- ============================================

USE modular_agents_db;

-- Drop the unused columns
ALTER TABLE raw_tistory_data
    DROP COLUMN IF EXISTS has_code_block,
    DROP COLUMN IF EXISTS code_languages,
    DROP COLUMN IF EXISTS view_count,
    DROP COLUMN IF EXISTS like_count,
    DROP COLUMN IF EXISTS comment_count,
    DROP COLUMN IF EXISTS is_private,
    DROP COLUMN IF EXISTS modified_at;

-- Drop the index on has_code_block if it exists
ALTER TABLE raw_tistory_data DROP INDEX IF EXISTS idx_has_code;

-- Add migration record
INSERT INTO migration_history (migration_name, description, applied_at)
VALUES (
    'remove_tistory_unused_columns',
    'Removed unused columns: has_code_block, code_languages, view_count, like_count, comment_count, is_private, modified_at',
    NOW()
);