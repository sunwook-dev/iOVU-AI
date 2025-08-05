-- ============================================
-- Modular Agents Database Setup
-- Version: 3.0.0
-- Description: Complete database schema with brand_official_name as primary key
-- ============================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS modular_agents_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE modular_agents_db;

-- Disable foreign key checks for setup
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. CORE TABLE: 01_brands
-- ============================================

DROP TABLE IF EXISTS 01_brands;
CREATE TABLE `01_brands` (
  `brand_official_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드 공식명 (Primary Key)',
  `brand_name_korean` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '브랜드 한글명',
  `brand_name_english` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '브랜드 영문명',
  `founding_year` int DEFAULT NULL COMMENT '설립 연도',
  `hq_country` char(2) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '본사 국가 (ISO 3166-1 alpha-2)',
  `address` text COLLATE utf8mb4_unicode_ci COMMENT '브랜드 주소',
  `official_site_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '공식 웹사이트',
  `instagram_handle` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Instagram @handle',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`brand_official_name`),
  KEY `idx_country` (`hq_country`),
  KEY `idx_instagram_handle` (`instagram_handle`),
  KEY `idx_brand_name_english` (`brand_name_english`),
  KEY `idx_brand_name_korean` (`brand_name_korean`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. RAW DATA TABLES
-- ============================================

-- raw_web_data table
DROP TABLE IF EXISTS raw_web_data;
CREATE TABLE `raw_web_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `url` varchar(2048) COLLATE utf8mb4_unicode_ci NOT NULL,
  `domain` varchar(255) COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS (substring_index(substring_index(substring_index(`url`,_utf8mb4'/',3),_utf8mb4'/',-1),_utf8mb4':',1)) STORED,
  `page_type` enum('homepage','product','about','collection','blog','other') COLLATE utf8mb4_unicode_ci DEFAULT 'other',
  `raw_html` longtext COLLATE utf8mb4_unicode_ci,
  `page_title` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `meta_description` text COLLATE utf8mb4_unicode_ci,
  `meta_keywords` text COLLATE utf8mb4_unicode_ci,
  `og_data` json DEFAULT NULL,
  `structured_data` json DEFAULT NULL COMMENT 'JSON-LD, microdata, etc.',
  `status_code` int DEFAULT NULL,
  `response_headers` json DEFAULT NULL,
  `content_hash` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'SHA-256 hash of raw_html',
  `content_length` int DEFAULT NULL,
  `crawl_depth` int DEFAULT '0',
  `parent_url` varchar(2048) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `crawler_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `crawled_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_brand_url` (`brand_name`,`url`(500)),
  KEY `idx_url` (`url`(500)),
  KEY `idx_domain` (`domain`),
  KEY `idx_brand_crawled` (`brand_name`,`crawled_at`),
  KEY `idx_page_type` (`page_type`),
  KEY `idx_status_code` (`status_code`),
  CONSTRAINT `fk_raw_web_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 03_raw_instagram_data table
DROP TABLE IF EXISTS 03_raw_instagram_data;
CREATE TABLE `03_raw_instagram_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `post_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shortcode` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `post_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `post_type` enum('image','video','carousel','reel','story') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `caption` text COLLATE utf8mb4_unicode_ci,
  `hashtags` json DEFAULT NULL,
  `mentions` json DEFAULT NULL,
  `location_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `media_urls` json DEFAULT NULL,
  `thumbnail_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `like_count` int DEFAULT '0',
  `comment_count` int DEFAULT '0',
  `view_count` int DEFAULT '0',
  `is_sponsored` tinyint(1) DEFAULT '0',
  `sponsor_tags` json DEFAULT NULL,
  `posted_at` datetime DEFAULT NULL,
  `crawled_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post` (`post_id`),
  KEY `idx_brand_posted` (`brand_name`,`posted_at`),
  KEY `idx_shortcode` (`shortcode`),
  KEY `idx_post_type` (`post_type`),
  KEY `idx_engagement` (`like_count`,`comment_count`),
  CONSTRAINT `fk_raw_instagram_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- raw_naver_blog_data table
DROP TABLE IF EXISTS raw_naver_blog_data;
CREATE TABLE `raw_naver_blog_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `blog_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `log_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `blog_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `post_title` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `post_content` longtext COLLATE utf8mb4_unicode_ci,
  `author_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `author_blog_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tags` json DEFAULT NULL,
  `images` json DEFAULT NULL,
  `view_count` int DEFAULT '0',
  `like_count` int DEFAULT '0',
  `comment_count` int DEFAULT '0',
  `is_advertisement` tinyint(1) DEFAULT '0',
  `posted_at` datetime DEFAULT NULL,
  `crawled_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_blog_post` (`blog_id`,`log_no`),
  KEY `idx_brand_posted` (`brand_name`,`posted_at`),
  KEY `idx_blog_url` (`blog_url`),
  KEY `idx_author` (`author_name`),
  KEY `idx_is_ad` (`is_advertisement`),
  CONSTRAINT `fk_raw_naver_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 05_raw_tistory_data table (renamed from raw_tistory_data)
DROP TABLE IF EXISTS `05_raw_tistory_data`;
CREATE TABLE `05_raw_tistory_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `blog_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entry_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `blog_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `post_title` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `post_content` longtext COLLATE utf8mb4_unicode_ci,
  `author_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tags` json DEFAULT NULL,
  `images` json DEFAULT NULL,
  `code_blocks` json DEFAULT NULL,
  `programming_language` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `posted_at` datetime DEFAULT NULL,
  `crawled_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_blog_entry` (`blog_name`,`entry_id`),
  KEY `idx_brand_posted` (`brand_name`,`posted_at`),
  KEY `idx_blog_url` (`blog_url`),
  KEY `idx_author` (`author_name`),
  KEY `idx_programming_lang` (`programming_language`),
  CONSTRAINT `fk_raw_tistory_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. CLEANED TEXT TABLES
-- ============================================

-- cleaned_web_text table
DROP TABLE IF EXISTS cleaned_web_text;
CREATE TABLE `cleaned_web_text` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `source_id` bigint unsigned NOT NULL,
  `source_url` varchar(2048) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cleaned_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `cleaned_meta_description` text COLLATE utf8mb4_unicode_ci,
  `cleaned_meta_keywords` json DEFAULT NULL,
  `cleaned_og_data` json DEFAULT NULL,
  `cleaned_structured_data` json DEFAULT NULL,
  `brand_mentions_removed` int DEFAULT '0',
  `word_count` int DEFAULT NULL,
  `sentence_count` int DEFAULT NULL,
  `char_count` int DEFAULT NULL,
  `unique_word_ratio` float DEFAULT NULL,
  `avg_word_length` float DEFAULT NULL,
  `cleaning_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '2.0',
  `processing_time_ms` int DEFAULT NULL,
  `cleaning_log` json DEFAULT NULL,
  `cleaned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_source` (`source_id`),
  KEY `idx_brand_cleaned` (`brand_name`,`cleaned_at`),
  KEY `idx_word_count` (`word_count`),
  FULLTEXT KEY `ft_cleaned_text` (`cleaned_text`),
  CONSTRAINT `fk_cleaned_web_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cleaned_web_source` FOREIGN KEY (`source_id`) REFERENCES `raw_web_data` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 07_instagram_data table
DROP TABLE IF EXISTS `07_instagram_data`;
CREATE TABLE `07_instagram_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `source_id` bigint unsigned NOT NULL,
  `post_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cleaned_caption` text COLLATE utf8mb4_unicode_ci,
  `cleaned_hashtags` json DEFAULT NULL,
  `cleaned_mentions` json DEFAULT NULL,
  `hashtag_count` int DEFAULT '0',
  `mention_count` int DEFAULT '0',
  `emoji_count` int DEFAULT '0',
  `word_count` int DEFAULT NULL,
  `sentence_count` int DEFAULT NULL,
  `char_count` int DEFAULT NULL,
  `unique_word_ratio` float DEFAULT NULL,
  `avg_word_length` float DEFAULT NULL,
  `engagement_rate` float DEFAULT NULL,
  `sentiment_score` float DEFAULT NULL,
  `cleaning_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '2.0',
  `processing_time_ms` int DEFAULT NULL,
  `cleaned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_source` (`source_id`),
  KEY `idx_brand_cleaned` (`brand_name`,`cleaned_at`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_engagement` (`engagement_rate`),
  FULLTEXT KEY `ft_cleaned_caption` (`cleaned_caption`),
  CONSTRAINT `fk_cleaned_instagram_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cleaned_instagram_source` FOREIGN KEY (`source_id`) REFERENCES `03_raw_instagram_data` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 08_refined_naver_data table (renamed from cleaned_naver_text)
DROP TABLE IF EXISTS `08_refined_naver_data`;
CREATE TABLE `08_refined_naver_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `source_id` bigint unsigned NOT NULL,
  `blog_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cleaned_title` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cleaned_content` text COLLATE utf8mb4_unicode_ci,
  `cleaned_tags` json DEFAULT NULL,
  `word_count` int DEFAULT NULL,
  `sentence_count` int DEFAULT NULL,
  `char_count` int DEFAULT NULL,
  `unique_word_ratio` float DEFAULT NULL,
  `avg_word_length` float DEFAULT NULL,
  `cleaning_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '2.0',
  `processing_time_ms` int DEFAULT NULL,
  `cleaned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_source` (`source_id`),
  KEY `idx_brand_cleaned` (`brand_name`,`cleaned_at`),
  KEY `idx_blog_id` (`blog_id`),
  KEY `idx_word_count` (`word_count`),
  FULLTEXT KEY `ft_cleaned_content` (`cleaned_content`),
  CONSTRAINT `fk_cleaned_naver_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cleaned_naver_source` FOREIGN KEY (`source_id`) REFERENCES `raw_naver_blog_data` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 09_refined_tistory_data table (renamed from cleaned_tistory_text)
DROP TABLE IF EXISTS `09_refined_tistory_data`;
CREATE TABLE `09_refined_tistory_data` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `source_id` bigint unsigned NOT NULL,
  `blog_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cleaned_title` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cleaned_content` text COLLATE utf8mb4_unicode_ci,
  `cleaned_tags` json DEFAULT NULL,
  `code_blocks_cleaned` json DEFAULT NULL,
  `word_count` int DEFAULT NULL,
  `sentence_count` int DEFAULT NULL,
  `char_count` int DEFAULT NULL,
  `unique_word_ratio` float DEFAULT NULL,
  `avg_word_length` float DEFAULT NULL,
  `cleaning_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '2.0',
  `processing_time_ms` int DEFAULT NULL,
  `cleaned_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_source` (`source_id`),
  KEY `idx_brand_cleaned` (`brand_name`,`cleaned_at`),
  KEY `idx_blog_name` (`blog_name`),
  KEY `idx_word_count` (`word_count`),
  FULLTEXT KEY `ft_cleaned_content` (`cleaned_content`),
  CONSTRAINT `fk_cleaned_tistory_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cleaned_tistory_source` FOREIGN KEY (`source_id`) REFERENCES `raw_tistory_data` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. PROCESSING AND TRACKING TABLES
-- ============================================

-- cleaning_logs table
DROP TABLE IF EXISTS cleaning_logs;
CREATE TABLE `cleaning_logs` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `platform` enum('web','instagram','naver','tistory') COLLATE utf8mb4_unicode_ci NOT NULL,
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_items` int DEFAULT '0',
  `processed_items` int DEFAULT '0',
  `failed_items` int DEFAULT '0',
  `avg_processing_time_ms` float DEFAULT NULL,
  `total_processing_time_ms` int DEFAULT NULL,
  `error_details` json DEFAULT NULL,
  `cleaning_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_brand_platform` (`brand_name`,`platform`),
  KEY `idx_batch` (`batch_id`),
  KEY `idx_started` (`started_at`),
  CONSTRAINT `fk_cleaning_logs_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- crawl_sessions table
DROP TABLE IF EXISTS crawl_sessions;
CREATE TABLE `crawl_sessions` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `platform` enum('web','instagram','naver','tistory') COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `end_time` datetime DEFAULT NULL,
  `total_pages` int DEFAULT '0',
  `success_count` int DEFAULT '0',
  `error_count` int DEFAULT '0',
  `status` enum('running','completed','failed','stopped') COLLATE utf8mb4_unicode_ci DEFAULT 'running',
  `configuration` json DEFAULT NULL,
  `error_logs` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_brand_platform` (`brand_name`,`platform`),
  KEY `idx_session` (`session_id`),
  KEY `idx_status` (`status`),
  KEY `idx_start_time` (`start_time`),
  CONSTRAINT `fk_crawl_sessions_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- keyword_extraction_status table
DROP TABLE IF EXISTS keyword_extraction_status;
CREATE TABLE `keyword_extraction_status` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `source_table` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_id` bigint unsigned NOT NULL,
  `status` enum('pending','processing','completed','failed') COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `keywords_extracted` int DEFAULT '0',
  `extraction_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  `processed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_source` (`source_table`,`source_id`),
  KEY `idx_brand_status` (`brand_name`,`status`),
  KEY `idx_processed` (`processed_at`),
  CONSTRAINT `fk_keyword_status_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- prompt_keywords table
DROP TABLE IF EXISTS prompt_keywords;
CREATE TABLE `prompt_keywords` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '브랜드명 (FK to 01_brands)',
  `cleaned_web_text_id` bigint unsigned NOT NULL,
  `entities` json DEFAULT NULL COMMENT 'Named entities extracted',
  `concepts` json DEFAULT NULL COMMENT 'Key concepts and themes',
  `relationships` json DEFAULT NULL COMMENT 'Entity relationships',
  `processes` json DEFAULT NULL COMMENT 'Processes and methods mentioned',
  `comparisons` json DEFAULT NULL COMMENT 'Comparisons and contrasts',
  `facts` json DEFAULT NULL COMMENT 'Key facts and figures',
  `queries` json DEFAULT NULL COMMENT 'Potential search queries',
  `extraction_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '1.0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_text_id` (`cleaned_web_text_id`),
  KEY `idx_brand` (`brand_name`),
  KEY `idx_created` (`created_at`),
  CONSTRAINT `fk_prompt_keywords_brand` FOREIGN KEY (`brand_name`) REFERENCES `01_brands` (`brand_official_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_prompt_keywords_text` FOREIGN KEY (`cleaned_web_text_id`) REFERENCES `cleaned_web_text` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- migration_history table
DROP TABLE IF EXISTS migration_history;
CREATE TABLE `migration_history` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `version` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `migration_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `executed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `execution_time_ms` int DEFAULT NULL,
  `status` enum('pending','running','completed','failed','rolled_back') COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `checksum` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `applied_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rollback_script` text COLLATE utf8mb4_unicode_ci,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_version` (`version`),
  KEY `idx_status` (`status`),
  KEY `idx_executed` (`executed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. VIEWS FOR COMMON QUERIES
-- ============================================

-- Brand overview
CREATE OR REPLACE VIEW v_brand_overview AS
SELECT 
    b.brand_official_name,
    b.brand_name_korean,
    b.brand_name_english,
    b.official_site_url,
    b.instagram_handle,
    COUNT(DISTINCT rw.id) as web_pages,
    COUNT(DISTINCT ri.id) as instagram_posts,
    COUNT(DISTINCT rn.id) as naver_posts,
    COUNT(DISTINCT rt.id) as tistory_posts,
    COUNT(DISTINCT cw.id) as cleaned_web_pages,
    COUNT(DISTINCT ci.id) as cleaned_instagram_posts,
    COUNT(DISTINCT cn.id) as cleaned_naver_posts,
    COUNT(DISTINCT ct.id) as cleaned_tistory_posts
FROM 01_brands b
LEFT JOIN raw_web_data rw ON b.brand_official_name = rw.brand_name
LEFT JOIN 03_raw_instagram_data ri ON b.brand_official_name = ri.brand_name
LEFT JOIN raw_naver_blog_data rn ON b.brand_official_name = rn.brand_name
LEFT JOIN raw_tistory_data rt ON b.brand_official_name = rt.brand_name
LEFT JOIN cleaned_web_text cw ON b.brand_official_name = cw.brand_name
LEFT JOIN `07_instagram_data` ci ON b.brand_official_name = ci.brand_name
LEFT JOIN `08_refined_naver_data` cn ON b.brand_official_name = cn.brand_name
LEFT JOIN `09_refined_tistory_data` ct ON b.brand_official_name = ct.brand_name
GROUP BY b.brand_official_name;

-- Processing status view
CREATE OR REPLACE VIEW v_processing_status AS
SELECT 
    b.brand_official_name,
    'web' as platform,
    COUNT(DISTINCT rw.id) as raw_count,
    COUNT(DISTINCT cw.id) as cleaned_count,
    COUNT(DISTINCT pk.id) as keywords_extracted,
    ROUND(COUNT(DISTINCT cw.id) * 100.0 / NULLIF(COUNT(DISTINCT rw.id), 0), 2) as cleaning_rate,
    ROUND(COUNT(DISTINCT pk.id) * 100.0 / NULLIF(COUNT(DISTINCT cw.id), 0), 2) as extraction_rate
FROM 01_brands b
LEFT JOIN raw_web_data rw ON b.brand_official_name = rw.brand_name
LEFT JOIN cleaned_web_text cw ON rw.id = cw.source_id
LEFT JOIN prompt_keywords pk ON cw.id = pk.cleaned_web_text_id
GROUP BY b.brand_official_name

UNION ALL

SELECT 
    b.brand_official_name,
    'instagram' as platform,
    COUNT(DISTINCT ri.id) as raw_count,
    COUNT(DISTINCT ci.id) as cleaned_count,
    0 as keywords_extracted,
    ROUND(COUNT(DISTINCT ci.id) * 100.0 / NULLIF(COUNT(DISTINCT ri.id), 0), 2) as cleaning_rate,
    0 as extraction_rate
FROM 01_brands b
LEFT JOIN 03_raw_instagram_data ri ON b.brand_official_name = ri.brand_name
LEFT JOIN `07_instagram_data` ci ON ri.id = ci.source_id
GROUP BY b.brand_official_name

UNION ALL

SELECT 
    b.brand_official_name,
    'naver' as platform,
    COUNT(DISTINCT rn.id) as raw_count,
    COUNT(DISTINCT cn.id) as cleaned_count,
    0 as keywords_extracted,
    ROUND(COUNT(DISTINCT cn.id) * 100.0 / NULLIF(COUNT(DISTINCT rn.id), 0), 2) as cleaning_rate,
    0 as extraction_rate
FROM 01_brands b
LEFT JOIN raw_naver_blog_data rn ON b.brand_official_name = rn.brand_name
LEFT JOIN `08_refined_naver_data` cn ON rn.id = cn.source_id
GROUP BY b.brand_official_name

UNION ALL

SELECT 
    b.brand_official_name,
    'tistory' as platform,
    COUNT(DISTINCT rt.id) as raw_count,
    COUNT(DISTINCT ct.id) as cleaned_count,
    0 as keywords_extracted,
    ROUND(COUNT(DISTINCT ct.id) * 100.0 / NULLIF(COUNT(DISTINCT rt.id), 0), 2) as cleaning_rate,
    0 as extraction_rate
FROM 01_brands b
LEFT JOIN raw_tistory_data rt ON b.brand_official_name = rt.brand_name
LEFT JOIN `09_refined_tistory_data` ct ON rt.id = ct.source_id
GROUP BY b.brand_official_name;

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 6. INITIAL DATA
-- ============================================

-- Insert migration history
INSERT INTO migration_history (version, migration_name, status, execution_time_ms)
VALUES ('3.0.0', 'Change to brand_official_name as primary key', 'completed', 0);

-- ============================================
-- Setup Complete!
-- ============================================