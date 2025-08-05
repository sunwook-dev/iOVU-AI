-- ============================================
-- Migration History Table
-- ============================================
-- Description: Tracks database schema migrations
-- Version: 1.0.0
-- Date: 2025-07-25
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: migration_history
-- Description: 마이그레이션 실행 이력
-- ============================================
CREATE TABLE IF NOT EXISTS migration_history (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL COMMENT '마이그레이션 파일명',
    version VARCHAR(20) COMMENT '버전',
    description TEXT COMMENT '설명',
    
    -- 실행 정보
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '실행 시각',
    execution_time_ms INT COMMENT '실행 시간(밀리초)',
    executed_by VARCHAR(100) COMMENT '실행자',
    
    -- 상태 정보
    status ENUM('pending','running','completed','failed','rolled_back') DEFAULT 'completed' COMMENT '상태',
    error_message TEXT COMMENT '에러 메시지',
    
    -- 체크섬
    checksum VARCHAR(64) COMMENT '파일 체크섬 (SHA256)',
    
    -- 롤백 정보
    can_rollback BOOLEAN DEFAULT FALSE COMMENT '롤백 가능 여부',
    rollback_sql TEXT COMMENT '롤백 SQL',
    rolled_back_at DATETIME COMMENT '롤백 시각',
    
    UNIQUE KEY uk_migration_name (migration_name),
    INDEX idx_executed_at (executed_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='마이그레이션 히스토리';

-- 기존 마이그레이션 기록 추가
INSERT INTO migration_history (migration_name, version, description, status) VALUES
('00_database_init.sql', '1.0.0', 'Database initialization', 'completed'),
('01_core_tables.sql', '1.0.0', 'Core tables (01_brands, products)', 'completed'),
('02_raw_data_tables.sql', '1.0.0', 'Raw data tables', 'completed'),
('03_refined_tables.sql', '1.0.0', 'Refined data tables', 'completed'),
('04_keyword_tables.sql', '1.0.0', 'Keyword extraction tables', 'completed'),
('05_tracking_tables.sql', '1.0.0', 'Tracking and monitoring tables', 'completed'),
('06_cleaned_text_tables.sql', '1.0.0', 'Cleaned text tables', 'completed'),
('add_brand_name_korean.sql', '1.0.0', 'Add Korean brand name column', 'completed')
ON DUPLICATE KEY UPDATE status = 'completed';