-- ============================================
-- Migration: Change brand_id to brand_name
-- Version: 3.0.0
-- Description: Migrate from brand_id (INT) to brand_official_name (VARCHAR) as foreign key
-- ============================================

-- IMPORTANT: Backup your database before running this migration!
-- mysqldump -u root -p modular_agents_db > backup_before_migration.sql

USE modular_agents_db;

-- Disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- STEP 1: Add brand_name columns to all tables
-- ============================================

-- Add brand_name column to raw tables
ALTER TABLE raw_web_data 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE 03_raw_instagram_data 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE raw_naver_blog_data 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE raw_tistory_data 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

-- Add brand_name column to cleaned tables
ALTER TABLE cleaned_web_text 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE `07_instagram_data` 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE cleaned_naver_text 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE cleaned_tistory_text 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

-- Add brand_name column to other tables
ALTER TABLE cleaning_logs 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE crawl_sessions 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE keyword_extraction_status 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

ALTER TABLE prompt_keywords 
ADD COLUMN brand_name VARCHAR(255) COLLATE utf8mb4_unicode_ci AFTER brand_id;

-- ============================================
-- STEP 2: Populate brand_name from brand_id
-- ============================================

-- Update raw tables
UPDATE raw_web_data rwd
JOIN 01_brands b ON rwd.brand_id = b.id
SET rwd.brand_name = b.brand_official_name
WHERE rwd.brand_id IS NOT NULL;

UPDATE 03_raw_instagram_data rid
JOIN 01_brands b ON rid.brand_id = b.id
SET rid.brand_name = b.brand_official_name
WHERE rid.brand_id IS NOT NULL;

UPDATE raw_naver_blog_data rnd
JOIN 01_brands b ON rnd.brand_id = b.id
SET rnd.brand_name = b.brand_official_name
WHERE rnd.brand_id IS NOT NULL;

UPDATE raw_tistory_data rtd
JOIN 01_brands b ON rtd.brand_id = b.id
SET rtd.brand_name = b.brand_official_name
WHERE rtd.brand_id IS NOT NULL;

-- Update cleaned tables
UPDATE cleaned_web_text cwt
JOIN 01_brands b ON cwt.brand_id = b.id
SET cwt.brand_name = b.brand_official_name
WHERE cwt.brand_id IS NOT NULL;

UPDATE `07_instagram_data` cit
JOIN 01_brands b ON cit.brand_id = b.id
SET cit.brand_name = b.brand_official_name
WHERE cit.brand_id IS NOT NULL;

UPDATE cleaned_naver_text cnt
JOIN 01_brands b ON cnt.brand_id = b.id
SET cnt.brand_name = b.brand_official_name
WHERE cnt.brand_id IS NOT NULL;

UPDATE cleaned_tistory_text ctt
JOIN 01_brands b ON ctt.brand_id = b.id
SET ctt.brand_name = b.brand_official_name
WHERE ctt.brand_id IS NOT NULL;

-- Update other tables
UPDATE cleaning_logs cl
JOIN 01_brands b ON cl.brand_id = b.id
SET cl.brand_name = b.brand_official_name
WHERE cl.brand_id IS NOT NULL;

UPDATE crawl_sessions cs
JOIN 01_brands b ON cs.brand_id = b.id
SET cs.brand_name = b.brand_official_name
WHERE cs.brand_id IS NOT NULL;

UPDATE keyword_extraction_status kes
JOIN 01_brands b ON kes.brand_id = b.id
SET kes.brand_name = b.brand_official_name
WHERE kes.brand_id IS NOT NULL;

UPDATE prompt_keywords pk
JOIN 01_brands b ON pk.brand_id = b.id
SET pk.brand_name = b.brand_official_name
WHERE pk.brand_id IS NOT NULL;

-- ============================================
-- STEP 3: Drop foreign key constraints
-- ============================================

-- Drop foreign keys from raw tables
ALTER TABLE raw_web_data DROP FOREIGN KEY raw_web_data_ibfk_1;
ALTER TABLE 03_raw_instagram_data DROP FOREIGN KEY 03_raw_instagram_data_ibfk_1;
ALTER TABLE raw_naver_blog_data DROP FOREIGN KEY raw_naver_blog_data_ibfk_1;
ALTER TABLE raw_tistory_data DROP FOREIGN KEY raw_tistory_data_ibfk_1;

-- Drop foreign keys from cleaned tables
ALTER TABLE cleaned_web_text DROP FOREIGN KEY cleaned_web_text_ibfk_1;
ALTER TABLE `07_instagram_data` DROP FOREIGN KEY cleaned_instagram_text_ibfk_1;
ALTER TABLE cleaned_naver_text DROP FOREIGN KEY cleaned_naver_text_ibfk_1;
ALTER TABLE cleaned_tistory_text DROP FOREIGN KEY cleaned_tistory_text_ibfk_1;

-- Drop foreign keys from other tables
ALTER TABLE cleaning_logs DROP FOREIGN KEY cleaning_logs_ibfk_1;
ALTER TABLE crawl_sessions DROP FOREIGN KEY crawl_sessions_ibfk_1;
ALTER TABLE keyword_extraction_status DROP FOREIGN KEY keyword_extraction_status_ibfk_1;
ALTER TABLE prompt_keywords DROP FOREIGN KEY prompt_keywords_ibfk_1;

-- ============================================
-- STEP 4: Change 01_brands table primary key
-- ============================================

-- Drop the auto_increment from id
ALTER TABLE 01_brands MODIFY id INT UNSIGNED NOT NULL;

-- Drop the primary key
ALTER TABLE 01_brands DROP PRIMARY KEY;

-- Add primary key to brand_official_name
ALTER TABLE 01_brands ADD PRIMARY KEY (brand_official_name);

-- Drop the id column
ALTER TABLE 01_brands DROP COLUMN id;

-- ============================================
-- STEP 5: Drop brand_id columns and add new foreign keys
-- ============================================

-- Raw tables
ALTER TABLE raw_web_data 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_raw_web_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE 03_raw_instagram_data 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_raw_instagram_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE raw_naver_blog_data 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_raw_naver_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE raw_tistory_data 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_raw_tistory_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

-- Cleaned tables
ALTER TABLE cleaned_web_text 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_cleaned_web_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `07_instagram_data` 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_cleaned_instagram_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE cleaned_naver_text 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_cleaned_naver_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE cleaned_tistory_text 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_cleaned_tistory_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

-- Other tables
ALTER TABLE cleaning_logs 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_cleaning_logs_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE crawl_sessions 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_crawl_sessions_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE keyword_extraction_status 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_keyword_status_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE prompt_keywords 
DROP COLUMN brand_id,
ADD CONSTRAINT fk_prompt_keywords_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

-- ============================================
-- STEP 6: Update indexes
-- ============================================

-- Update indexes on raw tables
ALTER TABLE raw_web_data 
DROP INDEX idx_brand_crawled,
ADD INDEX idx_brand_crawled (brand_name, crawled_at);

ALTER TABLE 03_raw_instagram_data 
DROP INDEX idx_brand_posted,
ADD INDEX idx_brand_posted (brand_name, posted_at);

ALTER TABLE raw_naver_blog_data 
DROP INDEX idx_brand_posted,
ADD INDEX idx_brand_posted (brand_name, posted_at);

ALTER TABLE raw_tistory_data 
DROP INDEX idx_brand_posted,
ADD INDEX idx_brand_posted (brand_name, posted_at);

-- Update indexes on cleaned tables
ALTER TABLE cleaned_web_text 
DROP INDEX idx_brand_cleaned,
ADD INDEX idx_brand_cleaned (brand_name, cleaned_at);

ALTER TABLE `07_instagram_data` 
DROP INDEX idx_brand_cleaned,
ADD INDEX idx_brand_cleaned (brand_name, cleaned_at);

ALTER TABLE cleaned_naver_text 
DROP INDEX idx_brand_cleaned,
ADD INDEX idx_brand_cleaned (brand_name, cleaned_at);

ALTER TABLE cleaned_tistory_text 
DROP INDEX idx_brand_cleaned,
ADD INDEX idx_brand_cleaned (brand_name, cleaned_at);

-- Update indexes on other tables
ALTER TABLE cleaning_logs 
DROP INDEX idx_brand_platform,
ADD INDEX idx_brand_platform (brand_name, platform);

ALTER TABLE crawl_sessions 
DROP INDEX idx_brand_platform,
ADD INDEX idx_brand_platform (brand_name, platform);

ALTER TABLE keyword_extraction_status 
DROP INDEX idx_brand_status,
ADD INDEX idx_brand_status (brand_name, status);

ALTER TABLE prompt_keywords 
DROP INDEX idx_brand,
ADD INDEX idx_brand (brand_name);

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Record migration
INSERT INTO migration_history (version, migration_name, status, execution_time_ms)
VALUES ('3.0.0', 'Migrated from brand_id to brand_name as foreign key', 'completed', 0);

-- ============================================
-- Migration Complete!
-- ============================================