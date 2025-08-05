# Tistory Blog Crawler Agent

티스토리 블로그 크롤링 에이전트 v2.0

## 개요

이 에이전트는 브랜드명을 기반으로 티스토리 블로그를 검색하고 관련 포스트들을 수집합니다.
구글 검색 봇 탐지를 우회하기 위해 undetected-chromedriver를 사용하며, 
최소 이미지 개수 조건을 만족하는 포스트만 저장합니다.

## 주요 변경사항 (v2.0)

- **Selenium + undetected-chromedriver 도입**: 구글 봇 탐지 우회
- **대체 검색 엔진 지원**: Daum, Naver 검색 폴백
- **향상된 URL 필터링**: 중복 제거 및 유효성 검증 강화

## 주요 기능

- 브랜드명 기반 티스토리 블로그 검색
- 봇 탐지 우회 기능 (undetected-chromedriver)
- 포스트 내용, 이미지, 태그, 카테고리 등 상세 정보 수집
- 최소 이미지 개수 필터링 (기본: 5개 이상)
- 중복 포스트 자동 제거
- MySQL 데이터베이스 저장

## 설치 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# Chrome 브라우저가 설치되어 있어야 합니다
# Mac: brew install --cask google-chrome
# Ubuntu: sudo apt-get install google-chrome-stable
```

## 환경 설정

상위 디렉토리의 `.env` 파일에 다음 설정 추가:

```env
# Tistory Crawler Settings
TISTORY_MAX_PAGES=10         # 브랜드당 최대 검색 페이지 수
TISTORY_POSTS_PER_PAGE=20    # 페이지당 포스트 수
TISTORY_CRAWL_DELAY=0.5      # 포스트 간 대기 시간 (초)
TISTORY_PAGE_DELAY=1.0       # 페이지 간 대기 시간 (초)
TISTORY_REQUEST_TIMEOUT=10   # 요청 타임아웃 (초)
TISTORY_MIN_IMAGES=5         # 최소 이미지 개수

# Chrome Driver Settings
TISTORY_USE_HEADLESS=false   # 헤드리스 모드 사용 여부
TISTORY_CHROME_WAIT=3        # Chrome 로딩 대기 시간 (초)

# Search Engine Settings
TISTORY_SEARCH_ENGINE=google # 기본 검색 엔진 (google/daum/naver)
TISTORY_FALLBACK_SEARCH=true # 대체 검색 사용 여부
```

## 사용 방법

### 특정 브랜드 크롤링

```bash
python run_crawler.py --brand-id 1
```

### 모든 브랜드 크롤링

```bash
python run_crawler.py --all
```

### 커스텀 설정으로 크롤링

```bash
python run_crawler.py --brand-id 1 --max-pages 5
```

## 크롤링 프로세스

1. **브랜드 정보 조회**: 데이터베이스에서 브랜드 정보 가져오기
2. **검색 수행**:
   - Primary: Selenium + Chrome으로 구글 검색 (`"브랜드명" site:tistory.com`)
   - Fallback: Daum/Naver 검색 API 사용
3. **URL 필터링**: 
   - 티스토리 도메인 확인
   - 카테고리/태그 페이지 제외
   - 중복 URL 제거
4. **포스트 크롤링**: 각 URL의 상세 내용 수집
5. **이미지 필터링**: 최소 이미지 개수 체크
6. **중복 체크**: blog_name과 post_id로 중복 확인
7. **데이터 저장**: MySQL 데이터베이스에 저장

## 검색 방식

### 1. Google 검색 (Primary)
- undetected-chromedriver를 사용하여 봇 탐지 우회
- 실제 브라우저처럼 동작하여 정확한 검색 결과 획득
- CAPTCHA 발생 시 자동으로 대체 검색으로 전환

### 2. Daum 검색 (Fallback)
- Daum 블로그 검색 API 활용
- 티스토리 블로그 필터링
- 구글 차단 시 자동 전환

### 3. Naver 검색 (Secondary Fallback)
- Naver 블로그 검색 활용
- 추가 검색 결과 보충

## 크롤링 결과 예시

```
🚀 티스토리 블로그 크롤러 시작
⏰ 시작 시간: 2025-07-22 18:57:05
📷 최소 이미지 개수: 3개
------------------------------------------------------------
🔍 브랜드 정보:
   - ID: 1
   - 이름: Uniform Bridge
   - 카테고리: ['Fashion', 'Contemporary', 'Streetwear']

페이지 1 검색 중...
  Selenium으로 구글 검색 시작...
  Selenium 검색에서 12개 URL 발견

크롤링 중 [1]: https://simonprankln.tistory.com/26...
  -> 저장 완료: 유니폼 브릿지 (Uniform Bridge) 21 s/s 룩북...

크롤링 완료!
- 크롤링한 포스트: 21개
- 저장된 포스트: 16개
```

## 데이터베이스 구조

### 05_raw_tistory_data 테이블

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | BIGINT | 자동 증가 PK |
| brand_id | INT | 브랜드 ID (FK) |
| blog_url | VARCHAR(500) | 포스트 URL |
| blog_name | VARCHAR(100) | 블로그명 |
| post_id | VARCHAR(50) | 포스트 ID |
| post_title | VARCHAR(500) | 포스트 제목 |
| post_content | LONGTEXT | HTML 형식 본문 |
| post_summary | TEXT | 텍스트 요약 (500자) |
| author | VARCHAR(100) | 작성자 |
| category | VARCHAR(100) | 카테고리 |
| tags | JSON | 태그 목록 |
| images | JSON | 이미지 URL 목록 |
| posted_at | DATETIME | 작성일 |
| raw_data | JSON | 원본 메타데이터 |
| crawler_version | VARCHAR(20) | 크롤러 버전 |
| created_at | TIMESTAMP | DB 저장 시간 |

## 주요 클래스

### TistoryCrawler

- `search_tistory()`: 메인 검색 함수 (자동 폴백)
- `search_tistory_selenium()`: Selenium 기반 구글 검색
- `search_tistory_direct()`: 대체 검색 엔진 사용
- `get_post_content()`: 포스트 상세 내용 추출
- `extract_blog_info()`: URL에서 블로그명과 포스트 ID 추출
- `check_duplicate()`: 중복 포스트 체크
- `save_to_database()`: 데이터베이스 저장
- `crawl_brand_blogs()`: 브랜드별 크롤링 메인 로직

## 특징

- **봇 탐지 우회**: undetected-chromedriver로 구글 검색 가능
- **다중 검색 엔진**: 구글 차단 시 자동으로 대체 검색 사용
- **스마트 필터링**: 이미지 개수 기반 품질 필터링
- **강력한 파싱**: 다양한 티스토리 테마 지원
- **모바일 URL 처리**: 자동으로 데스크톱 버전으로 변환

## 에러 처리

- Chrome 드라이버 오류 시 대체 검색으로 자동 전환
- 네트워크 오류 시 재시도
- 파싱 실패 시 다음 포스트로 진행
- 중복 포스트는 자동으로 건너뛰기
- 상세한 오류 로그 출력

## 문제 해결

### Chrome 드라이버 오류
```
Message: unknown error: Chrome failed to start
```
해결: Chrome 브라우저가 설치되어 있는지 확인

### 구글 검색 차단
```
⚠️ 구글에서 비정상적인 트래픽으로 감지됨
```
해결: 자동으로 Daum/Naver 검색으로 전환됨

### 이미지 부족
```
-> 이미지 부족 (2개)
```
해결: TISTORY_MIN_IMAGES 환경변수로 최소 이미지 수 조정

## 참고 사항

- Chrome 브라우저 필수 설치
- 대량 크롤링 시 IP 차단 주의
- 적절한 딜레이 설정으로 서버 부하 방지
- robots.txt 규칙 준수
- 저작권 및 개인정보 보호 고려

## 업데이트 내역

### v2.0.0 (2025-07-22)
- Selenium + undetected-chromedriver 도입
- 다중 검색 엔진 지원
- 봇 탐지 우회 기능 추가

### v1.0.0 (2025-07-22)
- 초기 버전 출시
- 기본 크롤링 기능 구현