-- ============================================
-- Migration: Rename cleaned_tistory_text to 09_refined_tistory_data
-- Date: 2025-07-26
-- Description: cleaned_tistory_text 테이블을 09_refined_tistory_data로 이름 변경
-- ============================================

USE modular_agents_db;

-- 1. Drop existing foreign key constraint
ALTER TABLE cleaned_tistory_text DROP FOREIGN KEY cleaned_tistory_text_brand_fk;

-- 2. Rename table
ALTER TABLE cleaned_tistory_text RENAME TO `09_refined_tistory_data`;

-- 3. Recreate foreign key with new table reference
ALTER TABLE `09_refined_tistory_data` 
ADD CONSTRAINT fk_refined_tistory_brand 
FOREIGN KEY (brand_id) REFERENCES `01_brands`(id) 
ON DELETE CASCADE;

-- Note: Indexes are automatically updated with table rename