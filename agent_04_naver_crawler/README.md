# Naver Blog Crawler Agent

네이버 블로그 크롤링 에이전트

## 개요

이 에이전트는 브랜드명을 기반으로 네이버 블로그를 검색하고 관련 포스트들을 수집합니다.
데이터베이스의 브랜드 정보를 활용하여 자동으로 크롤링을 수행하며,
수집된 데이터는 `raw_naver_blog_data` 테이블에 저장됩니다.

## 주요 기능

- 데이터베이스 브랜드명 기반 자동 검색
- 블로그 포스트 본문, 이미지, 태그 등 상세 정보 수집
- 중복 체크를 통한 효율적인 크롤링
- 날짜 형식 자동 변환 및 표준화
- JSON 필드를 활용한 구조화된 데이터 저장

## 설치 방법

```bash
# 의존성 설치
pip install -r requirements.txt
```

## 환경 설정

상위 디렉토리의 `.env` 파일에 다음 설정 추가:

```env
# Naver Crawler Settings
NAVER_MAX_PAGES=10          # 브랜드당 최대 페이지 수
NAVER_POSTS_PER_PAGE=10     # 페이지당 포스트 수
NAVER_CRAWL_DELAY=0.5       # 포스트 간 대기 시간(초)
NAVER_PAGE_DELAY=1.0        # 페이지 간 대기 시간(초)
NAVER_REQUEST_TIMEOUT=10    # 요청 타임아웃(초)
```

## 사용 방법

# 특정 브랜드 크롤링

```bash
python run_crawler.py --brand-name 'kijun'
```

# 모든 브랜드 크롤링

```bash
python run_crawler.py --all
```

# 커스텀 설정으로 크롤링

```bash
python run_crawler.py --brand-name 'kijun' --max-pages 20
```

## 크롤링 프로세스

1. **브랜드 정보 조회**: 데이터베이스에서 브랜드 정보 가져오기
2. **네이버 검색**: 브랜드명으로 블로그 검색 수행
3. **URL 추출**: 검색 결과에서 네이버 블로그 URL만 필터링
4. **상세 정보 수집**: 각 블로그 포스트의 상세 내용 크롤링
5. **중복 체크**: blog_id와 log_no로 기존 데이터 확인
6. **데이터 저장**: 새로운 포스트만 데이터베이스에 저장

## 데이터베이스 구조

### raw_naver_blog_data 테이블

| 컬럼명           | 타입         | 설명              |
| ---------------- | ------------ | ----------------- |
| id               | BIGINT       | 자동 증가 PK      |
| brand_id         | INT          | 브랜드 ID (FK)    |
| blog_url         | VARCHAR(500) | 블로그 포스트 URL |
| blog_id          | VARCHAR(100) | 네이버 블로그 ID  |
| log_no           | VARCHAR(50)  | 포스트 번호       |
| post_title       | VARCHAR(500) | 포스트 제목       |
| post_content     | LONGTEXT     | HTML 형식 본문    |
| post_summary     | TEXT         | 텍스트 요약       |
| author           | VARCHAR(100) | 작성자            |
| author_blog_name | VARCHAR(255) | 블로그명          |
| category         | VARCHAR(100) | 카테고리          |
| tags             | JSON         | 태그 목록         |
| images           | JSON         | 이미지 URL 목록   |
| view_count       | INT          | 조회수            |
| like_count       | INT          | 좋아요 수         |
| comment_count    | INT          | 댓글 수           |
| is_advertisement | BOOLEAN      | 광고글 여부       |
| posted_at        | DATETIME     | 작성일            |
| raw_data         | JSON         | 원본 데이터       |
| crawler_version  | VARCHAR(20)  | 크롤러 버전       |
| crawled_at       | DATETIME     | 크롤링 시간       |

## 주요 클래스

### NaverBlogCrawler

- `search_blogs()`: 네이버 블로그 검색
- `get_blog_content()`: 블로그 포스트 상세 내용 가져오기
- `extract_blog_id_and_log_no()`: URL에서 블로그 ID와 포스트 번호 추출
- `format_date()`: 다양한 날짜 형식 표준화
- `check_duplicate()`: 중복 포스트 확인
- `save_to_database()`: 데이터베이스 저장
- `crawl_brand_blogs()`: 브랜드별 크롤링 메인 로직

## 특징

- **스마트 날짜 파싱**: "어제", "3시간 전" 등 상대 시간 자동 변환
- **광고글 감지**: 포스트 내용에서 광고 여부 판단
- **이미지 최적화**: 네이버 CDN 이미지 URL 정리
- **태그 추출**: 해시태그 및 카테고리 태그 자동 수집
- **유연한 URL 파싱**: 다양한 네이버 블로그 URL 형식 지원

## 크롤링 결과 예시

```
=== 브랜드별 크롤링 시작 ===
브랜드: Uniform Bridge (ID: 1)

페이지 1 크롤링 중...
  크롤링: 유니폼브릿지 2024 S/S 신상품 후기
  -> 저장 완료

  크롤링: 유니폼 브릿지 셔츠 코디법
  -> 이미 저장된 포스트입니다: fashion123/223456789

페이지 2 크롤링 중...
...

크롤링 완료!
- 크롤링한 포스트: 50개
- 저장된 포스트: 35개 (15개 중복)
```

## 에러 처리

- 네트워크 오류 시 재시도 없이 다음 포스트로 진행
- HTML 파싱 실패 시 로그 출력 후 계속 진행
- 날짜 변환 실패 시 NULL로 저장
- 중복 포스트는 건너뛰기

## 주의사항

1. **크롤링 속도**: 네이버 서버 부하 방지를 위해 적절한 딜레이 필수
2. **IP 차단**: 과도한 요청 시 IP 차단 가능성 있음
3. **robots.txt**: 네이버 크롤링 정책 준수
4. **저작권**: 수집된 콘텐츠의 저작권 고려

## 유틸리티 스크립트

- `run_crawler.py`: 메인 크롤러 실행
- `check_data.py`: 크롤링된 데이터 확인
- `add_goyowear.py`: Goyowear 브랜드 추가 (예시)
- `quick_test.py`: 빠른 테스트용 스크립트

## 문제 해결

### 크롤링이 느린 경우

- `NAVER_CRAWL_DELAY` 값을 낮춰보세요 (최소 0.3초 권장)

### 중복 데이터가 많은 경우

- 정상적인 현상입니다. 동일 포스트가 검색 결과에 반복 노출됩니다.

### DateTime 직렬화 오류

- 코드에 이미 datetime 객체를 문자열로 변환하는 로직이 포함되어 있습니다.

## 업데이트 내역

### v1.0.0 (2025-07-22)

- 초기 버전 출시
- 데이터베이스 연동 구현
- 중복 체크 기능 추가
- DateTime 직렬화 문제 해결
