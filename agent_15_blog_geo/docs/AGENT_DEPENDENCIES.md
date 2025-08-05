# Agent 15 의존성 문서

## 개요
Agent 15 (Blog GEO Analyzer)는 블로그 콘텐츠의 품질을 분석하고 개선안을 제시하는 에이전트입니다.

## 입력 의존성

### Agent 08 (Naver Refiner) - 네이버 분석 시 필수
- **테이블**: `raw_naver_data`
- **필드**:
  - `post_title`: 포스트 제목
  - `post_content`: 포스트 내용
  - `image_urls`: 이미지 URL 목록
  - `published_date`: 게시 날짜
  - `tags`: 태그 목록
  - `view_count`: 조회수
  - `like_count`: 좋아요 수
- **설명**: 네이버 블로그 포스트의 원시 데이터를 제공합니다.

### Agent 09 (Tistory Refiner) - 티스토리 분석 시 필수
- **테이블**: `raw_tistory_data`
- **필드**:
  - `post_title`: 포스트 제목
  - `post_content`: 포스트 내용
  - `image_urls`: 이미지 URL 목록
  - `published_date`: 게시 날짜
  - `category`: 카테고리
  - `tags`: 태그 목록
  - `view_count`: 조회수
- **설명**: 티스토리 블로그 포스트의 원시 데이터를 제공합니다.

### Refined Content (선택)
- **테이블**: `refined_content`
- **필드**:
  - `refined_text`: 정제된 텍스트
  - `summary`: 요약
  - `key_points`: 핵심 포인트
  - `quality_score`: 품질 점수
- **설명**: Agent 08/09에서 정제한 콘텐츠를 활용하여 더 정확한 분석이 가능합니다.

## 출력 데이터

### blog_geo_analyses
- **설명**: 브랜드별 전체 분석 요약
- **주요 필드**:
  - `brand_id`: 브랜드 ID
  - `platform`: 플랫폼 (naver/tistory)
  - `total_posts_analyzed`: 분석한 총 포스트 수
  - `posts_consulted`: 컨설팅한 포스트 수
  - `average_eeat_score`: 평균 E-E-A-T 점수
  - `average_geo_score`: 평균 GEO 점수
  - `overall_score`: 전체 평균 점수

### blog_post_analyses
- **설명**: 개별 포스트 분석 결과
- **주요 필드**:
  - `post_id`: 포스트 ID
  - `experience_score`: 경험 점수
  - `expertise_score`: 전문성 점수
  - `authoritativeness_score`: 권위성 점수
  - `trustworthiness_score`: 신뢰성 점수
  - `clarity_score`: 명확성 점수
  - `structure_score`: 구조성 점수
  - `context_score`: 맥락성 점수
  - `alignment_score`: 정합성 점수
  - `originality_score`: 독창성 점수
  - `timeliness_score`: 시의성 점수

### blog_consulting_reports
- **설명**: 선정된 포스트의 컨설팅 보고서
- **주요 필드**:
  - `post_id`: 포스트 ID
  - `selection_type`: 선정 타입 (top/bottom)
  - `title_consulting`: 제목 개선 전략
  - `content_consulting`: 콘텐츠 개선 전략
  - `generated_title`: 생성된 개선 제목
  - `dalle_image_path`: DALL-E 생성 이미지 경로
  - `final_blog_image_path`: 최종 블로그 이미지 경로

## 실행 순서

1. **Agent 03/04/05**: 블로그 크롤링 (원시 데이터 수집)
2. **Agent 08/09**: 블로그 데이터 정제 및 저장
3. **Agent 15**: 블로그 GEO 분석 및 컨설팅

## API 의존성

### OpenAI API
- **용도**: 
  - E-E-A-T/GEO 분석
  - 컨설팅 내용 생성
  - DALL-E 이미지 생성
- **필수 여부**: 필수
- **설정**: `OPENAI_API_KEY` 환경변수 또는 `--api-key` 옵션

## 데이터 흐름

```
[Agent 08/09 Raw Data] → [Agent 15 Analysis] → [Consulting Reports]
                              ↓
                        [Generated Images]
```

## 주의사항

1. **데이터 존재 확인**: Agent 08/09의 데이터가 없으면 분석 불가
2. **API 키 필수**: OpenAI API 키가 없으면 실행 불가
3. **플랫폼 일치**: 네이버 분석 시 Agent 08, 티스토리 분석 시 Agent 09 데이터 필요
4. **이미지 처리**: 대량의 이미지 생성 시 API 비용 고려

## 호환성

- **Python**: 3.8+
- **데이터베이스**: MySQL 5.7+
- **LangChain**: 0.1.0+
- **OpenAI API**: GPT-4, DALL-E 3