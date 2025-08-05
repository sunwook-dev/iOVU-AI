import os
from pathlib import Path
from dotenv import load_dotenv

# 상위 디렉토리에서 환경 변수 로드
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """Instagram 크롤러 설정"""
    
    # Instagram 인증 정보 (환경 변수 필수)
    INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
    
    # 크롤링 설정
    MAX_SCROLL_ROUND = int(os.getenv("MAX_SCROLL_ROUND", "1"))
    CRAWL_BATCH_SIZE = int(os.getenv("CRAWL_BATCH_SIZE", "12"))
    MAX_POSTS_PER_PAGE = int(os.getenv("MAX_POSTS_PER_PAGE", "50"))
    
    # 경로 설정
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data" / "instagram"
    
    # 브라우저 설정
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    
    # 대기 시간 설정
    MIN_SLEEP_SECONDS = float(os.getenv("MIN_SLEEP_SECONDS", "5"))
    MAX_SLEEP_SECONDS = float(os.getenv("MAX_SLEEP_SECONDS", "9"))
    
    @classmethod
    def ensure_data_dirs(cls):
        """모든 데이터 디렉토리가 존재하는지 확인"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)