# Schema Directory

이 디렉토리의 개별 스키마 파일들은 이전 버전(v2.x)과의 호환성을 위해 유지됩니다.

## ⚠️ 중요 안내

**v3.0.0부터는 `setup_database.sql` 파일을 사용하세요!**

- 전체 스키마: `/database/setup_database.sql`
- 마이그레이션: `/database/migrations/migrate_to_brand_name_key.sql`

## 파일 목록 (Legacy)

- `00_database_init.sql` - 데이터베이스 초기화
- `01_core_tables.sql` - 핵심 테이블 (01_brands, products 등)
- `02_raw_data_tables.sql` - 원본 데이터 테이블
- `03_refined_tables.sql` - 정제된 데이터 테이블
- `04_keyword_tables.sql` - 키워드 관련 테이블
- `05_tracking_tables.sql` - 추적 및 모니터링 테이블
- `06_cleaned_text_tables.sql` - 정제된 텍스트 테이블
- `07_migration_history.sql` - 마이그레이션 기록

## 주의사항

이 파일들은 `brand_id (INT)`를 사용하는 구버전 스키마입니다.
새로운 프로젝트는 반드시 `setup_database.sql`을 사용하세요!