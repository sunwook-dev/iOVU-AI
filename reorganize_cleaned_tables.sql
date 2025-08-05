-- ============================================
-- 플랫폼별 cleaned text 테이블 재구성
-- Version: 3.0.0
-- ============================================

USE modular_agents_db;

-- ============================================
-- 1. 기존 cleaned_text_content를 web_cleaned_text로 이름 변경
-- ============================================
RENAME TABLE cleaned_text_content TO web_cleaned_text;

-- ============================================
-- 2. Instagram cleaned text 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS instagram_cleaned_text (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL COMMENT '원본 레코드 ID (raw_instagram_data)',
    post_id VARCHAR(255) COMMENT 'Instagram 포스트 ID',
    
    -- 정제된 텍스트
    cleaned_text TEXT NOT NULL COMMENT '정제된 텍스트',
    
    -- 기본 통계
    word_count INT COMMENT '단어 수',
    sentence_count INT COMMENT '문장 수',
    char_count INT COMMENT '문자 수',
    hashtag_count INT COMMENT '해시태그 수',
    mention_count INT COMMENT '멘션 수',
    unique_word_ratio FLOAT COMMENT '고유 단어 비율 (0-1)',
    avg_word_length FLOAT COMMENT '평균 단어 길이',
    
    -- 처리 정보
    cleaning_version VARCHAR(20) DEFAULT '3.0' COMMENT '정제기 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    
    -- 외래키 및 인덱스
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_source (source_id),
    INDEX idx_brand_id (brand_id),
    INDEX idx_cleaned_at (cleaned_at),
    INDEX idx_word_count (word_count),
    INDEX idx_post_id (post_id),
    FULLTEXT idx_cleaned_text (cleaned_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Instagram 정제된 텍스트';

-- ============================================
-- 3. Naver Blog cleaned text 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS naver_cleaned_text (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL COMMENT '원본 레코드 ID (raw_naver_blog_data)',
    blog_id VARCHAR(255) COMMENT '네이버 블로그 ID',
    post_url VARCHAR(2048) COMMENT '포스트 URL',
    
    -- 정제된 텍스트
    cleaned_text TEXT NOT NULL COMMENT '정제된 텍스트',
    
    -- 기본 통계
    word_count INT COMMENT '단어 수',
    sentence_count INT COMMENT '문장 수',
    char_count INT COMMENT '문자 수',
    unique_word_ratio FLOAT COMMENT '고유 단어 비율 (0-1)',
    avg_word_length FLOAT COMMENT '평균 단어 길이',
    
    -- 처리 정보
    cleaning_version VARCHAR(20) DEFAULT '3.0' COMMENT '정제기 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    
    -- 외래키 및 인덱스
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_source (source_id),
    INDEX idx_brand_id (brand_id),
    INDEX idx_cleaned_at (cleaned_at),
    INDEX idx_word_count (word_count),
    INDEX idx_blog_id (blog_id),
    FULLTEXT idx_cleaned_text (cleaned_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='네이버 블로그 정제된 텍스트';

-- ============================================
-- 4. Tistory cleaned text 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS tistory_cleaned_text (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    source_id BIGINT UNSIGNED NOT NULL COMMENT '원본 레코드 ID (raw_tistory_data)',
    blog_name VARCHAR(255) COMMENT '티스토리 블로그명',
    post_url VARCHAR(2048) COMMENT '포스트 URL',
    
    -- 정제된 텍스트
    cleaned_text TEXT NOT NULL COMMENT '정제된 텍스트',
    
    -- 기본 통계
    word_count INT COMMENT '단어 수',
    sentence_count INT COMMENT '문장 수',
    char_count INT COMMENT '문자 수',
    unique_word_ratio FLOAT COMMENT '고유 단어 비율 (0-1)',
    avg_word_length FLOAT COMMENT '평균 단어 길이',
    
    -- 처리 정보
    cleaning_version VARCHAR(20) DEFAULT '3.0' COMMENT '정제기 버전',
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    cleaned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '정제 시각',
    
    -- 외래키 및 인덱스
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_source (source_id),
    INDEX idx_brand_id (brand_id),
    INDEX idx_cleaned_at (cleaned_at),
    INDEX idx_word_count (word_count),
    INDEX idx_blog_name (blog_name),
    FULLTEXT idx_cleaned_text (cleaned_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='티스토리 정제된 텍스트';

-- ============================================
-- 5. web_cleaned_text 테이블 수정 (source_table 컬럼 제거)
-- ============================================
ALTER TABLE web_cleaned_text 
DROP COLUMN source_table,
ADD COLUMN page_title VARCHAR(500) COMMENT '페이지 제목' AFTER source_url,
COMMENT = '웹사이트 정제된 텍스트';

-- ============================================
-- 6. 기존 refined 테이블 삭제 (존재하는 경우에만)
-- ============================================
-- refined_content와 refined_web_data는 이미 데이터가 없으므로 삭제
DROP TABLE IF EXISTS refinement_logs;
DROP TABLE IF EXISTS refined_web_data;
DROP TABLE IF EXISTS refined_content;

-- ============================================
-- 7. 플랫폼별 정제 로그 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS cleaning_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    platform ENUM('web','instagram','naver','tistory') NOT NULL,
    brand_id INT UNSIGNED,
    batch_id VARCHAR(36) COMMENT '배치 ID',
    total_items INT DEFAULT 0 COMMENT '전체 항목',
    processed_items INT DEFAULT 0 COMMENT '처리된 항목',
    failed_items INT DEFAULT 0 COMMENT '실패 항목',
    avg_word_count FLOAT COMMENT '평균 단어 수',
    total_processing_time_ms INT COMMENT '총 처리 시간',
    error_details JSON COMMENT '에러 상세',
    started_at DATETIME COMMENT '시작 시각',
    completed_at DATETIME COMMENT '완료 시각',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_platform (platform),
    INDEX idx_batch_id (batch_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='정제 프로세스 로그';

-- text_cleaning_logs를 cleaning_logs로 이름 변경
DROP TABLE IF EXISTS text_cleaning_logs;

-- ============================================
-- 완료 메시지
-- ============================================
SELECT '테이블 재구성 완료!' as message;
SELECT TABLE_NAME, TABLE_COMMENT 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'modular_agents_db' 
AND TABLE_NAME LIKE '%cleaned%'
ORDER BY TABLE_NAME;