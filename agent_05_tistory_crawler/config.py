import os
from pathlib import Path
from dotenv import load_dotenv

# 상위 디렉토리에서 환경 변수 로드
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """티스토리 크롤러 설정"""
    
    # 크롤러 버전
    CRAWLER_VERSION = "2.0.0"  # v2: Selenium 기반 구글 검색 추가
    
    # 크롤링 설정
    MAX_PAGES_PER_BRAND = int(os.getenv("TISTORY_MAX_PAGES", "10"))
    POSTS_PER_PAGE = int(os.getenv("TISTORY_POSTS_PER_PAGE", "20"))
    CRAWL_DELAY = float(os.getenv("TISTORY_CRAWL_DELAY", "0.5"))
    PAGE_DELAY = float(os.getenv("TISTORY_PAGE_DELAY", "1.0"))
    REQUEST_TIMEOUT = int(os.getenv("TISTORY_REQUEST_TIMEOUT", "10"))
    
    # 최소 이미지 개수 (원본과 동일하게 5개로 설정)
    MIN_IMAGES = int(os.getenv("TISTORY_MIN_IMAGES", "5"))
    
    # 최소 콘텐츠 길이
    MIN_CONTENT_LENGTH = int(os.getenv("TISTORY_MIN_CONTENT_LENGTH", "100"))
    
    # Chrome 드라이버 설정
    USE_HEADLESS = os.getenv("TISTORY_USE_HEADLESS", "false").lower() == "true"
    CHROME_WAIT_TIME = int(os.getenv("TISTORY_CHROME_WAIT", "3"))
    ENABLE_MANUAL_CAPTCHA = os.getenv("TISTORY_MANUAL_CAPTCHA", "true").lower() == "true"
    
    # 검색 엔진 설정
    PRIMARY_SEARCH = os.getenv("TISTORY_SEARCH_ENGINE", "google")  # google, daum, naver
    FALLBACK_SEARCH = os.getenv("TISTORY_FALLBACK_SEARCH", "true").lower() == "true"
    
    # 키워드 필터링 설정
    # 네거티브 키워드 (이러한 키워드가 포함된 콘텐츠는 제외)
    NEGATIVE_KEYWORDS = [
        "대출", "투자", "주식", "부동산", "카지노", "도박", "성인", 
        "다이어트", "성형", "병원", "의료", "약국", "건강식품",
        "여행사", "항공권", "호텔예약", "렌터카", "관광",
        "보험", "연금", "펀드", "증권", "암호화폐", "비트코인"
    ]
    
    # 포지티브 키워드 (패션 관련 키워드)
    POSITIVE_KEYWORDS = [
        "패션", "스타일", "코디", "룩북", "착용", "스트릿", "브랜드",
        "의류", "옷", "셔츠", "팬츠", "자켓", "코트", "니트", "스웨터",
        "데님", "청바지", "스니커즈", "신발", "가방", "액세서리",
        "SS", "FW", "시즌", "컬렉션", "트렌드", "스타일링"
    ]
    
    # 데이터베이스 설정 (메인 .env에서 가져옴)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "modular_agents_db")
    
    # 경로
    PROJECT_ROOT = Path(__file__).parent
    LOG_DIR = PROJECT_ROOT / "logs"
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리가 모두 존재하는지 확인"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)