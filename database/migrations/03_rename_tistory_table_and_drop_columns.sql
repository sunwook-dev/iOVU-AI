-- Migration: Rename raw_tistory_data table and drop unused columns
-- Date: 2025-07-25

-- Step 1: Rename the table
ALTER TABLE modular_agents_db.raw_tistory_data 
RENAME TO modular_agents_db.`05_raw_tistory_data`;

-- Step 2: Drop unused columns
ALTER TABLE modular_agents_db.`05_raw_tistory_data`
DROP COLUMN IF EXISTS view_count,
DROP COLUMN IF EXISTS like_count,
DROP COLUMN IF EXISTS comment_count;

-- Note: The table will retain these columns:
-- id, blog_name, post_id, url, title, content, 
-- author, published_at, crawled_at, updated_at