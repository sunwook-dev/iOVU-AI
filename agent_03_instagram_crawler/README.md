# Agent 03: Instagram 크롤러

브랜드 Instagram 계정에서 게시물을 수집하는 에이전트입니다.

## 주요 기능

- Instagram 자동 로그인
- 브랜드 메인 게시물 크롤링
- 태그된 게시물 크롤링
- 게시물 상세 정보 수집 (캡션, 이미지, 댓글, 좋아요 수 등)
- 중복 게시물 자동 필터링
- 데이터베이스 저장 및 JSON 파일 백업

## 설치

### 요구사항

- Python 3.8 이상
- Playwright 지원 브라우저 (Chromium 권장)

### 의존성 설치

```bash
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

## 환경 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 설정을 추가하세요:

```env
# Instagram 인증 정보 (필수)
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# 크롤링 설정 (선택)
MAX_SCROLL_ROUND=5          # 최대 스크롤 횟수 (기본값: 1)
CRAWL_BATCH_SIZE=20         # 배치당 크롤링 수 (기본값: 12)
MAX_POSTS_PER_PAGE=100      # 페이지당 최대 게시물 수 (기본값: 50)
HEADLESS=false              # 헤드리스 모드 (기본값: false)

# 대기 시간 설정
MIN_SLEEP_SECONDS=5         # 최소 대기 시간 (기본값: 5)
MAX_SLEEP_SECONDS=9         # 최대 대기 시간 (기본값: 9)
```

## 사용 방법

### 기본 실행

```bash
# 특정 브랜드 크롤링
python run_crawler.py --brand-id 1

# 모든 활성 브랜드 크롤링
python run_crawler.py --all
```

### 옵션

- `--brand-id`: 특정 브랜드 ID 지정
- `--all`: 모든 활성 브랜드 크롤링
- `--headless`: 헤드리스 모드로 실행

### 예시

```bash
# 브랜드 ID 1 크롤링 (브라우저 표시)
python run_crawler.py --brand-id 1

# 모든 브랜드 헤드리스 모드로 크롤링
python run_crawler.py --all --headless
```

## 데이터 구조

### 입력: brand_channels 테이블

```sql
SELECT id, brand_id, instagram_handle 
FROM brand_channels 
WHERE platform = 'instagram' AND is_active = 1
```

### 출력: raw_instagram_data 테이블

| 필드 | 타입 | 설명 |
|------|------|------|
| id | INT | 자동 증가 ID |
| brand_id | INT | 브랜드 ID |
| channel_id | INT | 채널 ID |
| post_id | VARCHAR(50) | Instagram 게시물 ID |
| post_url | VARCHAR(500) | 게시물 URL |
| caption | TEXT | 게시물 캡션 |
| media_type | VARCHAR(20) | 미디어 타입 (image/video/carousel) |
| media_urls | JSON | 미디어 URL 목록 |
| like_count | INT | 좋아요 수 |
| comment_count | INT | 댓글 수 |
| hashtags | JSON | 해시태그 목록 |
| mentions | JSON | 멘션 목록 |
| location_info | JSON | 위치 정보 |
| posted_at | DATETIME | 게시 시간 |
| is_tagged | BOOLEAN | 태그된 게시물 여부 |
| crawled_at | DATETIME | 크롤링 시간 |
| raw_data | JSON | 원본 데이터 |

### JSON 파일 구조

크롤링된 데이터는 `data/instagram/` 디렉토리에 JSON 파일로도 저장됩니다:

```json
{
    "number": 1,
    "href": "https://www.instagram.com/p/ABC123/",
    "date": "2024-01-15 10:30:00",
    "content": "게시물 캡션 내용",
    "img": ["이미지 URL 1", "이미지 URL 2"],
    "comments": ["댓글 1", "댓글 2"],
    "like_count": 123,
    "comment_count": 45
}
```

## 크롤링 프로세스

1. **브랜드 정보 조회**: 데이터베이스에서 브랜드 Instagram 핸들 확인
2. **로그인**: Instagram 계정 로그인
3. **메인 게시물 크롤링**: 브랜드 계정의 메인 게시물 수집
4. **태그된 게시물 크롤링**: 브랜드가 태그된 게시물 수집
5. **상세 정보 수집**: 각 게시물의 상세 정보 크롤링
6. **데이터 저장**: 데이터베이스와 JSON 파일에 저장

## 에러 처리

- **로그인 실패**: 환경 변수 확인 및 계정 상태 점검
- **셀렉터 변경**: Instagram UI 변경 시 셀렉터 업데이트 필요
- **속도 제한**: 크롤링 속도 조절 (대기 시간 증가)
- **중복 데이터**: post_id 기반 자동 필터링

## 주의사항

1. **계정 보안**: 
   - 실제 계정 사용 시 2단계 인증 해제 필요
   - 크롤링 전용 계정 사용 권장

2. **속도 제한**:
   - Instagram의 속도 제한 정책 준수
   - 적절한 대기 시간 설정 필수

3. **데이터 정확성**:
   - Instagram UI 변경으로 셀렉터가 작동하지 않을 수 있음
   - 정기적인 코드 업데이트 필요

## 트러블슈팅

### 로그인 실패
```bash
# 환경 변수 확인
echo $INSTAGRAM_USERNAME
echo $INSTAGRAM_PASSWORD

# .env 파일 위치 확인
ls -la ../.env
```

### 셀렉터 에러
- Instagram UI가 변경되었을 가능성
- 브라우저 개발자 도구로 새 셀렉터 확인
- `instagram_crawler.py`의 셀렉터 업데이트

### 크롤링 속도 문제
```env
# .env 파일에서 대기 시간 증가
MIN_SLEEP_SECONDS=10
MAX_SLEEP_SECONDS=15
```

## 향후 개선 계획

- [ ] 스토리 크롤링 기능 추가
- [ ] 릴스(Reels) 크롤링 기능 추가
- [ ] 댓글의 대댓글 크롤링 지원
- [ ] 미디어 타입 자동 구분 (이미지/비디오/캐러셀)
- [ ] 프록시 지원
- [ ] 병렬 크롤링 지원

## 관련 에이전트

- **agent_07_instagram_refiner**: 크롤링된 데이터를 정제하고 분석
- **agent_01_query_collector**: 크롤링 대상 브랜드 정보 제공