-- ============================================
-- Tracking and Monitoring Tables
-- ============================================
-- Description: Tables for system monitoring and cost tracking
-- Version: 1.0.0
-- ============================================

USE modular_agents_db;

-- ============================================
-- Table: processing_pipeline
-- Description: 전체 파이프라인 처리 추적
-- ============================================
CREATE TABLE IF NOT EXISTS processing_pipeline (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED NOT NULL,
    pipeline_id VARCHAR(36) DEFAULT (UUID()) COMMENT '파이프라인 UUID',
    pipeline_name VARCHAR(100) COMMENT '파이프라인 이름',
    
    -- 파이프라인 설정
    pipeline_type ENUM('full','incremental','keyword_only','geo_only','custom') DEFAULT 'full' COMMENT '파이프라인 타입',
    pipeline_config JSON COMMENT '파이프라인 설정',
    
    -- 상태 추적
    current_stage ENUM('initialized','crawling','refining','keyword_extraction','geo_optimization','completed') DEFAULT 'initialized' COMMENT '현재 단계',
    status ENUM('pending','running','completed','failed','cancelled','paused') DEFAULT 'pending' COMMENT '상태',
    
    -- 진행 상황
    total_stages INT DEFAULT 4 COMMENT '전체 단계 수',
    completed_stages INT DEFAULT 0 COMMENT '완료된 단계 수',
    progress_percentage FLOAT GENERATED ALWAYS AS (
        CASE 
            WHEN total_stages > 0 
            THEN (completed_stages / total_stages * 100)
            ELSE 0
        END
    ) STORED COMMENT '진행률(%)',
    
    -- 처리 통계
    total_items INT DEFAULT 0 COMMENT '전체 항목 수',
    processed_items INT DEFAULT 0 COMMENT '처리된 항목 수',
    failed_items INT DEFAULT 0 COMMENT '실패한 항목 수',
    skipped_items INT DEFAULT 0 COMMENT '건너뛴 항목 수',
    
    -- 에러 추적
    error_count INT DEFAULT 0 COMMENT '에러 수',
    last_error TEXT COMMENT '마지막 에러',
    error_details JSON COMMENT '에러 상세',
    
    -- 타임스탬프
    scheduled_at DATETIME COMMENT '예약 시각',
    started_at DATETIME COMMENT '시작 시각',
    completed_at DATETIME COMMENT '완료 시각',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE CASCADE,
    INDEX idx_pipeline_id (pipeline_id),
    INDEX idx_status (status),
    INDEX idx_current_stage (current_stage),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='처리 파이프라인';

-- ============================================
-- Table: stage_logs
-- Description: 각 단계별 상세 로그
-- ============================================
CREATE TABLE IF NOT EXISTS stage_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pipeline_id BIGINT UNSIGNED NOT NULL,
    stage_name VARCHAR(50) NOT NULL COMMENT '단계명',
    stage_type ENUM('crawl','refine','extract','optimize','custom') COMMENT '단계 타입',
    
    -- 상태
    status ENUM('started','running','completed','failed','skipped') DEFAULT 'started' COMMENT '상태',
    
    -- 통계
    input_count INT DEFAULT 0 COMMENT '입력 항목 수',
    output_count INT DEFAULT 0 COMMENT '출력 항목 수',
    error_count INT DEFAULT 0 COMMENT '에러 수',
    
    -- 성능
    processing_time_ms INT COMMENT '처리 시간(밀리초)',
    items_per_second FLOAT COMMENT '초당 처리 항목',
    
    -- 리소스 사용
    memory_usage_mb INT COMMENT '메모리 사용량(MB)',
    cpu_usage_percent FLOAT COMMENT 'CPU 사용률(%)',
    
    -- 로그
    log_messages JSON COMMENT '로그 메시지',
    error_details JSON COMMENT '에러 상세',
    
    started_at DATETIME COMMENT '시작 시각',
    completed_at DATETIME COMMENT '완료 시각',
    
    FOREIGN KEY (pipeline_id) REFERENCES processing_pipeline(id) ON DELETE CASCADE,
    INDEX idx_stage_name (stage_name),
    INDEX idx_status (status),
    INDEX idx_started (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='단계별 로그';

-- ============================================
-- Table: api_usage_tracking
-- Description: API 사용량 및 비용 추적
-- ============================================
CREATE TABLE IF NOT EXISTS api_usage_tracking (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED,
    pipeline_id BIGINT UNSIGNED,
    
    -- 서비스 정보
    service ENUM('openai','anthropic','instagram_api','naver_api','custom') NOT NULL COMMENT '서비스',
    service_endpoint VARCHAR(255) COMMENT 'API 엔드포인트',
    operation VARCHAR(100) NOT NULL COMMENT '작업 타입',
    model_name VARCHAR(50) COMMENT '모델명',
    
    -- 사용량
    request_count INT DEFAULT 1 COMMENT '요청 수',
    input_tokens INT COMMENT '입력 토큰',
    output_tokens INT COMMENT '출력 토큰',
    total_tokens INT GENERATED ALWAYS AS (COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)) STORED COMMENT '전체 토큰',
    
    -- 비용
    input_cost_usd DECIMAL(10,6) COMMENT '입력 비용(USD)',
    output_cost_usd DECIMAL(10,6) COMMENT '출력 비용(USD)',
    total_cost_usd DECIMAL(10,6) COMMENT '총 비용(USD)',
    cost_krw DECIMAL(10,2) COMMENT '원화 환산 비용',
    exchange_rate DECIMAL(10,4) COMMENT '환율',
    
    -- 성능
    response_time_ms INT COMMENT '응답 시간(밀리초)',
    status_code INT COMMENT 'HTTP 상태 코드',
    is_success BOOLEAN DEFAULT TRUE COMMENT '성공 여부',
    error_message TEXT COMMENT '에러 메시지',
    
    -- 메타데이터
    request_id VARCHAR(100) COMMENT '요청 ID',
    user_agent VARCHAR(255) COMMENT '사용자 에이전트',
    ip_address VARCHAR(45) COMMENT 'IP 주소',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE SET NULL,
    FOREIGN KEY (pipeline_id) REFERENCES processing_pipeline(id) ON DELETE SET NULL,
    INDEX idx_service (service),
    INDEX idx_operation (operation),
    INDEX idx_created (created_at),
    INDEX idx_brand_cost (brand_id, created_at),
    INDEX idx_success (is_success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API 사용 추적';

-- ============================================
-- Table: cost_summary
-- Description: 비용 요약 (일별/월별)
-- ============================================
CREATE TABLE IF NOT EXISTS cost_summary (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    brand_id INT UNSIGNED,
    summary_date DATE NOT NULL COMMENT '요약 날짜',
    summary_type ENUM('daily','weekly','monthly') DEFAULT 'daily' COMMENT '요약 타입',
    
    -- 서비스별 비용
    openai_cost_usd DECIMAL(10,4) DEFAULT 0 COMMENT 'OpenAI 비용',
    anthropic_cost_usd DECIMAL(10,4) DEFAULT 0 COMMENT 'Anthropic 비용',
    other_api_cost_usd DECIMAL(10,4) DEFAULT 0 COMMENT '기타 API 비용',
    total_cost_usd DECIMAL(10,4) DEFAULT 0 COMMENT '총 비용(USD)',
    total_cost_krw DECIMAL(10,2) DEFAULT 0 COMMENT '총 비용(KRW)',
    
    -- 사용량
    total_requests INT DEFAULT 0 COMMENT '총 요청 수',
    total_tokens INT DEFAULT 0 COMMENT '총 토큰 수',
    
    -- 작업별 분석
    crawling_cost DECIMAL(10,4) DEFAULT 0 COMMENT '크롤링 비용',
    refinement_cost DECIMAL(10,4) DEFAULT 0 COMMENT '정제 비용',
    extraction_cost DECIMAL(10,4) DEFAULT 0 COMMENT '추출 비용',
    optimization_cost DECIMAL(10,4) DEFAULT 0 COMMENT '최적화 비용',
    
    -- 통계
    avg_cost_per_request DECIMAL(10,6) COMMENT '요청당 평균 비용',
    avg_cost_per_token DECIMAL(10,8) COMMENT '토큰당 평균 비용',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE SET NULL,
    UNIQUE KEY uk_summary (brand_id, summary_date, summary_type),
    INDEX idx_date (summary_date),
    INDEX idx_type (summary_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='비용 요약';

-- ============================================
-- Table: system_metrics
-- Description: 시스템 성능 메트릭
-- ============================================
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    metric_timestamp DATETIME NOT NULL COMMENT '측정 시각',
    
    -- 시스템 리소스
    cpu_usage_percent FLOAT COMMENT 'CPU 사용률(%)',
    memory_usage_mb INT COMMENT '메모리 사용량(MB)',
    memory_total_mb INT COMMENT '전체 메모리(MB)',
    disk_usage_gb FLOAT COMMENT '디스크 사용량(GB)',
    disk_total_gb FLOAT COMMENT '전체 디스크(GB)',
    
    -- 데이터베이스
    db_connections_active INT COMMENT '활성 DB 연결',
    db_connections_idle INT COMMENT '유휴 DB 연결',
    db_query_avg_ms FLOAT COMMENT '평균 쿼리 시간(ms)',
    db_slow_queries INT COMMENT '느린 쿼리 수',
    
    -- 처리 통계
    active_pipelines INT COMMENT '활성 파이프라인',
    queued_jobs INT COMMENT '대기중인 작업',
    processing_rate FLOAT COMMENT '처리율(items/min)',
    error_rate FLOAT COMMENT '에러율(%)',
    
    -- API 상태
    api_availability FLOAT COMMENT 'API 가용성(%)',
    api_response_time_avg FLOAT COMMENT '평균 API 응답시간(ms)',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_timestamp (metric_timestamp),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='시스템 메트릭';

-- ============================================
-- Table: alerts
-- Description: 시스템 알림
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    alert_type ENUM('cost','performance','error','system','custom') NOT NULL COMMENT '알림 타입',
    severity ENUM('info','warning','error','critical') DEFAULT 'info' COMMENT '심각도',
    
    -- 알림 내용
    title VARCHAR(255) NOT NULL COMMENT '알림 제목',
    message TEXT NOT NULL COMMENT '알림 메시지',
    details JSON COMMENT '상세 정보',
    
    -- 관련 정보
    brand_id INT UNSIGNED COMMENT '관련 브랜드',
    pipeline_id BIGINT UNSIGNED COMMENT '관련 파이프라인',
    related_table VARCHAR(50) COMMENT '관련 테이블',
    related_id BIGINT COMMENT '관련 레코드 ID',
    
    -- 상태
    is_read BOOLEAN DEFAULT FALSE COMMENT '읽음 여부',
    is_resolved BOOLEAN DEFAULT FALSE COMMENT '해결 여부',
    resolved_by VARCHAR(100) COMMENT '해결자',
    resolved_at DATETIME COMMENT '해결 시각',
    resolution_notes TEXT COMMENT '해결 메모',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (brand_id) REFERENCES 01_brands(id) ON DELETE SET NULL,
    FOREIGN KEY (pipeline_id) REFERENCES processing_pipeline(id) ON DELETE SET NULL,
    INDEX idx_type_severity (alert_type, severity),
    INDEX idx_read (is_read),
    INDEX idx_resolved (is_resolved),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='시스템 알림';

-- ============================================
-- Views for monitoring
-- ============================================

-- Daily cost view
CREATE OR REPLACE VIEW v_daily_costs AS
SELECT 
    DATE(created_at) as date,
    brand_id,
    service,
    COUNT(*) as request_count,
    SUM(total_tokens) as total_tokens,
    SUM(total_cost_usd) as total_cost_usd,
    AVG(response_time_ms) as avg_response_time_ms
FROM api_usage_tracking
GROUP BY DATE(created_at), brand_id, service;

-- Pipeline status view
CREATE OR REPLACE VIEW v_pipeline_status AS
SELECT 
    p.id,
    p.pipeline_id,
    b.brand_official_name,
    p.pipeline_type,
    p.current_stage,
    p.status,
    p.progress_percentage,
    p.error_count,
    p.started_at,
    p.completed_at,
    TIMESTAMPDIFF(MINUTE, p.started_at, IFNULL(p.completed_at, NOW())) as duration_minutes
FROM processing_pipeline p
LEFT JOIN 01_brands b ON p.brand_id = b.id
ORDER BY p.created_at DESC;