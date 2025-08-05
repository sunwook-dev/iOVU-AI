-- ============================================
-- Migration: Rename web_keyword_extraction_01 to 10_web_keyword_title
-- Date: 2025-07-26
-- Description: web_keyword_extraction_01 테이블을 10_web_keyword_title로 이름 변경
-- ============================================

USE modular_agents_db;

-- Rename table
ALTER TABLE web_keyword_extraction_01 RENAME TO `10_web_keyword_title`;

-- Note: Indexes are automatically updated with table rename