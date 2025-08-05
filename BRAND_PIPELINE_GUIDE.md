# 브랜드 파이프라인 가이드

## 개요
이 시스템은 Agent 01의 FastAPI에서 입력받은 브랜드명을 모든 후속 에이전트(02-11)가 기억하고 사용할 수 있도록 설계되었습니다.

## 주요 기능

### 1. 브랜드명 기반 실행
- **이전**: 각 에이전트는 brand_id만 받아서 실행
- **현재**: 브랜드명(예: "kijun")으로 직접 실행 가능

### 2. 자동 데이터 조회
각 에이전트는 브랜드명을 받으면:
1. 데이터베이스에서 brand_id 조회
2. 해당 브랜드의 URL, Instagram 등 필요한 정보 자동 가져오기
3. 크롤링/분석 작업 수행

## 사용 방법

### 개별 에이전트 실행
```bash
# Agent 02: 웹 크롤러
python agent_02_web_crawler/run_crawler.py --brand-name kijun

# Agent 03: Instagram 크롤러  
python agent_03_instagram_crawler/run_crawler.py --brand-name kijun

# Agent 04: Naver 블로그 크롤러
python agent_04_naver_crawler/run_crawler.py --brand-name kijun

# Agent 05: Tistory 블로그 크롤러
python agent_05_tistory_crawler/run_crawler.py --brand-name kijun
```

### 통합 파이프라인 실행
```bash
# 모든 에이전트 순차 실행
python run_brand_pipeline.py kijun

# 특정 에이전트만 실행
python run_brand_pipeline.py kijun --agents 2,3,6,7

# 크롤러 건너뛰고 Refiner만 실행
python run_brand_pipeline.py kijun --skip-crawlers
```

## 작동 원리

### 1. Agent 01 (Query Collector)
```python
# FastAPI로 브랜드 정보 입력
POST /brands
{
    "name": "kijun",
    "homepage_url": "https://kijun.co",
    "instagram": "@kijun_official"
}
```

### 2. 브랜드명 전파
- 각 에이전트는 `--brand-name` 파라미터 지원
- BrandQueries.get_brand_by_name()으로 DB 조회
- brand_id와 관련 정보 자동 획득

### 3. 데이터 흐름
```
사용자 입력 (FastAPI) 
    ↓ "kijun"
Agent 01 → DB 저장
    ↓
Agent 02-05 (크롤러)
    - brand_name으로 DB 조회
    - URL, Instagram 등 자동 획득
    - 크롤링 수행
    ↓
Agent 06-09 (Refiner)
    - 크롤링된 데이터 정제
    ↓
Agent 10-11 (키워드 추출)
    - 최종 분석
```

## 주요 변경사항

### Agent 02 (Web Crawler)
- `--brand-name` 옵션 추가
- 브랜드명으로 official_site_url 자동 조회

### Agent 03 (Instagram Crawler)
- brand_id를 선택적 파라미터로 변경
- `--brand-name` 옵션으로 대체 가능

### Agent 04 & 05 (Blog Crawlers)
- crawl_single_brand()에 brand_name 파라미터 추가
- 브랜드명 기반 조회 로직 구현

## 환경 변수
파이프라인 실행 시 자동 설정:
- `CURRENT_BRAND_ID`: 현재 처리 중인 브랜드 ID
- `CURRENT_BRAND_NAME`: 현재 처리 중인 브랜드명

## 트러블슈팅

### 브랜드를 찾을 수 없을 때
1. DB에 브랜드가 등록되어 있는지 확인
2. 브랜드명이 정확한지 확인 (대소문자 구분)
3. Agent 01 API로 먼저 등록

### URL이 없어서 크롤링 실패
1. Agent 01에서 브랜드 등록 시 URL 정보 입력
2. 또는 DB에서 직접 업데이트

## 예시 시나리오

### 신규 브랜드 "newbrand" 처리
```bash
# 1. API 서버 시작
python agent_01_query_collector/run_api.py

# 2. 브랜드 등록 (별도 터미널에서)
curl -X POST http://localhost:8000/brands \
  -H "Content-Type: application/json" \
  -d '{
    "name": "newbrand",
    "homepage_url": "https://newbrand.com",
    "instagram": "@newbrand"
  }'

# 3. 파이프라인 실행
python run_brand_pipeline.py newbrand
```

이제 모든 에이전트가 "newbrand"라는 이름만으로 필요한 모든 정보를 자동으로 찾아 작업을 수행합니다!