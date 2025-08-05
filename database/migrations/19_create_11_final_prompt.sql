-- ============================================
-- Migration: Create 11_final_prompt table
-- Date: 2025-07-26
-- Description: 프롬프트 생성기가 만든 최종 프롬프트 저장 테이블
-- ============================================

USE modular_agents_db;

-- 1. Create final prompt table
CREATE TABLE IF NOT EXISTS `11_final_prompt` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '자동 증가 ID',
    `brand_id` INT UNSIGNED NOT NULL COMMENT '브랜드 ID',
    `brand_name` VARCHAR(255) NOT NULL COMMENT '브랜드명',
    
    -- 프롬프트 내용
    `prompt_text` TEXT NOT NULL COMMENT '생성된 프롬프트 (한국어)',
    `prompt_text_en` TEXT COMMENT '영어 버전 프롬프트 (선택)',
    `language` VARCHAR(10) DEFAULT 'ko' COMMENT '언어 (ko/en)',
    
    -- 3×3 매트릭스 분류
    `intent_type` VARCHAR(20) NOT NULL COMMENT '의도: informational/navigational/transactional',
    `difficulty_level` VARCHAR(10) NOT NULL COMMENT '난이도: easy/medium/hard',
    
    -- 생성 정보
    `generation_method` VARCHAR(50) NOT NULL COMMENT '생성 방법: doc_expansion/domain_adapt/template_gpt4',
    `domain_major` VARCHAR(100) COMMENT '주요 도메인',
    `domain_minor` JSON COMMENT '세부 도메인 (JSON 배열)',
    
    -- 키워드 및 품질
    `keywords_used` JSON COMMENT '사용된 키워드 목록 (JSON 배열)',
    `source_content_ids` JSON COMMENT '참조된 콘텐츠 ID (JSON 배열)',
    `quality_scores` JSON COMMENT '품질 점수 (JSON 객체)',
    -- quality_scores 예시:
    -- {
    --   "naturalness": 0.85,
    --   "intent_match": 0.90,
    --   "difficulty_match": 0.88,
    --   "geo_score": 0.75,
    --   "domain_relevance": 0.92,
    --   "overall": 0.86
    -- }
    
    -- GEO 최적화
    `optimization_tags` JSON COMMENT 'GEO 최적화 태그 (JSON 배열)',
    -- optimization_tags 예시: ["statistics_friendly", "citation_ready", "comparison_ready"]
    
    -- 메타데이터
    `metadata` JSON COMMENT '추가 메타데이터 (JSON 객체)',
    
    -- 검증 상태
    `is_validated` BOOLEAN DEFAULT FALSE COMMENT '검증 완료 여부',
    `validation_notes` TEXT COMMENT '검증 노트',
    
    -- 타임스탬프
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
    
    -- 인덱스
    INDEX idx_brand_id (brand_id),
    INDEX idx_intent_difficulty (intent_type, difficulty_level),
    INDEX idx_generation_method (generation_method),
    INDEX idx_language (language),
    INDEX idx_quality_overall ((CAST(JSON_EXTRACT(quality_scores, '$.overall') AS DECIMAL(3,2)))),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_validated (is_validated),
    
    -- 외래키 (선택적 - brands 테이블이 있다면)
    FOREIGN KEY (brand_id) REFERENCES `01_brands`(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Agent 12에서 생성한 최종 프롬프트 저장 테이블';

-- 2. Create prompt generation batches table for tracking
CREATE TABLE IF NOT EXISTS `11_prompt_generation_batches` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `batch_id` VARCHAR(36) UNIQUE NOT NULL COMMENT 'UUID 배치 ID',
    `brand_id` INT UNSIGNED NOT NULL COMMENT '브랜드 ID',
    
    -- 배치 정보
    `total_count` INT UNSIGNED NOT NULL COMMENT '목표 프롬프트 수',
    `completed_count` INT UNSIGNED DEFAULT 0 COMMENT '완료된 프롬프트 수',
    `status` ENUM('in_progress', 'completed', 'failed') DEFAULT 'in_progress' COMMENT '배치 상태',
    
    -- 분포 추적 (JSON)
    `matrix_distribution` JSON COMMENT '9개 셀별 분포',
    -- 예시: {"informational_easy": 12, "informational_medium": 11, ...}
    
    `language_distribution` JSON COMMENT '언어별 분포',
    -- 예시: {"ko": 90, "en": 10}
    
    `method_distribution` JSON COMMENT '생성 방법별 분포',
    -- 예시: {"doc_expansion": 50, "domain_adapt": 30, "template_gpt4": 20}
    
    -- 품질 통계
    `quality_stats` JSON COMMENT '품질 통계',
    -- 예시: {"average_score": 0.82, "high_quality_ratio": 0.75, "validation_pass_rate": 0.85}
    
    -- 오류 처리
    `error_message` TEXT COMMENT '오류 메시지',
    
    -- 타임스탬프
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `completed_at` TIMESTAMP NULL,
    
    INDEX idx_batch_id (batch_id),
    INDEX idx_brand_id (brand_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC),
    
    FOREIGN KEY (brand_id) REFERENCES `01_brands`(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='프롬프트 생성 배치 추적 테이블';

-- 3. Create view for prompt distribution analysis
CREATE OR REPLACE VIEW `11_prompt_distribution_view` AS
SELECT 
    brand_id,
    brand_name,
    intent_type,
    difficulty_level,
    language,
    COUNT(*) as prompt_count,
    AVG(CAST(JSON_EXTRACT(quality_scores, '$.overall') AS DECIMAL(3,2))) as avg_quality,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY brand_id), 2) as percentage
FROM `11_final_prompt`
WHERE quality_scores IS NOT NULL
GROUP BY brand_id, brand_name, intent_type, difficulty_level, language
ORDER BY brand_id, intent_type, difficulty_level, language;

-- 4. Create view for brand prompt summary
CREATE OR REPLACE VIEW `11_brand_prompt_summary` AS
SELECT 
    fp.brand_id,
    fp.brand_name,
    COUNT(*) as total_prompts,
    COUNT(CASE WHEN language = 'ko' THEN 1 END) as korean_prompts,
    COUNT(CASE WHEN language = 'en' THEN 1 END) as english_prompts,
    AVG(CAST(JSON_EXTRACT(quality_scores, '$.overall') AS DECIMAL(3,2))) as avg_quality_score,
    COUNT(CASE WHEN is_validated THEN 1 END) as validated_count,
    COUNT(DISTINCT intent_type) as intent_types_covered,
    COUNT(DISTINCT difficulty_level) as difficulty_levels_covered,
    MIN(created_at) as first_prompt_at,
    MAX(created_at) as last_prompt_at
FROM `11_final_prompt` fp
GROUP BY fp.brand_id, fp.brand_name;

-- 5. Log the migration
INSERT INTO schema_migrations (version, description, executed_at)
VALUES ('19', 'Create 11_final_prompt table and related structures', NOW())
ON DUPLICATE KEY UPDATE executed_at = NOW();