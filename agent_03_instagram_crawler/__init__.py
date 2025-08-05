"""
Agent 03: Instagram Crawler

Instagram 콘텐츠를 크롤링하여 데이터베이스에 저장하는 에이전트
"""

from .crawler import InstagramCrawler, Config

__version__ = "1.0.0"
__all__ = ['InstagramCrawler', 'Config']