-- ============================================
-- Migration: Rename 08_refined_tistory_data to 09_refined_tistory_data
-- Date: 2025-07-26
-- Description: 테이블 번호 체계 업데이트
-- ============================================

USE modular_agents_db;

-- 1. Rename the table
ALTER TABLE `08_refined_tistory_data` 
RENAME TO `09_refined_tistory_data`;

-- 2. Update any views that reference this table
-- Update data_completeness_summary view with both tables renamed
CREATE OR REPLACE VIEW data_completeness_summary AS
SELECT 
    b.id AS brand_id,
    b.brand_name_korean,
    b.brand_official_name,
    
    -- Raw data counts
    (SELECT COUNT(*) FROM 02_raw_web_data WHERE brand_id = b.id) AS raw_web_count,
    (SELECT COUNT(*) FROM 03_raw_instagram_data WHERE brand_id = b.id) AS raw_instagram_count,
    (SELECT COUNT(*) FROM 04_raw_naver_blog_data WHERE brand_official_name = b.brand_official_name) AS raw_naver_count,
    (SELECT COUNT(*) FROM 05_raw_tistory_data WHERE brand_official_name = b.brand_official_name) AS raw_tistory_count,
    
    -- Refined data counts
    (SELECT COUNT(*) FROM 06_refined_web_data WHERE brand_id = b.id) AS refined_web_count,
    (SELECT COUNT(*) FROM 08_refined_naver_data WHERE brand_id = b.id) AS refined_naver_count,
    (SELECT COUNT(*) FROM 09_refined_tistory_data WHERE brand_id = b.id) AS refined_tistory_count,
    
    CURRENT_TIMESTAMP AS last_updated
FROM 01_brands b
ORDER BY b.brand_name_korean;

-- Update tistory_processing_status view
CREATE OR REPLACE VIEW tistory_processing_status AS
SELECT 
    b.brand_official_name,
    COUNT(DISTINCT rt.id) AS total_raw_posts,
    COUNT(DISTINCT rtd.source_id) AS processed_posts,
    COUNT(DISTINCT rt.id) - COUNT(DISTINCT rtd.source_id) AS pending_posts,
    ROUND(COUNT(DISTINCT rtd.source_id) * 100.0 / NULLIF(COUNT(DISTINCT rt.id), 0), 2) AS processing_rate
FROM 01_brands b
LEFT JOIN 05_raw_tistory_data rt ON b.brand_official_name = rt.brand_official_name
LEFT JOIN 09_refined_tistory_data rtd ON b.id = rtd.brand_id AND rt.id = rtd.source_id
GROUP BY b.brand_official_name
HAVING total_raw_posts > 0
ORDER BY processing_rate DESC, total_raw_posts DESC;

-- Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('13', 'Rename 08_refined_tistory_data to 09_refined_tistory_data', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();