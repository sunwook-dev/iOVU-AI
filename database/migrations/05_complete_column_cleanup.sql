-- Migration: Complete column cleanup for 05_raw_tistory_data and 01_brands
-- Date: 2025-07-25
-- Description: Remove all unnecessary columns that were not dropped in previous migrations

-- Step 1: Drop remaining unused columns from 05_raw_tistory_data
ALTER TABLE modular_agents_db.`05_raw_tistory_data`
DROP COLUMN IF EXISTS has_code_block,
DROP COLUMN IF EXISTS code_languages,
DROP COLUMN IF EXISTS view_count,
DROP COLUMN IF EXISTS like_count,
DROP COLUMN IF EXISTS comment_count,
DROP COLUMN IF EXISTS is_private,
DROP COLUMN IF EXISTS modified_at;

-- Step 2: Drop brand_domain_tree from 01_brands (if previous migration didn't work)
ALTER TABLE modular_agents_db.`01_brands`
DROP COLUMN IF EXISTS brand_domain_tree;

-- Note: These migrations use IF EXISTS to avoid errors if columns were already dropped