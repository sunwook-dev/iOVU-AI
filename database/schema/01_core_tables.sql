-- ============================================
-- Core Tables: Brands, Channels, Products
-- ============================================
-- Description: Core business entities for brand management
-- Version: 1.0.0
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: 01_brands
-- Description: 브랜드 기본 정보
-- ============================================
CREATE TABLE IF NOT EXISTS 01_brands (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_official_name VARCHAR(255) NOT NULL UNIQUE COMMENT '브랜드 공식명 (영/한글)',
    hq_country CHAR(2) COMMENT 'ISO-2 국가 코드',
    mission_tagline VARCHAR(255) COMMENT '브랜드 슬로건/미션',
    primary_demographics JSON COMMENT '핵심 타겟 인구통계 {"gender":"F","age":"18-29"}',
    geographic_targets JSON COMMENT '주요 판매국가 배열 ["KR","JP","US"]',
    brand_personality JSON COMMENT '브랜드 개성 키워드 ["Playful","Vintage"]',
    brand_story TEXT COMMENT '브랜드 스토리/철학',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_brand_name (brand_official_name),
    INDEX idx_country (hq_country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='브랜드 기본 정보';

-- ============================================
-- Table: brand_channels
-- Description: 브랜드 디지털 & 커머스 채널
-- ============================================
CREATE TABLE IF NOT EXISTS brand_channels (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    official_site_url VARCHAR(500) COMMENT '공식 웹사이트',
    eshop_urls JSON COMMENT '이커머스 URL 배열 (쿠팡, Amazon 등)',
    instagram_handle VARCHAR(100) COMMENT 'Instagram @handle',
    musinsa_shop_url VARCHAR(500) COMMENT '무신사 스토어 URL',
    naver_shopping_url VARCHAR(500) COMMENT '네이버 쇼핑 브랜드관 URL',
    tiktok_handle VARCHAR(100) COMMENT 'TikTok @handle',
    youtube_channel_url VARCHAR(500) COMMENT 'YouTube 채널 URL',
    kakao_channel_id VARCHAR(100) COMMENT '카카오톡 채널 ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_brand_channel (brand_id),
    INDEX idx_instagram (instagram_handle),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='브랜드 채널 정보';

-- ============================================
-- Table: products
-- Description: 개별 제품 정보
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    product_name VARCHAR(255) NOT NULL COMMENT '제품명',
    product_code VARCHAR(100) COMMENT '제품 코드/SKU',
    core_categories JSON COMMENT '제품 카테고리 ["Tops","Outerwear"]',
    materials_focus JSON COMMENT '주요 소재 배열',
    design_elements JSON COMMENT '디자인 요소 (패턴, 실루엣 등)',
    season ENUM('SS','FW','Spring','Summer','Autumn','Winter','All') COMMENT '시즌',
    colorways JSON COMMENT '출시 색상 배열',
    price DECIMAL(10,2) COMMENT '정가',
    currency CHAR(3) DEFAULT 'KRW' COMMENT 'ISO-4217 통화 코드',
    sale_price DECIMAL(10,2) COMMENT '할인가',
    discount_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN price > 0 AND sale_price IS NOT NULL 
            THEN ((price - sale_price) / price * 100)
            ELSE NULL
        END
    ) STORED COMMENT '할인율(%)',
    sizes_available JSON COMMENT '사이즈 옵션 ["XS","S","M","L"]',
    inventory_status ENUM('In Stock','Low','Sold Out','Pre-Order') DEFAULT 'In Stock' COMMENT '재고 상태',
    image_urls JSON COMMENT '제품 이미지 URL 배열',
    product_json JSON COMMENT '크롤링된 원본 제품 정보',
    source_url VARCHAR(500) COMMENT '제품 수집 출처 URL',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    registered_at DATE COMMENT '제품 등록일',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_brand_product (brand_id, product_name),
    INDEX idx_product_code (product_code),
    INDEX idx_season (season),
    INDEX idx_inventory (inventory_status),
    INDEX idx_price (price, sale_price),
    INDEX idx_active_status (is_active, brand_id),
    FULLTEXT idx_product_search (product_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='제품 정보';

-- ============================================
-- Triggers for data integrity
-- ============================================

-- Trigger to validate price before insert
DELIMITER $$
CREATE TRIGGER validate_product_price_insert
BEFORE INSERT ON products
FOR EACH ROW
BEGIN
    IF NEW.price < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Product price cannot be negative';
    END IF;
    
    IF NEW.sale_price IS NOT NULL AND NEW.sale_price > NEW.price THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Sale price cannot be higher than regular price';
    END IF;
END$$
DELIMITER ;

-- Trigger to validate price before update
DELIMITER $$
CREATE TRIGGER validate_product_price_update
BEFORE UPDATE ON products
FOR EACH ROW
BEGIN
    IF NEW.price < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Product price cannot be negative';
    END IF;
    
    IF NEW.sale_price IS NOT NULL AND NEW.sale_price > NEW.price THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Sale price cannot be higher than regular price';
    END IF;
END$$
DELIMITER ;