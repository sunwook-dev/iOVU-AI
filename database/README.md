# 📊 Modular Agents Database

브랜드 분석을 위한 통합 데이터베이스 시스템 (v3.0.0)

## 🚀 빠른 시작 (1분 설정)

### 방법 1: 자동 설정 (권장)
```bash
# 1. 데이터베이스 폴더로 이동
cd database/

# 2. 자동 설정 실행
python quick_setup.py

# 3. MySQL 정보 입력
Host [localhost]: 
Port [3306]: 
User [root]: 
Password: ****
```

### 방법 2: 수동 설정
```bash
# 1. MySQL 접속
mysql -u root -p

# 2. SQL 파일 실행
mysql> source setup_database.sql

# 3. 확인
mysql> USE modular_agents_db;
mysql> SHOW TABLES;
```

### 방법 3: 명령줄 한 줄 설정
```bash
python quick_setup.py --host localhost --user root --password yourpass
```

---

## 🔄 중요 변경사항 (v3.0.0)

### 주요 변경점
- **PRIMARY KEY 변경**: `01_brands` 테이블의 기본키가 `id (INT)`에서 `brand_official_name (VARCHAR)`으로 변경
- **외래키 변경**: 모든 테이블의 `brand_id` 컬럼이 `brand_name`으로 변경
- **CASCADE 업데이트**: 브랜드명 변경 시 모든 관련 데이터 자동 업데이트

### 기존 데이터 마이그레이션
```bash
# 백업 필수!
mysqldump -u root -p modular_agents_db > backup_before_migration.sql

# 마이그레이션 실행
mysql -u root -p modular_agents_db < migrations/migrate_to_brand_name_key.sql
```

---

## 📁 폴더 구조

```
database/
├── setup_database.sql      # 전체 스키마 (v3.0.0)
├── quick_setup.py         # 자동 설정 스크립트
├── README.md             # 이 문서
├── .env.example          # 환경 변수 예제
├── config.py            # 데이터베이스 설정
├── init_db.py           # 초기화 스크립트
├── migrations/          # 마이그레이션 스크립트
│   └── migrate_to_brand_name_key.sql
├── queries/             # 쿼리 헬퍼 함수
└── utils/               # 유틸리티 함수
```

---

## 🗄️ 데이터베이스 구조

### 1. 핵심 테이블

#### 🏢 01_brands (변경됨)
브랜드 기본 정보
```sql
- brand_official_name  # PRIMARY KEY (변경!)
- brand_name_korean    # 한글명
- brand_name_english   # 영문명
- official_site_url    # 공식 웹사이트
- instagram_handle     # Instagram 계정
- address             # 주소
- founding_year       # 설립 연도
- hq_country         # 본사 국가
```

### 2. 원본 데이터 테이블

#### 🌐 raw_web_data
웹 크롤링 원본 데이터
```sql
- id                 # 자동 증가 ID
- brand_name         # 브랜드명 (FK) - 변경!
- url               # 페이지 URL
- raw_html          # HTML 원본
- page_title        # 페이지 제목
- meta_data         # 메타데이터
```

#### 📸 03_raw_instagram_data
인스타그램 포스트 데이터
```sql
- id                # 자동 증가 ID
- brand_name        # 브랜드명 (FK) - 변경!
- post_id           # 포스트 ID
- caption           # 캡션
- hashtags          # 해시태그
- like_count        # 좋아요 수
```

### 3. 정제된 데이터 테이블

#### 📝 cleaned_web_text
정제된 웹 텍스트
```sql
- id                # 자동 증가 ID
- brand_name        # 브랜드명 (FK) - 변경!
- cleaned_text      # 정제된 텍스트
- word_count        # 단어 수
- quality_score     # 품질 점수
```

### 4. 키워드 테이블

#### 🔑 prompt_keywords
추출된 키워드
```sql
- id                # 자동 증가 ID
- brand_name        # 브랜드명 (FK) - 변경!
- entities          # 개체명 (JSON)
- concepts          # 개념 (JSON)
- relationships     # 관계 (JSON)
```

---

## 🔧 환경 설정

### .env 파일 설정
```bash
# 데이터베이스
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=modular_agents_db

# API 키
OPENAI_API_KEY=sk-...
```

---

## 💻 사용 예제

### Python에서 연결 (새로운 방식)
```python
from database.utils import get_db

# 연결
db = get_db()

# 브랜드 조회 (brand_name 사용)
01_brands = db.execute("SELECT * FROM 01_brands WHERE brand_official_name = %s", ("Nike",))

# 데이터 삽입
db.insert('raw_web_data', {
    'brand_name': 'Nike',  # brand_id 대신 brand_name 사용!
    'url': 'https://nike.com',
    'raw_html': '<html>...'
})
```

### 트랜잭션 사용
```python
with db.transaction():
    # 브랜드 추가
    db.insert('01_brands', {
        'brand_official_name': 'NewBrand',
        'official_site_url': 'https://newbrand.com'
    })
    
    # 관련 데이터 추가
    db.insert('raw_web_data', {
        'brand_name': 'NewBrand',  # 같은 이름 사용
        'url': 'https://newbrand.com'
    })
```

---

## 📊 유용한 쿼리

### 브랜드별 데이터 통계
```sql
SELECT * FROM v_brand_overview;
```

### 처리 현황 보기
```sql
SELECT * FROM v_processing_status;
```

### 특정 브랜드 데이터 조회
```sql
SELECT * FROM raw_web_data 
WHERE brand_name = 'Nike' 
ORDER BY crawled_at DESC;
```

---

## 🔄 마이그레이션

### v2.x에서 v3.0으로 업그레이드
```bash
# 1. 백업
mysqldump -u root -p modular_agents_db > backup_v2.sql

# 2. 마이그레이션 실행
mysql -u root -p modular_agents_db < migrations/migrate_to_brand_name_key.sql

# 3. 확인
mysql -u root -p -e "USE modular_agents_db; DESCRIBE 01_brands;"
```

### 롤백 (필요시)
```bash
# 백업에서 복원
mysql -u root -p modular_agents_db < backup_v2.sql
```

---

## 🐛 문제 해결

### 외래키 제약 오류
```sql
-- 임시로 외래키 체크 비활성화
SET FOREIGN_KEY_CHECKS = 0;
-- 작업 수행
SET FOREIGN_KEY_CHECKS = 1;
```

### 브랜드명 변경
```sql
-- CASCADE UPDATE로 자동 변경됨
UPDATE 01_brands 
SET brand_official_name = 'NewName' 
WHERE brand_official_name = 'OldName';
```

### 한글 깨짐
```sql
ALTER DATABASE modular_agents_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

---

## 📈 데이터베이스 최적화

### 인덱스 확인
```sql
SHOW INDEX FROM raw_web_data;
```

### 쿼리 성능 분석
```sql
EXPLAIN SELECT * FROM cleaned_web_text 
WHERE brand_name = 'Nike' 
AND word_count > 100;
```

### 정기 정리
```sql
-- 30일 이상된 로그 삭제
DELETE FROM cleaning_logs 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- 테이블 최적화
OPTIMIZE TABLE raw_web_data;
```

---

## 📝 라이선스

MIT License

---

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request