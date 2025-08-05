# Agent 15: Blog GEO Analyzer

블로그 콘텐츠의 E-E-A-T(Experience, Expertise, Authoritativeness, Trustworthiness)와 GEO(Generative Engine Optimization)를 분석하고 개선안을 제시하는 에이전트입니다.

## 개요

이 에이전트는 네이버와 티스토리 블로그 포스트를 분석하여:
- E-E-A-T 기준으로 콘텐츠 품질 평가
- GEO 기준으로 AI 검색엔진 최적화 수준 평가
- 상위/하위 성과 포스트에 대한 컨설팅 제공
- 개선된 블로그 이미지 생성

## 주요 기능

### 1. E-E-A-T 분석
- **Experience (경험)**: 실제 경험과 사례 포함 여부
- **Expertise (전문성)**: 전문 지식과 깊이 있는 정보
- **Authoritativeness (권위성)**: 신뢰할 수 있는 출처와 근거
- **Trustworthiness (신뢰성)**: 정확성과 일관성

### 2. GEO 분석
- **Clarity (명확성)**: 명확하고 구체적인 정보 전달
- **Structure (구조성)**: 체계적인 정보 구성
- **Context (맥락성)**: 충분한 배경 정보 제공
- **Alignment (정합성)**: 시각적 요소와 텍스트의 조화
- **Originality (독창성)**: 독특한 관점과 인사이트
- **Timeliness (시의성)**: 최신 트렌드와 이벤트 반영

### 3. 시너지 분석
- **일관성**: E-E-A-T와 GEO 요소 간 조화
- **시너지 효과**: 요소들의 상호 보완 효과

### 4. 컨설팅 기능
- 제목 개선 전략 (3가지 방향)
- 콘텐츠 구조 개선안
- DALL-E를 활용한 이미지 생성
- 최종 블로그 이미지 합성

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
export OPENAI_API_KEY="your-api-key"
```

## 사용법

### 1. 명령줄 실행

```bash
# 네이버 블로그 분석
python run_analysis.py naver 1 --posts-limit 10

# 티스토리 블로그 분석
python run_analysis.py tistory 2 --brand-name "테스트브랜드" --selective-count 3

# 데이터베이스 저장 없이 실행
python run_analysis.py naver 1 --no-database

# API 키 직접 지정
python run_analysis.py tistory 1 --api-key "your-api-key"
```

### 2. Python API 사용

```python
from agent_15_blog_geo import create_blog_geo_analyzer

# 분석기 생성
analyzer = create_blog_geo_analyzer(
    openai_api_key="your-api-key",
    output_dir="../outputs"
)

# 블로그 분석 실행
results = analyzer.analyze_blog(
    platform="naver",
    brand_id=1,
    brand_name="브랜드명",
    total_posts_to_process=10,
    n_selective=2,
    save_to_database=True
)

# 결과 확인
print(f"총 분석 포스트: {results['total_posts_analyzed']}")
print(f"평균 E-E-A-T 점수: {results['average_scores']['eeat_average']}")
print(f"평균 GEO 점수: {results['average_scores']['geo_average']}")
```

## 워크플로우 구조

```
[데이터 준비] → [포스트 분석] → [순위 선정] → [컨설팅 생성]
                                                     ↓
[최종 보고서] ← [블로그 이미지 생성] ← [이미지 생성] ←┘
```

### 노드 설명

1. **prepare_data**: 데이터베이스에서 블로그 데이터 로드
2. **analyze_posts**: 각 포스트의 E-E-A-T/GEO 분석
3. **rank_and_select**: 상위/하위 성과자 선정
4. **consult_posts**: 선정된 포스트에 대한 컨설팅
5. **generate_images**: DALL-E로 개선된 이미지 생성
6. **generate_blog_images**: 최종 블로그 이미지 합성
7. **finalize_reports**: 최종 보고서 생성

## 데이터베이스 연동

### 입력 데이터 (Agent 08/09에서)
- `raw_naver_data`: 네이버 블로그 원시 데이터
- `raw_tistory_data`: 티스토리 블로그 원시 데이터
- `refined_content`: 정제된 콘텐츠 (선택)

### 출력 데이터
- `blog_geo_analyses`: 전체 분석 요약
- `blog_post_analyses`: 개별 포스트 분석 결과
- `blog_consulting_reports`: 컨설팅 보고서

## 출력 파일

1. **분석 보고서** (`analysis_report_*.md`)
   - 전체 포스트 분석 결과
   - E-E-A-T/GEO 점수 상세
   - 강점과 약점 분석

2. **컨설팅 보고서** (`consulting_report_*.md`)
   - 선정된 포스트의 개선안
   - 제목 및 구조 개선 전략
   - 이미지 개선 제안

3. **생성된 이미지**
   - DALL-E 생성 이미지 (`dalle_*.png`)
   - 최종 블로그 이미지 (`blog_image_*.png`)

## 평가 기준 상세

### E-E-A-T 점수 (각 25점, 총 100점)
- **90-100점**: 탁월함
- **80-89점**: 우수함
- **70-79점**: 양호함
- **60-69점**: 보통
- **60점 미만**: 개선 필요

### GEO 점수 (각 16.67점, 총 100점)
- 6가지 기준의 균형잡힌 평가
- AI 검색엔진 최적화 관점

### 시너지 점수 (총 100점)
- 일관성 50점
- 시너지 효과 50점

## 에이전트 간 연결

### 선행 에이전트
- **Agent 08 (Naver Refiner)**: 네이버 블로그 데이터 제공
- **Agent 09 (Tistory Refiner)**: 티스토리 블로그 데이터 제공

### 후행 에이전트
- 분석 결과는 향후 콘텐츠 전략 수립에 활용 가능

## 문제 해결

### OpenAI API 오류
```bash
# API 키 확인
echo $OPENAI_API_KEY

# 직접 지정
python run_analysis.py naver 1 --api-key "sk-..."
```

### 데이터 없음 오류
```bash
# Agent 08/09 실행 확인
cd ../agent_08_naver_refiner
python main.py --brand-id 1
```

### 메모리 부족
- `--posts-limit` 값을 줄여서 실행
- 이미지 생성을 건너뛰려면 코드 수정 필요

## 변경 이력

### v2.0.0 (2024-01-24)
- SQLAlchemy에서 PyMySQL로 변경
- 공통 데이터베이스 연결 사용
- RotatingFileHandler 로깅 적용
- 한국어 문서화 완성
- 인코딩 문제 해결

### v1.0.0
- 초기 버전 릴리즈

## 라이선스

MIT License