-- ============================================
-- Raw Data Tables: Platform-specific crawled data
-- ============================================
-- Description: Stores raw crawled data from different platforms
-- Version: 1.0.0
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: 02_raw_web_data
-- Description: 웹사이트 크롤링 원본 데이터
-- ============================================
CREATE TABLE IF NOT EXISTS 02_raw_web_data (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    url VARCHAR(2048) NOT NULL COMMENT '크롤링한 URL',
    domain VARCHAR(255) GENERATED ALWAYS AS (
        SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(url, '/', 3), '://', -1), '/', 1)
    ) STORED COMMENT '도메인',
    page_type ENUM('homepage','product','about','collection','blog','other') DEFAULT 'other' COMMENT '페이지 타입',
    raw_html LONGTEXT COMMENT '원본 HTML',
    page_title VARCHAR(500) COMMENT '페이지 제목',
    meta_description TEXT COMMENT '메타 설명',
    meta_keywords TEXT COMMENT '메타 키워드',
    og_data JSON COMMENT 'Open Graph 데이터',
    structured_data JSON COMMENT 'JSON-LD 구조화 데이터',
    status_code INT COMMENT 'HTTP 상태 코드',
    response_headers JSON COMMENT 'HTTP 응답 헤더',
    content_hash VARCHAR(64) COMMENT 'SHA256 해시 (중복 체크용)',
    crawl_depth INT DEFAULT 0 COMMENT '크롤링 깊이',
    parent_url VARCHAR(2048) COMMENT '참조 URL',
    crawler_version VARCHAR(20) COMMENT '크롤러 버전',
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '크롤링 시각',
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_url_hash (brand_id, content_hash),
    INDEX idx_url (url(255)),
    INDEX idx_domain (domain),
    INDEX idx_crawled_at (crawled_at),
    INDEX idx_page_type (page_type),
    INDEX idx_status (status_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='웹 크롤링 원본 데이터';

-- ============================================
-- Table: 03_raw_instagram_data
-- Description: Instagram 크롤링 원본 데이터
-- ============================================
CREATE TABLE IF NOT EXISTS 03_raw_instagram_data (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    post_id VARCHAR(100) NOT NULL COMMENT 'Instagram 포스트 ID',
    shortcode VARCHAR(50) COMMENT 'Instagram shortcode',
    post_type ENUM('image','video','carousel','reel','story') COMMENT '콘텐츠 타입',
    caption TEXT COMMENT '게시글 본문',
    hashtags JSON COMMENT '해시태그 배열',
    mentions JSON COMMENT '멘션된 계정 배열',
    location_info JSON COMMENT '위치 정보',
    media_urls JSON COMMENT '미디어 URL 배열',
    thumbnail_url VARCHAR(500) COMMENT '썸네일 URL',
    video_duration INT COMMENT '비디오 길이(초)',
    likes_count INT DEFAULT 0 COMMENT '좋아요 수',
    comments_count INT DEFAULT 0 COMMENT '댓글 수',
    views_count INT COMMENT '조회수 (비디오/릴스)',
    is_sponsored BOOLEAN DEFAULT FALSE COMMENT '광고 여부',
    sponsor_tags JSON COMMENT '협찬 태그',
    posted_at DATETIME COMMENT '게시 시각',
    raw_data JSON COMMENT '원본 API 응답',
    crawler_version VARCHAR(20) COMMENT '크롤러 버전',
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '크롤링 시각',
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_post (brand_id, post_id),
    INDEX idx_shortcode (shortcode),
    INDEX idx_posted_at (posted_at),
    INDEX idx_post_type (post_type),
    INDEX idx_engagement (likes_count, comments_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Instagram 크롤링 원본 데이터';

-- ============================================
-- Table: raw_naver_blog_data
-- Description: 네이버 블로그 크롤링 원본 데이터
-- ============================================
CREATE TABLE IF NOT EXISTS raw_naver_blog_data (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    blog_url VARCHAR(500) NOT NULL COMMENT '블로그 포스트 URL',
    blog_id VARCHAR(100) COMMENT '블로그 ID',
    log_no VARCHAR(50) COMMENT '포스트 번호',
    post_title VARCHAR(500) COMMENT '포스트 제목',
    post_content LONGTEXT COMMENT '포스트 내용 (HTML)',
    post_summary TEXT COMMENT '요약/미리보기',
    author VARCHAR(100) COMMENT '작성자',
    author_blog_name VARCHAR(255) COMMENT '블로그명',
    category VARCHAR(100) COMMENT '카테고리',
    tags JSON COMMENT '태그 배열',
    images JSON COMMENT '이미지 URL 배열',
    view_count INT DEFAULT 0 COMMENT '조회수',
    like_count INT DEFAULT 0 COMMENT '공감수',
    comment_count INT DEFAULT 0 COMMENT '댓글수',
    is_advertisement BOOLEAN DEFAULT FALSE COMMENT '광고성 포스트 여부',
    posted_at DATETIME COMMENT '게시 시각',
    raw_data JSON COMMENT '원본 크롤링 데이터',
    crawler_version VARCHAR(20) COMMENT '크롤러 버전',
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '크롤링 시각',
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_blog_post (blog_id, log_no),
    INDEX idx_blog_url (blog_url(255)),
    INDEX idx_author (author),
    INDEX idx_posted_at (posted_at),
    INDEX idx_view_count (view_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='네이버 블로그 크롤링 원본 데이터';

-- ============================================
-- Table: 05_raw_tistory_data
-- Description: 티스토리 크롤링 원본 데이터
-- ============================================
CREATE TABLE IF NOT EXISTS `05_raw_tistory_data` (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    blog_url VARCHAR(500) NOT NULL COMMENT '블로그 포스트 URL',
    blog_name VARCHAR(100) COMMENT '블로그명',
    post_id VARCHAR(50) COMMENT '포스트 ID',
    post_title VARCHAR(500) COMMENT '포스트 제목',
    post_content LONGTEXT COMMENT '포스트 내용 (HTML)',
    post_summary TEXT COMMENT '요약/설명',
    author VARCHAR(100) COMMENT '작성자',
    category VARCHAR(100) COMMENT '카테고리',
    tags JSON COMMENT '태그 배열',
    images JSON COMMENT '이미지 URL 배열',
    posted_at DATETIME COMMENT '게시 시각',
    raw_data JSON COMMENT '원본 크롤링 데이터',
    crawler_version VARCHAR(20) COMMENT '크롤러 버전',
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '크롤링 시각',
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_tistory_post (blog_name, post_id),
    INDEX idx_blog_url (blog_url(255)),
    INDEX idx_author (author),
    INDEX idx_posted_at (posted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='티스토리 크롤링 원본 데이터';

-- ============================================
-- Table: crawl_sessions
-- Description: 크롤링 세션 관리
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    session_id VARCHAR(36) DEFAULT (UUID()) COMMENT '세션 UUID',
    platform ENUM('web','instagram','naver_blog','tistory') NOT NULL COMMENT '플랫폼',
    crawl_type ENUM('full','incremental','targeted') DEFAULT 'full' COMMENT '크롤링 타입',
    status ENUM('pending','running','completed','failed','cancelled') DEFAULT 'pending' COMMENT '상태',
    total_urls INT DEFAULT 0 COMMENT '전체 URL 수',
    crawled_urls INT DEFAULT 0 COMMENT '크롤링 완료 URL 수',
    failed_urls INT DEFAULT 0 COMMENT '실패한 URL 수',
    config JSON COMMENT '크롤링 설정',
    error_log JSON COMMENT '에러 로그',
    started_at DATETIME COMMENT '시작 시각',
    completed_at DATETIME COMMENT '완료 시각',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_status (status),
    INDEX idx_platform (platform),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='크롤링 세션 관리';