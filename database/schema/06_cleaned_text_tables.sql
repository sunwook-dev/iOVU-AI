-- ============================================
-- Cleaned Text Tables: Processed and refined text data
-- ============================================
-- Description: Stores cleaned and processed text from various sources
-- Version: 1.0.0
-- Date: 2025-07-25
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: 06_refined_web_data
-- Description: 웹사이트 정제된 텍스트
-- ============================================
CREATE TABLE IF NOT EXISTS `06_refined_web_data` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL COMMENT 'raw_web_data 테이블 ID',
    source_url VARCHAR(2048) COMMENT '원본 URL',
    
    -- 정제된 콘텐츠
    title VARCHAR(500) COMMENT '클리닝된 제목 (브랜드명 제거)',
    cleaned_text TEXT NOT NULL COMMENT '정제된 텍스트',
    cleaned_meta_description TEXT COMMENT '정제된 메타 설명',
    cleaned_meta_keywords JSON COMMENT '정제된 키워드 배열',
    cleaned_og_data JSON COMMENT '정제된 OG 데이터',
    cleaned_structured_data JSON COMMENT '정제된 구조화 데이터',
    
    -- 정제 통계
    brand_mentions_removed INT DEFAULT 0 COMMENT '제거된 브랜드명 언급 횟수',
    word_count INT COMMENT '단어 수',
    sentence_count INT COMMENT '문장 수',
    char_count INT COMMENT '문자 수',
    unique_word_ratio FLOAT COMMENT '고유 단어 비율',
    avg_word_length FLOAT COMMENT '평균 단어 길이',
    
    -- 처리 정보
    cleaning_version VARCHAR(20) DEFAULT '3.0' COMMENT '클리닝 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    cleaning_log JSON COMMENT '클리닝 과정 로그',
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '최종 수정 시각',
    
    UNIQUE KEY uk_source (source_id),
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_brand_id (brand_id),
    INDEX idx_cleaned_at (cleaned_at),
    INDEX idx_word_count (word_count),
    FULLTEXT idx_cleaned_text (cleaned_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='웹사이트 정제된 텍스트';

-- ============================================
-- Table: 07_instagram_data
-- Description: Instagram 정제된 텍스트
-- ============================================
CREATE TABLE IF NOT EXISTS `07_instagram_data` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL COMMENT '03_raw_instagram_data 테이블 ID',
    source_url VARCHAR(2048) COMMENT '원본 Instagram URL',
    
    -- 정제된 콘텐츠
    cleaned_caption TEXT COMMENT '정제된 캡션',
    cleaned_hashtags JSON COMMENT '정제된 해시태그 목록',
    cleaned_mentions JSON COMMENT '정제된 멘션 목록',
    cleaned_metadata JSON COMMENT '추가 메타데이터',
    
    -- 정제 통계
    brand_mentions_removed INT DEFAULT 0 COMMENT '제거된 브랜드명 언급 횟수',
    word_count INT COMMENT '단어 수',
    hashtag_count INT COMMENT '해시태그 수',
    mention_count INT COMMENT '멘션 수',
    emoji_count INT COMMENT '이모지 수',
    
    -- 감성 분석
    sentiment_score FLOAT COMMENT '감성 점수 (-1 to 1)',
    sentiment_label ENUM('positive','neutral','negative') COMMENT '감성 레이블',
    
    -- 처리 정보
    cleaning_version VARCHAR(20) DEFAULT '1.0' COMMENT '클리닝 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    
    UNIQUE KEY uk_source (source_id),
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_brand_id (brand_id),
    INDEX idx_cleaned_at (cleaned_at),
    INDEX idx_sentiment (sentiment_score),
    FULLTEXT idx_cleaned_caption (cleaned_caption)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Instagram 정제된 텍스트';

-- ============================================
-- Table: 08_refined_naver_data
-- Description: 네이버 블로그 정제된 텍스트
-- ============================================
CREATE TABLE IF NOT EXISTS `08_refined_naver_data` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL COMMENT 'raw_naver_blog_data 테이블 ID',
    source_url VARCHAR(2048) COMMENT '원본 네이버 블로그 URL',
    
    -- 정제된 콘텐츠
    title VARCHAR(500) COMMENT '정제된 제목',
    cleaned_text TEXT NOT NULL COMMENT '정제된 본문',
    cleaned_tags JSON COMMENT '정제된 태그 목록',
    cleaned_metadata JSON COMMENT '추가 메타데이터',
    
    -- 콘텐츠 분류
    content_type ENUM('review','news','guide','promotion','other') COMMENT '콘텐츠 타입',
    is_sponsored BOOLEAN DEFAULT FALSE COMMENT '스폰서/광고 여부',
    
    -- 정제 통계
    brand_mentions_removed INT DEFAULT 0 COMMENT '제거된 브랜드명 언급 횟수',
    word_count INT COMMENT '단어 수',
    sentence_count INT COMMENT '문장 수',
    image_count INT COMMENT '이미지 수',
    link_count INT COMMENT '링크 수',
    
    -- 품질 평가
    quality_score FLOAT COMMENT '콘텐츠 품질 점수 (0-1)',
    relevance_score FLOAT COMMENT '브랜드 관련성 점수 (0-1)',
    
    -- 처리 정보
    cleaning_version VARCHAR(20) DEFAULT '1.0' COMMENT '클리닝 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    
    UNIQUE KEY uk_source (source_id),
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_brand_id (brand_id),
    INDEX idx_cleaned_at (cleaned_at),
    INDEX idx_quality (quality_score),
    INDEX idx_content_type (content_type),
    FULLTEXT idx_cleaned_text (cleaned_text, title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='네이버 블로그 정제된 텍스트';

-- ============================================
-- Table: 09_refined_tistory_data
-- Description: 티스토리 정제된 텍스트
-- ============================================
CREATE TABLE IF NOT EXISTS `09_refined_tistory_data` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL COMMENT 'raw_tistory_data 테이블 ID',
    source_url VARCHAR(2048) COMMENT '원본 티스토리 URL',
    
    -- 정제된 콘텐츠
    title VARCHAR(500) COMMENT '정제된 제목',
    cleaned_text TEXT NOT NULL COMMENT '정제된 본문',
    cleaned_tags JSON COMMENT '정제된 태그 목록',
    cleaned_categories JSON COMMENT '카테고리 정보',
    cleaned_metadata JSON COMMENT '추가 메타데이터',
    
    -- 콘텐츠 분류
    content_type ENUM('review','news','guide','promotion','tech','other') COMMENT '콘텐츠 타입',
    is_sponsored BOOLEAN DEFAULT FALSE COMMENT '스폰서/광고 여부',
    
    -- 정제 통계
    brand_mentions_removed INT DEFAULT 0 COMMENT '제거된 브랜드명 언급 횟수',
    word_count INT COMMENT '단어 수',
    sentence_count INT COMMENT '문장 수',
    code_block_count INT COMMENT '코드 블록 수',
    image_count INT COMMENT '이미지 수',
    
    -- 품질 평가
    quality_score FLOAT COMMENT '콘텐츠 품질 점수 (0-1)',
    technical_depth_score FLOAT COMMENT '기술적 깊이 점수 (0-1)',
    
    -- 처리 정보
    cleaning_version VARCHAR(20) DEFAULT '1.0' COMMENT '클리닝 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    
    UNIQUE KEY uk_source (source_id),
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_brand_id (brand_id),
    INDEX idx_cleaned_at (cleaned_at),
    INDEX idx_quality (quality_score),
    INDEX idx_content_type (content_type),
    FULLTEXT idx_cleaned_text (cleaned_text, title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='티스토리 정제된 텍스트';

-- ============================================
-- Table: cleaning_logs
-- Description: 정제 프로세스 로그
-- ============================================
CREATE TABLE IF NOT EXISTS cleaning_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED,
    source_type ENUM('web','instagram','naver','tistory') NOT NULL COMMENT '소스 타입',
    batch_id VARCHAR(36) COMMENT '배치 ID (UUID)',
    
    -- 처리 통계
    total_items INT DEFAULT 0 COMMENT '전체 항목 수',
    processed_items INT DEFAULT 0 COMMENT '처리된 항목 수',
    failed_items INT DEFAULT 0 COMMENT '실패한 항목 수',
    skipped_items INT DEFAULT 0 COMMENT '건너뛴 항목 수',
    
    -- 품질 통계
    avg_word_count FLOAT COMMENT '평균 단어 수',
    avg_quality_score FLOAT COMMENT '평균 품질 점수',
    total_processing_time_ms INT COMMENT '총 처리 시간',
    
    -- 에러 정보
    error_details JSON COMMENT '에러 상세 정보',
    
    -- 시간 정보
    started_at DATETIME COMMENT '시작 시각',
    completed_at DATETIME COMMENT '완료 시각',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_batch_id (batch_id),
    INDEX idx_source_type (source_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='정제 프로세스 로그';