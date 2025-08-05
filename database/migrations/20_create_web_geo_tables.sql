-- ============================================
-- Migration: Create Web GEO Optimization Tables
-- Date: 2025-07-26
-- Description: Agent_13 GEO 최적화 결과 저장 테이블
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: 20_web_geo_analysis
-- Description: GEO 분석 결과 저장
-- ============================================
CREATE TABLE IF NOT EXISTS `20_web_geo_analysis` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    raw_web_data_id BIGINT UNSIGNED NOT NULL,
    
    -- 페이지 정보
    page_url VARCHAR(2048) NOT NULL COMMENT '페이지 URL',
    page_type VARCHAR(50) COMMENT '페이지 타입',
    
    -- SEO/GEO 점수
    seo_score FLOAT COMMENT 'SEO 점수 (0-100)',
    geo_scores JSON COMMENT 'GEO 6가지 기준별 점수',
    -- {
    --   "clarity": 85.5,
    --   "structure": 78.0,
    --   "context": 82.3,
    --   "alignment": 79.5,
    --   "timeliness": 71.0,
    --   "originality": 88.2
    -- }
    
    -- 사이트 전체 점수 (사이트 요약인 경우)
    is_site_summary BOOLEAN DEFAULT FALSE COMMENT '사이트 전체 요약 여부',
    site_seo_score FLOAT COMMENT '사이트 전체 SEO 점수',
    site_geo_score FLOAT COMMENT '사이트 전체 GEO 점수',
    
    -- 분석 상세
    analysis_details JSON COMMENT 'SEO/GEO 분석 상세 정보',
    recommendations JSON COMMENT '개선 권장사항',
    
    -- 타임스탬프
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES `01_brands`(id) ON DELETE CASCADE,
    FOREIGN KEY (raw_web_data_id) REFERENCES `02_raw_web_data`(id) ON DELETE CASCADE,
    INDEX idx_brand_page (brand_id, page_type),
    INDEX idx_scores (seo_score, site_geo_score),
    INDEX idx_site_summary (is_site_summary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='웹 GEO 분석 결과';

-- ============================================
-- Table: 20_web_geo_optimized
-- Description: GEO 최적화 결과 저장
-- ============================================
CREATE TABLE IF NOT EXISTS `20_web_geo_optimized` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    analysis_id BIGINT UNSIGNED NOT NULL,
    brand_id INT UNSIGNED NOT NULL,
    
    -- 최적화된 콘텐츠
    optimized_html LONGTEXT COMMENT '최적화된 HTML',
    
    -- 개별 최적화 요소
    meta_tags JSON COMMENT '최적화된 메타태그',
    -- {
    --   "title": "최적화된 타이틀",
    --   "description": "최적화된 설명",
    --   "keywords": ["키워드1", "키워드2"],
    --   "og_title": "오픈그래프 타이틀",
    --   "og_description": "오픈그래프 설명"
    -- }
    
    jsonld_schemas JSON COMMENT 'JSON-LD 스키마',
    -- {
    --   "schemas": [...],
    --   "schema_types": ["Organization", "WebSite", "BreadcrumbList"]
    -- }
    
    faq_content JSON COMMENT 'FAQ 콘텐츠',
    -- {
    --   "faqs": [
    --     {"question": "...", "answer": "...", "category": "..."}
    --   ],
    --   "faq_schema": {...}
    -- }
    
    h1_optimization JSON COMMENT 'H1 태그 최적화 정보',
    -- {
    --   "original_h1_count": 2,
    --   "action_taken": "converted_multiple_h1_to_h2",
    --   "final_h1_count": 1,
    --   "h1_content": "최종 H1 내용"
    -- }
    
    -- 개선 사항
    improvements JSON COMMENT '적용된 개선사항',
    optimization_type VARCHAR(50) COMMENT '최적화 타입 (full/meta_only/content_only)',
    
    -- 타임스탬프
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (analysis_id) REFERENCES `20_web_geo_analysis`(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES `01_brands`(id) ON DELETE CASCADE,
    INDEX idx_analysis (analysis_id),
    INDEX idx_optimization_type (optimization_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='웹 GEO 최적화 결과';

-- ============================================
-- Table: 20_geo_optimization_logs (선택적)
-- Description: GEO 최적화 작업 로그
-- ============================================
CREATE TABLE IF NOT EXISTS `20_geo_optimization_logs` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    session_id VARCHAR(36) DEFAULT (UUID()) COMMENT '세션 UUID',
    
    -- 작업 정보
    optimization_mode ENUM('analyze', 'optimize', 'full') DEFAULT 'full' COMMENT '최적화 모드',
    total_pages INT DEFAULT 0 COMMENT '전체 페이지 수',
    analyzed_pages INT DEFAULT 0 COMMENT '분석된 페이지 수',
    optimized_pages INT DEFAULT 0 COMMENT '최적화된 페이지 수',
    
    -- 점수 요약
    avg_seo_score_before FLOAT COMMENT '최적화 전 평균 SEO 점수',
    avg_seo_score_after FLOAT COMMENT '최적화 후 평균 SEO 점수',
    avg_geo_score_before FLOAT COMMENT '최적화 전 평균 GEO 점수',
    avg_geo_score_after FLOAT COMMENT '최적화 후 평균 GEO 점수',
    
    -- API 사용량
    llm_tokens_used INT DEFAULT 0 COMMENT '사용된 LLM 토큰 수',
    llm_cost DECIMAL(10,4) COMMENT 'LLM 사용 비용',
    
    -- 상태
    status ENUM('running', 'completed', 'failed', 'cancelled') DEFAULT 'running',
    error_message TEXT COMMENT '에러 메시지',
    
    -- 타임스탬프
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    FOREIGN KEY (brand_id) REFERENCES `01_brands`(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_status (status),
    INDEX idx_started (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='GEO 최적화 로그';

-- Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('20', 'Create Web GEO optimization tables (20_web_geo_analysis, 20_web_geo_optimized)', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();