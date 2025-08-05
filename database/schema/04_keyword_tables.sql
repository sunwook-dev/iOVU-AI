-- ============================================
-- Keyword Extraction Tables
-- ============================================
-- Description: Tables for keyword extraction and management
-- Version: 1.0.0
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: keyword_extraction_jobs
-- Description: 키워드 추출 작업 관리
-- ============================================
CREATE TABLE IF NOT EXISTS keyword_extraction_jobs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    refined_content_id BIGINT UNSIGNED NOT NULL,
    brand_id INT UNSIGNED NOT NULL,
    job_id VARCHAR(36) DEFAULT (UUID()) COMMENT '작업 UUID',
    
    -- 작업 상태
    status ENUM('pending','running','completed','failed','cancelled') DEFAULT 'pending' COMMENT '상태',
    priority INT DEFAULT 5 COMMENT '우선순위 (1-10)',
    retry_count INT DEFAULT 0 COMMENT '재시도 횟수',
    
    -- 설정
    algorithm_config JSON COMMENT '알고리즘 설정 {"rake": {...}, "yake": {...}}',
    extraction_params JSON COMMENT '추출 파라미터',
    language CHAR(2) DEFAULT 'ko' COMMENT '언어',
    
    -- 결과 요약
    total_candidates INT DEFAULT 0 COMMENT '후보 키워드 수',
    filtered_keywords INT DEFAULT 0 COMMENT '필터링 후 키워드 수',
    final_keywords INT DEFAULT 0 COMMENT '최종 키워드 수',
    
    -- 처리 정보
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    error_message TEXT COMMENT '에러 메시지',
    
    -- 타임스탬프
    started_at DATETIME COMMENT '시작 시각',
    completed_at DATETIME COMMENT '완료 시각',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (refined_content_id) REFERENCES refined_content(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_job_id (job_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority, status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='키워드 추출 작업';

-- ============================================
-- Table: extracted_keywords
-- Description: 추출된 키워드
-- ============================================
CREATE TABLE IF NOT EXISTS extracted_keywords (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT UNSIGNED NOT NULL,
    brand_id INT UNSIGNED NOT NULL,
    
    -- 키워드 정보
    keyword VARCHAR(255) NOT NULL COMMENT '키워드',
    normalized_keyword VARCHAR(255) NOT NULL COMMENT '정규화된 키워드',
    stem VARCHAR(100) COMMENT '어간',
    
    -- 추출 정보
    algorithm ENUM('RAKE','YAKE','PositionRank','TextRank','Combined') NOT NULL COMMENT '추출 알고리즘',
    algorithm_score FLOAT COMMENT '알고리즘 점수',
    combined_score FLOAT COMMENT '통합 점수 (0-1)',
    
    -- 키워드 속성
    word_count INT DEFAULT 1 COMMENT '단어 수',
    char_count INT COMMENT '문자 수',
    frequency INT DEFAULT 1 COMMENT '출현 빈도',
    positions JSON COMMENT '출현 위치 배열',
    
    -- 분류
    tail_type ENUM('short_tail','mid_tail','long_tail') COMMENT '키워드 길이 타입',
    semantic_category ENUM('product','attribute','situation','persona','brand','style','material','color','feature','other') COMMENT '의미 카테고리',
    is_brand_specific BOOLEAN DEFAULT FALSE COMMENT '브랜드 특화 키워드',
    is_product_name BOOLEAN DEFAULT FALSE COMMENT '제품명 여부',
    is_technical_term BOOLEAN DEFAULT FALSE COMMENT '전문 용어 여부',
    
    -- 중요도
    importance_score FLOAT COMMENT '중요도 점수 (0-1)',
    relevance_score FLOAT COMMENT '관련성 점수 (0-1)',
    uniqueness_score FLOAT COMMENT '독특성 점수 (0-1)',
    
    -- 검증
    is_approved BOOLEAN DEFAULT NULL COMMENT '승인 여부',
    approved_by VARCHAR(100) COMMENT '승인자',
    approved_at DATETIME COMMENT '승인 시각',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_id) REFERENCES keyword_extraction_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_keyword (keyword),
    INDEX idx_normalized (normalized_keyword),
    INDEX idx_algorithm (algorithm),
    INDEX idx_score (combined_score DESC),
    INDEX idx_category (semantic_category),
    INDEX idx_brand_specific (is_brand_specific, brand_id),
    INDEX idx_approved (is_approved),
    FULLTEXT idx_keyword_search (keyword, normalized_keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='추출된 키워드';

-- ============================================
-- Table: keyword_clusters
-- Description: 키워드 클러스터링
-- ============================================
CREATE TABLE IF NOT EXISTS keyword_clusters (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    cluster_name VARCHAR(255) COMMENT '클러스터명',
    cluster_type ENUM('semantic','statistical','hybrid') DEFAULT 'semantic' COMMENT '클러스터링 방법',
    
    -- 클러스터 정보
    centroid_keyword VARCHAR(255) COMMENT '중심 키워드',
    cluster_size INT DEFAULT 0 COMMENT '클러스터 크기',
    coherence_score FLOAT COMMENT '응집도 점수 (0-1)',
    
    -- 클러스터 속성
    main_category VARCHAR(100) COMMENT '주요 카테고리',
    sub_categories JSON COMMENT '하위 카테고리 배열',
    common_attributes JSON COMMENT '공통 속성',
    
    -- 메타데이터
    algorithm_params JSON COMMENT '클러스터링 파라미터',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_cluster_name (cluster_name),
    INDEX idx_coherence (coherence_score),
    INDEX idx_size (cluster_size)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='키워드 클러스터';

-- ============================================
-- Table: keyword_cluster_members
-- Description: 클러스터 멤버 관계
-- ============================================
CREATE TABLE IF NOT EXISTS keyword_cluster_members (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    cluster_id BIGINT UNSIGNED NOT NULL,
    keyword_id BIGINT UNSIGNED NOT NULL,
    membership_score FLOAT DEFAULT 1.0 COMMENT '소속도 점수 (0-1)',
    is_representative BOOLEAN DEFAULT FALSE COMMENT '대표 키워드 여부',
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (cluster_id) REFERENCES keyword_clusters(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES extracted_keywords(id) ON DELETE CASCADE,
    UNIQUE KEY uk_cluster_keyword (cluster_id, keyword_id),
    INDEX idx_membership (membership_score),
    INDEX idx_representative (is_representative)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='클러스터 멤버';

-- ============================================
-- Table: keyword_performance
-- Description: 키워드 성능 추적
-- ============================================
CREATE TABLE IF NOT EXISTS keyword_performance (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    keyword_id BIGINT UNSIGNED NOT NULL,
    brand_id INT UNSIGNED NOT NULL,
    
    -- 사용 통계
    usage_count INT DEFAULT 0 COMMENT '사용 횟수',
    in_title_count INT DEFAULT 0 COMMENT '제목 사용 횟수',
    in_description_count INT DEFAULT 0 COMMENT '설명 사용 횟수',
    
    -- 성능 메트릭
    click_through_rate FLOAT COMMENT 'CTR (%)',
    conversion_rate FLOAT COMMENT '전환율 (%)',
    engagement_score FLOAT COMMENT '참여도 점수',
    
    -- SEO 메트릭
    search_volume INT COMMENT '월간 검색량',
    competition_level ENUM('low','medium','high') COMMENT '경쟁도',
    keyword_difficulty FLOAT COMMENT '키워드 난이도 (0-100)',
    
    -- 트렌드
    trend_direction ENUM('rising','stable','falling') COMMENT '트렌드 방향',
    trend_score FLOAT COMMENT '트렌드 점수',
    seasonal_pattern JSON COMMENT '계절성 패턴',
    
    -- 최적화 효과
    geo_usage_count INT DEFAULT 0 COMMENT 'GEO 최적화 사용 횟수',
    avg_improvement_score FLOAT COMMENT '평균 개선 점수',
    
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (keyword_id) REFERENCES extracted_keywords(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_keyword_perf (keyword_id),
    INDEX idx_usage (usage_count),
    INDEX idx_performance (click_through_rate, conversion_rate),
    INDEX idx_trend (trend_direction)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='키워드 성능';

-- ============================================
-- Table: brand_keywords
-- Description: 브랜드별 주요 키워드
-- ============================================
CREATE TABLE IF NOT EXISTS brand_keywords (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    keyword VARCHAR(255) NOT NULL COMMENT '키워드',
    keyword_type ENUM('core','product','campaign','seasonal','trending') COMMENT '키워드 타입',
    
    -- 중요도
    priority INT DEFAULT 5 COMMENT '우선순위 (1-10)',
    weight FLOAT DEFAULT 1.0 COMMENT '가중치',
    
    -- 출처
    source ENUM('manual','extracted','imported','generated') DEFAULT 'manual' COMMENT '키워드 출처',
    source_reference VARCHAR(500) COMMENT '출처 참조',
    
    -- 상태
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    valid_from DATE COMMENT '유효 시작일',
    valid_until DATE COMMENT '유효 종료일',
    
    -- 메타데이터
    notes TEXT COMMENT '메모',
    created_by VARCHAR(100) COMMENT '생성자',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_brand_keyword (brand_id, keyword),
    INDEX idx_keyword_type (keyword_type),
    INDEX idx_priority (priority),
    INDEX idx_active (is_active),
    INDEX idx_valid_date (valid_from, valid_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='브랜드 키워드';

-- ============================================
-- Triggers
-- ============================================

-- Update cluster size when members are added/removed
DELIMITER $$
CREATE TRIGGER update_cluster_size_insert
AFTER INSERT ON keyword_cluster_members
FOR EACH ROW
BEGIN
    UPDATE keyword_clusters 
    SET cluster_size = (
        SELECT COUNT(*) 
        FROM keyword_cluster_members 
        WHERE cluster_id = NEW.cluster_id
    )
    WHERE id = NEW.cluster_id;
END$$

CREATE TRIGGER update_cluster_size_delete
AFTER DELETE ON keyword_cluster_members
FOR EACH ROW
BEGIN
    UPDATE keyword_clusters 
    SET cluster_size = (
        SELECT COUNT(*) 
        FROM keyword_cluster_members 
        WHERE cluster_id = OLD.cluster_id
    )
    WHERE id = OLD.cluster_id;
END$$
DELIMITER ;