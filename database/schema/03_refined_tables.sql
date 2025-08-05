-- ============================================
-- Refined Data Tables: Processed and cleaned data
-- ============================================
-- Description: Stores refined and processed content
-- Version: 1.0.0
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: refined_content
-- Description: 정제된 콘텐츠 (모든 플랫폼 통합)
-- ============================================
CREATE TABLE IF NOT EXISTS refined_content (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_table ENUM('web','instagram','naver','tistory') NOT NULL COMMENT '원본 테이블',
    source_id BIGINT UNSIGNED NOT NULL COMMENT '원본 레코드 ID',
    source_url VARCHAR(2048) COMMENT '원본 URL',
    
    -- 정제된 콘텐츠
    refined_text TEXT NOT NULL COMMENT '정제된 텍스트',
    summary TEXT COMMENT 'AI 생성 요약',
    key_points JSON COMMENT '핵심 포인트 배열',
    
    -- 콘텐츠 분석
    entities JSON COMMENT '추출된 엔티티 (제품명, 브랜드명 등)',
    topics JSON COMMENT '주제 분류',
    categories JSON COMMENT '콘텐츠 카테고리',
    sentiment_score FLOAT COMMENT '감성 점수 (-1 to 1)',
    sentiment_label ENUM('positive','neutral','negative') COMMENT '감성 레이블',
    
    -- 언어 분석
    language CHAR(2) DEFAULT 'ko' COMMENT '언어 코드',
    readability_score FLOAT COMMENT '가독성 점수',
    word_count INT COMMENT '단어 수',
    sentence_count INT COMMENT '문장 수',
    
    -- 품질 평가
    quality_score FLOAT COMMENT '콘텐츠 품질 점수 (0-1)',
    relevance_score FLOAT COMMENT '브랜드 관련성 점수 (0-1)',
    informativeness_score FLOAT COMMENT '정보성 점수 (0-1)',
    
    -- 메타데이터
    refiner_version VARCHAR(20) COMMENT '정제기 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    refined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_source (source_table, source_id),
    INDEX idx_quality (quality_score),
    INDEX idx_relevance (relevance_score),
    INDEX idx_sentiment (sentiment_score),
    INDEX idx_refined_at (refined_at),
    FULLTEXT idx_refined_text (refined_text, summary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='정제된 콘텐츠';

-- ============================================
-- Table: content_segments
-- Description: 콘텐츠 세그먼트 (긴 콘텐츠 분할)
-- ============================================
CREATE TABLE IF NOT EXISTS content_segments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    refined_content_id BIGINT UNSIGNED NOT NULL,
    segment_index INT NOT NULL COMMENT '세그먼트 순서',
    segment_type ENUM('intro','body','conclusion','product_desc','review','specs') COMMENT '세그먼트 타입',
    segment_text TEXT NOT NULL COMMENT '세그먼트 텍스트',
    segment_summary VARCHAR(500) COMMENT '세그먼트 요약',
    has_product_info BOOLEAN DEFAULT FALSE COMMENT '제품 정보 포함 여부',
    has_price_info BOOLEAN DEFAULT FALSE COMMENT '가격 정보 포함 여부',
    extracted_products JSON COMMENT '추출된 제품 정보',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (refined_content_id) REFERENCES refined_content(id) ON DELETE CASCADE,
    UNIQUE KEY uk_segment (refined_content_id, segment_index),
    INDEX idx_segment_type (segment_type),
    INDEX idx_has_product (has_product_info),
    FULLTEXT idx_segment_text (segment_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='콘텐츠 세그먼트';

-- ============================================
-- Table: extracted_products_from_content
-- Description: 콘텐츠에서 추출된 제품 정보
-- ============================================
CREATE TABLE IF NOT EXISTS extracted_products_from_content (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    refined_content_id BIGINT UNSIGNED NOT NULL,
    brand_id INT UNSIGNED NOT NULL,
    
    -- 추출된 제품 정보
    product_name VARCHAR(255) COMMENT '제품명',
    product_category VARCHAR(100) COMMENT '제품 카테고리',
    price_info VARCHAR(100) COMMENT '가격 정보 (텍스트)',
    extracted_price DECIMAL(10,2) COMMENT '추출된 가격',
    currency CHAR(3) DEFAULT 'KRW' COMMENT '통화',
    
    -- 제품 속성
    colors JSON COMMENT '언급된 색상',
    sizes JSON COMMENT '언급된 사이즈',
    materials JSON COMMENT '언급된 소재',
    features JSON COMMENT '제품 특징',
    
    -- 컨텍스트
    mention_context TEXT COMMENT '제품 언급 문맥',
    mention_count INT DEFAULT 1 COMMENT '언급 횟수',
    confidence_score FLOAT COMMENT '추출 신뢰도 (0-1)',
    
    -- 매칭 정보
    matched_product_id BIGINT UNSIGNED COMMENT '매칭된 products 테이블 ID',
    match_score FLOAT COMMENT '매칭 점수 (0-1)',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (refined_content_id) REFERENCES refined_content(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    FOREIGN KEY (matched_product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_product_name (product_name),
    INDEX idx_confidence (confidence_score),
    INDEX idx_matched (matched_product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='콘텐츠에서 추출된 제품';

-- ============================================
-- Table: content_relationships
-- Description: 콘텐츠 간 관계
-- ============================================
CREATE TABLE IF NOT EXISTS content_relationships (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    content_id_1 BIGINT UNSIGNED NOT NULL,
    content_id_2 BIGINT UNSIGNED NOT NULL,
    relationship_type ENUM('similar','reference','response','series') COMMENT '관계 타입',
    similarity_score FLOAT COMMENT '유사도 점수 (0-1)',
    shared_keywords JSON COMMENT '공통 키워드',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (content_id_1) REFERENCES refined_content(id) ON DELETE CASCADE,
    FOREIGN KEY (content_id_2) REFERENCES refined_content(id) ON DELETE CASCADE,
    UNIQUE KEY uk_relationship (content_id_1, content_id_2, relationship_type),
    INDEX idx_similarity (similarity_score),
    CHECK (content_id_1 < content_id_2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='콘텐츠 관계';

-- ============================================
-- Table: refinement_logs
-- Description: 정제 프로세스 로그
-- ============================================
CREATE TABLE IF NOT EXISTS refinement_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_table ENUM('web','instagram','naver','tistory') NOT NULL,
    batch_id VARCHAR(36) COMMENT '배치 ID',
    total_items INT DEFAULT 0 COMMENT '전체 항목',
    processed_items INT DEFAULT 0 COMMENT '처리된 항목',
    failed_items INT DEFAULT 0 COMMENT '실패 항목',
    avg_quality_score FLOAT COMMENT '평균 품질 점수',
    total_tokens_used INT COMMENT '사용된 토큰 수',
    total_cost DECIMAL(10,4) COMMENT '총 비용',
    error_details JSON COMMENT '에러 상세',
    started_at DATETIME COMMENT '시작 시각',
    completed_at DATETIME COMMENT '완료 시각',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_batch_id (batch_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='정제 로그';