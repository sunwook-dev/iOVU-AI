-- ============================================
-- Migration: Rename cleaned_naver_text to 08_refined_naver_data
-- Date: 2025-07-26
-- Description: cleaned_naver_text 테이블을 08_refined_naver_data로 이름 변경
-- ============================================

USE modular_agents_db;

-- 1. Drop existing foreign key constraint
ALTER TABLE cleaned_naver_text DROP FOREIGN KEY cleaned_naver_text_brand_fk;

-- 2. Rename table
ALTER TABLE cleaned_naver_text RENAME TO `08_refined_naver_data`;

-- 3. Recreate foreign key with new table reference
ALTER TABLE `08_refined_naver_data` 
ADD CONSTRAINT fk_refined_naver_brand 
FOREIGN KEY (brand_id) REFERENCES `01_brands`(id) 
ON DELETE CASCADE;

-- Note: Indexes are automatically updated with table rename