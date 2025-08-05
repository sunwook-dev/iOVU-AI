-- ============================================
-- Migration: Add Korean brand name column
-- ============================================
-- Description: Adds brand_name_korean column to 01_brands table
-- Version: 1.0.0
-- Date: 2025-07-25
-- ============================================

USE modular_agents_db;

-- Add brand_name_korean column to 01_brands table
ALTER TABLE 01_brands 
ADD COLUMN brand_name_korean VARCHAR(255) COMMENT '브랜드 한글명' AFTER brand_official_name,
ADD INDEX idx_brand_name_korean (brand_name_korean);

-- Update existing 01_brands with Korean names
UPDATE 01_brands 
SET brand_name_korean = CASE 
    WHEN brand_official_name = 'uniformbridge' THEN '유니폼브릿지'
    WHEN brand_official_name = 'kijun' THEN '기준'
    ELSE NULL
END
WHERE brand_official_name IN ('uniformbridge', 'kijun');