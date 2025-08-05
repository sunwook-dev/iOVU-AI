# 🔄 Database Migration Guide v3.0

## 개요

Modular Agents 데이터베이스가 v3.0으로 업그레이드되면서 주요 구조 변경이 있습니다.

### 주요 변경사항
- `01_brands` 테이블의 PRIMARY KEY가 `id (INT)`에서 `brand_official_name (VARCHAR)`으로 변경
- 모든 테이블의 `brand_id` 컬럼이 `brand_name`으로 변경
- CASCADE UPDATE 지원으로 브랜드명 변경 시 자동 업데이트

## 마이그레이션 단계별 가이드

### 1. 사전 준비

#### 데이터베이스 백업 (필수!)
```bash
# 전체 데이터베이스 백업
mysqldump -u root -p modular_agents_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 또는 특정 테이블만 백업
mysqldump -u root -p modular_agents_db 01_brands raw_web_data > backup_core_tables.sql
```

#### 현재 상태 확인
```sql
-- 브랜드 목록 확인
SELECT id, brand_official_name FROM 01_brands;

-- 데이터 건수 확인
SELECT 
    (SELECT COUNT(*) FROM raw_web_data) as web_count,
    (SELECT COUNT(*) FROM 03_raw_instagram_data) as instagram_count,
    (SELECT COUNT(*) FROM cleaned_web_text) as cleaned_count;
```

### 2. 마이그레이션 실행

#### 자동 마이그레이션
```bash
cd /path/to/modular_agents/database
mysql -u root -p modular_agents_db < migrations/migrate_to_brand_name_key.sql
```

#### 수동 마이그레이션 (단계별)
```sql
-- 1. 외래키 체크 비활성화
SET FOREIGN_KEY_CHECKS = 0;

-- 2. brand_name 컬럼 추가
ALTER TABLE raw_web_data ADD COLUMN brand_name VARCHAR(255) AFTER brand_id;

-- 3. 데이터 복사
UPDATE raw_web_data rwd
JOIN 01_brands b ON rwd.brand_id = b.id
SET rwd.brand_name = b.brand_official_name;

-- 4. 외래키 재설정
ALTER TABLE raw_web_data 
DROP FOREIGN KEY raw_web_data_ibfk_1,
DROP COLUMN brand_id,
ADD CONSTRAINT fk_raw_web_brand FOREIGN KEY (brand_name) 
REFERENCES 01_brands(brand_official_name) ON DELETE CASCADE ON UPDATE CASCADE;

-- 5. 외래키 체크 활성화
SET FOREIGN_KEY_CHECKS = 1;
```

### 3. 마이그레이션 검증

```sql
-- 테이블 구조 확인
DESCRIBE 01_brands;
DESCRIBE raw_web_data;

-- 데이터 무결성 확인
SELECT COUNT(*) FROM raw_web_data WHERE brand_name IS NULL;

-- 외래키 제약 확인
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'modular_agents_db'
AND REFERENCED_TABLE_NAME = '01_brands';
```

### 4. 애플리케이션 코드 업데이트

#### Python 코드 변경 예시

**Before (v2.x):**
```python
# 브랜드 ID로 조회
brand_id = 1
db.execute("SELECT * FROM raw_web_data WHERE brand_id = %s", (brand_id,))

# 데이터 삽입
db.insert('raw_web_data', {
    'brand_id': brand_id,
    'url': 'https://example.com'
})
```

**After (v3.0):**
```python
# 브랜드명으로 조회
brand_name = "Nike"
db.execute("SELECT * FROM raw_web_data WHERE brand_name = %s", (brand_name,))

# 데이터 삽입
db.insert('raw_web_data', {
    'brand_name': brand_name,  # brand_id 대신 brand_name 사용
    'url': 'https://example.com'
})
```

#### 쿼리 헬퍼 업데이트

```python
# database/queries/brand_queries.py
class BrandQueries:
    @staticmethod
    def get_brand(brand_name: str):
        """브랜드명으로 조회"""
        db = get_db()
        return db.execute_one(
            "SELECT * FROM 01_brands WHERE brand_official_name = %s",
            (brand_name,)
        )
```

### 5. 롤백 절차 (필요시)

```bash
# 백업에서 복원
mysql -u root -p modular_agents_db < backup_20240725_120000.sql

# 또는 역마이그레이션 스크립트 실행
mysql -u root -p modular_agents_db < migrations/rollback_to_brand_id.sql
```

## 주의사항

### 1. 브랜드명 규칙
- 브랜드명은 이제 PRIMARY KEY이므로 중복 불가
- 대소문자 구분 (Nike ≠ nike)
- 최대 255자 제한
- NULL 불가

### 2. 성능 고려사항
- VARCHAR PRIMARY KEY는 INT보다 약간 느릴 수 있음
- 적절한 인덱스 설정 필요
- 브랜드명이 자주 변경되는 경우 CASCADE UPDATE 부하 고려

### 3. 호환성
- 기존 brand_id를 사용하는 코드는 모두 수정 필요
- API 응답 형식 변경 가능
- 외부 시스템 연동 확인 필요

## 문제 해결

### 외래키 제약 오류
```sql
-- Error: Cannot add or update a child row
-- Solution: 브랜드가 존재하는지 확인
SELECT * FROM 01_brands WHERE brand_official_name = 'YourBrand';
```

### 중복 키 오류
```sql
-- Error: Duplicate entry for key 'PRIMARY'
-- Solution: 브랜드명 중복 확인
SELECT brand_official_name, COUNT(*) 
FROM 01_brands 
GROUP BY brand_official_name 
HAVING COUNT(*) > 1;
```

### 데이터 타입 불일치
```sql
-- Error: Data too long for column
-- Solution: 데이터 길이 확인
SELECT brand_official_name, LENGTH(brand_official_name) 
FROM 01_brands 
WHERE LENGTH(brand_official_name) > 255;
```

## 지원

문제 발생 시:
1. 에러 메시지와 함께 이슈 등록
2. 백업 파일 보관 확인
3. 마이그레이션 로그 첨부