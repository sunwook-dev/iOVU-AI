# KIJUN 브랜드 디지털 채널 최적화 보고서 생성기

모듈화된 구조로 재구성된 통합 보고서 생성기입니다.

## 기능

- Instagram/Blog 데이터 분석 및 차트 생성
- 웹사이트 SEO/GEO 분석 및 차트 생성
- LLM 기반 보고서 섹션 자동 생성
- 목업 이미지 자동 삽입

## 디렉토리 구조

```
generate_report_final/
├── main.py                 # 메인 실행 파일
├── requirements.txt        # 패키지 의존성
├── README.md              # 프로젝트 설명
├── __init__.py            # 패키지 초기화
├── utils/                 # 유틸리티 모듈
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   ├── font_utils.py      # 폰트 설정
│   ├── file_utils.py      # 파일 처리
│   ├── image_utils.py     # 이미지 처리
│   └── markdown_utils.py  # 마크다운 생성
├── analyzers/             # 데이터 분석 모듈
│   ├── __init__.py
│   ├── instagram_analyzer.py
│   ├── blog_analyzer.py
│   └── website_analyzer.py
├── charts/                # 차트 생성 모듈
│   ├── __init__.py
│   ├── platform_charts.py
│   ├── website_charts.py
│   └── individual_charts.py
└── reports/               # 보고서 생성 모듈
    ├── __init__.py
    ├── llm_generator.py
    └── report_generator.py
```

## 설치 및 실행

1. 의존성 설치:

```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
   `.env` 파일에 OpenAI API 키 설정:

```
OPENAI_API_KEY=your_api_key_here
```

3. 데이터 파일 준비:
   `input/` 폴더에 필요한 JSON 데이터 파일들을 배치

4. 실행:

```bash
python main.py
```

## 출력

- 보고서: `output/KIJUN_브랜드_디지털채널_최적화_보고서_통합본.md`
- 차트 이미지들: `output/` 폴더 내
- 목업 이미지: `input/image/` 폴더에서 참조

## 모듈 설명

### utils/

- `config.py`: 전역 설정 관리
- `font_utils.py`: matplotlib 폰트 설정
- `file_utils.py`: JSON/마크다운 파일 처리
- `image_utils.py`: 이미지 경로 처리
- `markdown_utils.py`: 마크다운 포맷팅

### analyzers/

- `instagram_analyzer.py`: Instagram 데이터 전처리
- `blog_analyzer.py`: 블로그 데이터 전처리
- `website_analyzer.py`: 웹사이트 데이터 추출

### charts/

- `platform_charts.py`: 플랫폼 비교 차트
- `website_charts.py`: 웹사이트 분석 차트
- `individual_charts.py`: 개별 플랫폼 차트

### reports/

- `llm_generator.py`: LLM 텍스트 생성
- `report_generator.py`: 최종 보고서 조립
