# 🚀 Modular Agents - 브랜드 분석 AI 시스템

브랜드의 디지털 콘텐츠를 수집, 분석, 최적화하는 모듈식 AI 에이전트 시스템

## 📋 목차
- [시스템 개요](#-시스템-개요)
- [주요 기능](#-주요-기능)
- [빠른 시작](#-빠른-시작)
- [프로젝트 구조](#-프로젝트-구조)
- [에이전트 목록](#-에이전트-목록)
- [데이터베이스](#-데이터베이스)
- [개발 가이드](#-개발-가이드)

## 🎯 시스템 개요

Modular Agents는 브랜드의 온라인 존재감을 종합적으로 분석하고 최적화하는 AI 기반 시스템입니다. 각 에이전트는 특정 작업에 특화되어 있으며, 파이프라인 방식으로 연결되어 데이터를 순차적으로 처리합니다.

### 핵심 가치
- **모듈화**: 각 에이전트가 독립적으로 개발, 테스트, 배포 가능
- **확장성**: 새로운 플랫폼이나 기능을 쉽게 추가
- **자동화**: 데이터 수집부터 분석까지 완전 자동화
- **AI 기반**: OpenAI API를 활용한 고급 콘텐츠 분석

## ✨ 주요 기능

### 1. 데이터 수집
- 🌐 웹사이트 크롤링 (동적/정적 페이지)
- 📸 Instagram 포스트 및 스토리 수집
- 📝 네이버/티스토리 블로그 크롤링
- 🔍 검색 쿼리 및 트렌드 분석

### 2. 데이터 정제
- 🧹 HTML 클리닝 및 텍스트 추출
- 🔄 중복 제거 및 정규화
- 📊 품질 점수 계산
- 🏷️ 메타데이터 추출

### 3. AI 분석
- 🔑 키워드 추출 및 클러스터링
- 📈 감성 분석 및 트렌드 예측
- 🎯 타겟 고객 분석
- 💡 콘텐츠 인사이트 생성

### 4. 최적화
- 🚀 SEO/GEO 최적화
- 📱 소셜 미디어 최적화
- ✍️ AI 콘텐츠 생성
- 📊 성과 측정 및 리포팅

## 🚀 빠른 시작

### 1. 요구사항
- Python 3.8+
- MySQL 5.7+
- Redis (선택사항)
- 8GB+ RAM

### 2. 설치

```bash
# 1. 저장소 클론
git clone [repository-url]
cd modular_agents

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -e .
# 또는
pip install -r requirements.txt

# 4. 환경변수 설정
cp database/.env.example .env
# .env 파일 편집하여 API 키 등 설정
```

### 3. 데이터베이스 설정

```bash
# 자동 설정 (권장)
cd database
python quick_setup.py

# 또는 수동 설정
mysql -u root -p < database/setup_database.sql
```

### 4. 첫 실행

```bash
# 브랜드 등록
mysql -u root -p modular_agents_db
> INSERT INTO brands (brand_official_name, official_site_url, instagram_handle) 
> VALUES ('Nike', 'https://nike.com', '@nike');

# 웹 크롤러 실행
python agent_02_web_crawler/main.py --brand-id 1

# 텍스트 정제
python agent_06_web_refiner/main.py --brand-id 1

# 키워드 추출
python agent_08_keyword_extractor/main.py --brand-id 1
```

## 📁 프로젝트 구조

```
modular_agents/
├── database/               # 데이터베이스 관련
│   ├── setup_database.sql  # 전체 스키마
│   ├── quick_setup.py      # 자동 설정 스크립트
│   ├── config.py           # DB 설정
│   ├── queries/            # 쿼리 헬퍼
│   └── utils/              # 유틸리티
│
├── agent_02_web_crawler/   # 웹 크롤러
├── agent_03_instagram/     # Instagram 크롤러
├── agent_04_text_cleaner/  # 텍스트 정제
├── agent_06_web_refiner/   # 웹 데이터 정제
├── agent_08_keyword_extractor/  # 키워드 추출
│
├── requirements.txt        # 전체 의존성
├── setup.py               # 패키지 설정
├── .gitignore             # Git 제외 파일
└── README.md              # 이 문서
```

## 🤖 에이전트 목록

### 데이터 수집 에이전트
| 에이전트 | 설명 | 주요 기능 |
|---------|------|----------|
| 02_web_crawler | 웹사이트 크롤러 | 동적/정적 페이지, 제품 정보, 이미지 |
| 03_instagram | Instagram 크롤러 | 포스트, 스토리, 릴스, 해시태그 |
| 04_naver | 네이버 블로그 크롤러 | 블로그 포스트, 리뷰, 이미지 |
| 05_tistory | 티스토리 크롤러 | 기술 블로그, 리뷰 |

### 데이터 정제 에이전트
| 에이전트 | 설명 | 주요 기능 |
|---------|------|----------|
| 06_web_refiner | 웹 데이터 정제 | HTML 클리닝, 구조화, 품질 평가 |
| 07_instagram_refiner | Instagram 정제 | 캡션 정제, 해시태그 분석 |

### 분석 에이전트
| 에이전트 | 설명 | 주요 기능 |
|---------|------|----------|
| 08_keyword_extractor | 키워드 추출 | TF-IDF, 의미 분석, 클러스터링 |
| 10_prompt_generator | 프롬프트 생성 | AI 콘텐츠 생성용 프롬프트 |

## 💾 데이터베이스

### 주요 테이블

#### brands (브랜드)
```sql
- id: 브랜드 ID
- brand_official_name: 공식명
- brand_name_korean: 한글명
- brand_name_english: 영문명
- official_site_url: 웹사이트
- instagram_handle: Instagram
- address: 주소
```

#### raw_web_data (웹 원본)
```sql
- url: 페이지 URL
- raw_html: HTML 원본
- page_title: 제목
- meta_data: 메타데이터
- crawled_at: 수집 시간
```

#### cleaned_web_text (정제된 텍스트)
```sql
- cleaned_text: 정제된 텍스트
- word_count: 단어 수
- quality_score: 품질 점수
```

#### extracted_keywords (키워드)
```sql
- keyword: 키워드
- keyword_type: 유형
- relevance_score: 관련성
- frequency: 빈도
```

### 데이터베이스 관리

```bash
# 백업
mysqldump -u root -p modular_agents_db > backup.sql

# 복원
mysql -u root -p modular_agents_db < backup.sql

# 상태 확인
mysql -u root -p modular_agents_db -e "SELECT * FROM v_brand_overview;"
```

## 🔧 개발 가이드

### 새 에이전트 추가

1. 디렉토리 생성
```bash
mkdir agent_XX_new_agent
cd agent_XX_new_agent
```

2. 기본 구조
```
agent_XX_new_agent/
├── __init__.py
├── main.py
├── config.py
├── requirements.txt
├── README.md
└── processors/
    └── __init__.py
```

3. 데이터베이스 연결
```python
from database.utils import get_db

db = get_db()
results = db.execute("SELECT * FROM brands")
```

### 코딩 규칙
- PEP 8 스타일 가이드 준수
- 타입 힌트 사용
- 독스트링 작성
- 단위 테스트 포함

### 환경 변수
```env
# 필수
OPENAI_API_KEY=sk-...
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=modular_agents_db

# 선택
LOG_LEVEL=INFO
MAX_WORKERS=4
CACHE_TTL=3600
```

## 📊 모니터링

### 로그 확인
```bash
# 전체 로그
tail -f agent_*/logs/*.log

# 특정 에이전트
tail -f agent_02_web_crawler/logs/crawler.log
```

### 성능 메트릭
```sql
-- 처리 현황
SELECT * FROM v_processing_status;

-- API 사용량
SELECT * FROM api_usage_tracking 
WHERE DATE(called_at) = CURDATE();
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🆘 문제 해결

### 일반적인 문제

1. **MySQL 연결 오류**
   ```bash
   # MySQL 서버 확인
   sudo service mysql status
   
   # 권한 확인
   mysql -u root -p -e "SHOW GRANTS;"
   ```

2. **OpenAI API 오류**
   ```bash
   # API 키 확인
   echo $OPENAI_API_KEY
   
   # 사용량 확인
   curl https://api.openai.com/v1/usage
   ```

3. **메모리 부족**
   ```bash
   # 배치 크기 줄이기
   export BATCH_SIZE=10
   ```

### 지원

- 📧 이메일: support@example.com
- 💬 Slack: #modular-agents
- 📚 문서: [Wiki](https://github.com/yourrepo/wiki)

---

© 2024 Modular Agents. All rights reserved.