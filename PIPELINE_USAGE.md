# 모듈러 에이전트 파이프라인 사용 가이드

전체 15개 에이전트를 순차적으로 실행하는 통합 파이프라인 시스템입니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
# 기본 패키지 설치
pip install -r requirements_pipeline.txt

# 또는 개별 설치
pip install streamlit plotly psutil pymysql python-dotenv pandas
```

### 2. 환경 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=modular_agents_db
DB_CHARSET=utf8mb4

# OpenAI 설정 (필수)
OPENAI_API_KEY=your_openai_api_key_here

# 선택적 설정
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=256
LLM_TEMPERATURE=0.2
```

### 3. 데이터베이스 초기화

```bash
# 데이터베이스 및 테이블 생성
cd database
python init_db.py
```

### 4. 대시보드 실행

```bash
# 실행 스크립트 사용 (권장)
python run_dashboard.py

# 또는 직접 실행
streamlit run pipeline_dashboard.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## 📋 사용법

### 1. 브랜드 정보 입력

대시보드 사이드바에서:
- **브랜드 ID**: 고유한 정수 값 입력
- **브랜드명**: 선택사항, 브랜드 공식명

### 2. 실행 모드 선택

#### 전체 실행 (기본)
- 모든 15개 에이전트를 순서대로 실행

#### 선택적 실행
- 특정 에이전트들만 선택하여 실행
- 의존성이 있는 에이전트는 자동으로 포함됨

#### 특정 단계부터
- 지정된 에이전트부터 끝까지 실행

### 3. 고급 옵션

- **에러 시 중단**: 에이전트 실행 실패 시 파이프라인 중단 여부
- **데이터 검증**: 각 단계별 입력/출력 데이터 검증
- **자동 재시도**: 실패한 에이전트 자동 재시도
- **건너뛸 에이전트**: 특정 에이전트 제외

### 4. 환경 변수

- **OPENAI_API_KEY**: OpenAI API 키 (필수)
- **추가 환경 변수**: JSON 형식으로 입력

## 🎯 에이전트 실행 순서

1. **Agent 01**: Query Collector (검색 쿼리 수집)
2. **Agent 02**: Web Crawler (웹사이트 크롤링)
3. **Agent 03**: Instagram Crawler (Instagram 크롤링)
4. **Agent 04**: Naver Crawler (네이버 블로그 크롤링)
5. **Agent 05**: Tistory Crawler (티스토리 크롤링)
6. **Agent 06**: Web Refiner (웹 데이터 정제)
7. **Agent 07**: Instagram Refiner (Instagram 데이터 정제)
8. **Agent 08**: Naver Refiner (네이버 데이터 정제)
9. **Agent 09**: Tistory Refiner (티스토리 데이터 정제)
10. **Agent 10**: Web Keyword Extractor (웹 키워드 추출)
11. **Agent 11**: Social Keyword Extractor (소셜 키워드 추출)
12. **Agent 12**: Prompt Generator (프롬프트 생성)
13. **Agent 13**: Web GEO Optimizer (웹 GEO 최적화)
14. **Agent 14**: Instagram GEO Optimizer (Instagram GEO 최적화)
15. **Agent 15**: Blog GEO Analyzer (블로그 GEO 분석)

## 📊 대시보드 기능

### 제어판 탭
- **시작/일시정지/재개/중지**: 파이프라인 제어
- **실행 계획**: 선택된 에이전트 목록 표시

### 진행 상황 탭
- **전체 진행률**: 완료된 에이전트 비율
- **에이전트별 상태**: 각 에이전트의 현재 상태
- **실시간 메트릭**: 완료/실패/진행 중 개수

### 로그 탭
- **실시간 로그**: 각 에이전트의 실행 로그
- **로그 레벨 필터**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **자동 스크롤**: 최신 로그 자동 표시

### 통계 탭
- **실행 통계**: 총 로그 수, 에러 수, 경고 수
- **상태 분포**: 에이전트 상태별 파이 차트
- **에러/경고 분석**: 에이전트별 에러/경고 수 차트
- **결과 내보내기**: JSON 형식으로 결과 다운로드

## 🔧 명령줄 사용법

대시보드 없이 명령줄에서 직접 실행:

```bash
# 기본 실행
python pipeline_orchestrator.py 1 --brand-name "테스트브랜드"

# 특정 에이전트만 실행
python pipeline_orchestrator.py 1 --target-agents agent_01 agent_02 agent_06

# 특정 에이전트 건너뛰기
python pipeline_orchestrator.py 1 --skip-agents agent_03 agent_04 agent_05

# 에러 시 계속 진행
python pipeline_orchestrator.py 1 --no-stop-on-error

# 결과 내보내기
python pipeline_orchestrator.py 1 --export results.json
```

## 📁 데이터 흐름

```
입력: 브랜드 정보 (브랜드 ID, 이름 등)
  ↓
Agent 01: 검색 쿼리 수집 → brands, brand_channels 테이블
  ↓
Agent 02-05: 다양한 플랫폼 크롤링 → raw_* 테이블들
  ↓ 
Agent 06-09: 데이터 정제 → refined_content 테이블
  ↓
Agent 10-11: 키워드 추출 → extracted_keywords 테이블
Agent 12: 프롬프트 생성 → generated_prompts 테이블
  ↓
Agent 13-15: GEO 최적화 및 분석 → *_geo_analysis 테이블들
  ↓
출력: 최적화된 콘텐츠, 분석 보고서, 생성된 이미지
```

## ⚠️ 주의사항

### 필수 요구사항
1. **OpenAI API 키**: 대부분의 에이전트에서 필수
2. **MySQL 데이터베이스**: 모든 데이터 저장소
3. **충분한 디스크 공간**: 크롤링 데이터 저장용 (최소 5GB)
4. **안정적인 인터넷 연결**: 크롤링 및 API 호출용

### 실행 시간
- **전체 파이프라인**: 브랜드당 약 2-4시간
- **에이전트별 평균**: 5-30분 (데이터량에 따라 변동)

### 리소스 사용량
- **메모리**: 에이전트당 평균 1-2GB
- **CPU**: 중간 정도 사용량
- **네트워크**: 크롤링 단계에서 높음

## 🔍 문제 해결

### 일반적인 오류

#### 1. 데이터베이스 연결 실패
```bash
# MySQL 서버 상태 확인
sudo service mysql status

# 데이터베이스 존재 확인
mysql -u root -p -e "SHOW DATABASES LIKE 'modular_agents_db';"
```

#### 2. OpenAI API 오류
- API 키 유효성 확인
- 요청 한도 확인
- 네트워크 연결 확인

#### 3. 메모리 부족
- 동시 실행 에이전트 수 제한
- 가상 메모리 증가
- 불필요한 프로세스 종료

#### 4. 의존성 오류
```bash
# 패키지 재설치
pip install -r requirements_pipeline.txt --force-reinstall

# 가상환경 사용 권장
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements_pipeline.txt
```

### 로그 확인
```bash
# 파이프라인 로그
ls logs/pipeline/

# 개별 에이전트 로그
ls agent_*/logs/

# 실시간 로그 모니터링
tail -f logs/pipeline/pipeline_*.log
```

## 📞 지원

- **이슈 리포트**: GitHub Issues
- **문서**: README.md
- **실행 예시**: pipeline_orchestrator.py 하단 참조

## 🔄 업데이트

새로운 에이전트 추가 시:
1. `utils/agent_manager.py`의 `get_default_agent_configs()` 함수 수정
2. 의존성 관계 정의
3. 대시보드 재시작

---

**최종 업데이트**: 2024-07-24