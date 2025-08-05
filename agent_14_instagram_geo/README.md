# KIJUN Instagram 완전 통합 파이프라인

KIJUN 브랜드의 Instagram 콘텐츠 분석, 이미지 생성, 목업 제작을 위한 완전 통합 파이프라인입니다.

## 📋 주요 기능

### 1단계: E-E-A-T-GEO 완전한 분석

- **공식 게시물**: E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) 및 GEO (Generative Engine Optimization) 완전 분석
- **UGC 분석**: TPO (Time, Place, Occasion), 스타일링, 감정 분석
- **순차적 파일 처리**: 파일1 → 1단계→2단계→3단계 완료, 파일2 → 1단계→2단계→3단계 완료
- **전체 게시물 처리**: 12개 게시물 전체 분석 (기존 2개 제한 해제)
- **자동 컨설팅**: 점수 기준 상위/하위 게시물 선별 후 개선안 제공

### 2단계: AI 이미지 생성 (DALL-E 3)

- DALL-E 3를 활용한 고품질 Instagram 이미지 생성
- 분석 결과 기반 최적화된 이미지 컨셉 적용
- **API 키 필수 검증**: .env 파일에서 OpenAI API 키 자동 로드

### 3단계: Instagram 목업 생성

- 실제 Instagram 게시물과 유사한 목업 생성
- **실제 이미지 파일 사용**: images/ 폴더의 모든 파일 활용
- **특별 프로필 이미지**: insta_default_image.jpg 전용 사용
- **JSON 콘텐츠 통합**: generated_content 파일의 hashtags → 해시태그 위치, new_caption_v1 → 본문 위치
- 한글 폰트 지원으로 완벽한 한국어 표시 (Windows/Mac/Linux 대응)

## 🏗️ 프로젝트 구조

```
agent_14_instagram_geo/
├── kijun_complete_integrated_pipeline.py  # 🔥 메인 통합 파이프라인
├── run_pipeline.py                        # 파이프라인 실행기
├── .env                                   # OpenAI API 키 설정
├── .env.example                          # 환경 변수 예시
├── requirements.txt                      # Python 패키지 의존성
├── images/                               # 🎨 실제 이미지 파일들
│   ├── insta_default_image.jpg          # 프로필 이미지 (전용)
│   ├── heart.png                        # 좋아요 아이콘
│   ├── comment.png                      # 댓글 아이콘
│   ├── share.png                        # 공유 아이콘
│   └── bookmark.png                     # 북마크 아이콘
├── kijun_official.json                  # 🔍 KIJUN 공식 게시물 데이터
├── kijun_official_tagged.json           # 🔍 KIJUN UGC 데이터
└── outputs/                             # 생성된 결과물들
    ├── *_eeatg_analysis.json           # E-E-A-T-GEO 분석 결과
    ├── *_ugc_combined_analysis.json    # UGC 포함 분석 결과
    ├── *_generated_content.json        # 개선된 콘텐츠 제안
    ├── final_generated_image_kijun.jpg  # DALL-E 3 생성 이미지
    └── *_instagram_mockup.jpg          # 최종 Instagram 목업
```

## 🚀 설치 및 사용법

### 1. 환경 설정

```bash
# 패키지 설치
pip install -r requirements.txt

# 환경 변수 확인 (이미 설정됨)
# .env 파일에 OpenAI API 키가 설정되어 있는지 확인
```

⚠️ **중요**: OpenAI API 키가 `.env` 파일에 설정되어야 합니다:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 2. 데이터 준비

다음 형식의 JSON 파일을 준비하세요:

**kijun_official.json** (공식 게시물 - 12개 게시물):

```json
[
  {
    "href": "https://instagram.com/p/sample1",
    "date": "2025-01-20",
    "content": "KIJUN 신상품 컬렉션 출시! #fashion #style",
    "img": ["image1.jpg", "image2.jpg"],
    "comments": []
  }
]
```

**kijun_official_tagged.json** (UGC 포함 - 12개 게시물):

```json
[
  {
    "href": "https://instagram.com/p/ugc1",
    "date": "2025-01-20",
    "content": "KIJUN 티셔츠 너무 편해요! #kijun #ootd",
    "img": ["ugc_image.jpg"],
    "comments": []
  }
]
```

### 3. 실행

**메인 실행 (권장)**

```bash
python run_pipeline.py
```

**또는 통합 파이프라인 직접 실행**

```bash
python kijun_complete_integrated_pipeline.py
```

### 4. 실행 과정

#### 파일별 순차 처리:

1. **파일1 (kijun_official_tagged.json)**: 1단계→2단계→3단계 완료
2. **파일2 (kijun_official.json)**: 1단계→2단계→3단계 완료

#### 각 단계별 처리:

- **1단계**: 12개 게시물 전체 E-E-A-T-GEO 분석
- **2단계**: DALL-E 3 이미지 생성 (API 키 필수)
- **3단계**: Instagram 목업 생성 (실제 이미지 파일 사용)

## 📊 출력 파일

### 분석 결과 파일:

- `kijun_official_eeatg_analysis.json`: 공식 게시물 E-E-A-T-GEO 분석
- `kijun_official_tagged_ugc_combined_analysis.json`: UGC 포함 종합 분석
- `*_generated_content.json`: 개선된 콘텐츠 제안 (hashtags, new_caption_v1 포함)

### 생성 결과 파일:

- `final_generated_image_kijun.jpg`: AI 생성 이미지 (DALL-E 3)
- `kijun_official_instagram_mockup.jpg`: 공식 게시물 Instagram 목업
- `kijun_official_tagged_instagram_mockup.jpg`: UGC Instagram 목업

## 🎯 핵심 특징

### ✅ 실제 이미지 파일 활용

- **아이콘 생성 없음**: `images/` 폴더의 모든 실제 파일 사용
- **전용 프로필 이미지**: `insta_default_image.jpg` 프로필 이미지로 활용
- **PNG 투명도 지원**: heart.png, comment.png, share.png, bookmark.png

### ✅ JSON 콘텐츠 통합

- **generated_content 파일**: `hashtags` → 해시태그 위치에 삽입
- **new_caption_v1**: 본문 텍스트 위치에 삽입
- **Key-Value 형식**: API 응답을 구조화된 형식으로 파싱

### ✅ 순차적 파일 처리

```
파일1: 1단계 → 2단계 → 3단계 완료
파일2: 1단계 → 2단계 → 3단계 완료
```

### ✅ 전체 게시물 처리

- **12개 게시물 전체**: 기존 2개 제한 해제
- **UGC/공식 자동 구분**: 파일명 기준 (`tagged` 포함 여부)
- **개별 분석**: 각 게시물별 상세 점수 및 개선안 제공

### ✅ API 키 필수 검증

```python
if not api_key:
    print("❌ OpenAI API 키가 .env 파일에 설정되지 않았습니다.")
    print("💡 .env 파일에 OPENAI_API_KEY=your_api_key_here를 추가해주세요.")
    return False
```

## 🔧 커스터마이징

### 이미지 파일 교체

`images/` 폴더의 파일들을 원하는 이미지로 교체하세요:

- `insta_default_image.jpg`: 프로필 이미지
- `heart.png`, `comment.png`, `share.png`, `bookmark.png`: Instagram 아이콘들

### 폰트 설정

`utils/font_utils.py`에서 폰트 경로를 수정하여 사용할 폰트를 변경할 수 있습니다.

## 📝 요구사항

- Python 3.8+
- OpenAI API 키
- PIL (Pillow)
- requests
- python-dotenv

## 🐛 문제 해결

### 한글 폰트 문제

```bash
# Mac
brew install --cask font-nanum-gothic

# Ubuntu/Debian
sudo apt-get install fonts-nanum
```

### 모듈 import 오류

프로젝트 루트 디렉토리에서 실행하세요:

```bash
cd agent_14_instagram_geo
python run_pipeline.py
```

## 📄 라이센스

이 프로젝트는 KIJUN 브랜드 전용으로 제작되었습니다.

분석 결과는 JSON 파일로 저장되며, 다음 정보를 포함합니다:

- **analysis_results**: 모든 게시물의 상세 분석 결과
- **low_score_posts**: 하위 점수 게시물 2개
- **high_score_posts**: 상위 점수 게시물 2개
- **generated_content**:
  - `low_score_revisions`: 하위 점수 게시물의 개선 제안
  - `best_practices`: 상위 점수 게시물의 베스트 프랙티스

## 분석 기준

### 공식 계정 (E-E-A-T-GEO)

- **Experience**: 실제 사용자 경험 표현도
- **Expertise**: 전문적 정보 전달도
- **Authoritativeness**: 브랜드 권위성
- **Trustworthiness**: 신뢰성
- **GEO**: 생성형 AI 최적화 (명료성, 구조성, 맥락성, 일치성, 적시성, 독창성)

### UGC 게시물

- **TPO 분석**: 제품과 상황의 적합성
- **스타일링 분석**: 코디네이션의 창의성
- **감정 분석**: 사용자의 긍정적 감정 표현

## 주의사항

- 이미지 파일 경로가 정확해야 합니다
- OpenAI API 키가 유효해야 합니다
- 인터넷 연결이 필요합니다 (OpenAI API 호출)

## 문제 해결

### 패키지 설치 오류

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### API 키 오류

`.env` 파일의 OpenAI API 키를 확인하세요.

### 이미지 로드 오류

이미지 파일 경로와 파일 존재 여부를 확인하세요.
