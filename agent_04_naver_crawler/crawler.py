import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs
import json
from datetime import datetime, timedelta
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries.data_queries import DataQueries
from database.queries.brand_queries import BrandQueries
from database.utils import get_db
from config import Config


class NaverBlogCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            }
        )
        self.config = Config
        self.logger = self._setup_logger()
        self.data_queries = DataQueries()
        
    def _setup_logger(self):
        """로거 설정"""
        # logs 디렉토리 생성
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 로거 생성
        logger = logging.getLogger('NaverBlogCrawler')
        logger.setLevel(logging.INFO)
        
        # 파일 핸들러 설정 (10MB, 5개 파일 로테이션)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, f'crawler_{datetime.now().strftime("%Y%m%d")}.log'),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(file_handler)
        
        return logger
        
    def extract_blog_id_and_log_no(self, url):
        """블로그 URL에서 blog_id와 log_no 추출"""
        try:
            parsed = urlparse(url)
            if 'blog.naver.com' in parsed.netloc:
                # blog.naver.com/blog_id/log_no 형식
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    return path_parts[0], path_parts[1]
                elif len(path_parts) == 1:
                    # blog.naver.com/PostView.naver?blogId=xxx&logNo=xxx 형식
                    query_params = parse_qs(parsed.query)
                    blog_id = query_params.get('blogId', [None])[0]
                    log_no = query_params.get('logNo', [None])[0]
                    return blog_id, log_no
        except Exception as e:
            print(f"URL 파싱 오류: {e}")
        return None, None

    def format_date(self, date_str):
        """날짜 문자열을 표준 형식으로 변환"""
        if not date_str:
            return None
        
        try:
            # 상대 시간 처리
            if "분 전" in date_str or "시간 전" in date_str or "방금 전" in date_str:
                return datetime.now()
            if "어제" in date_str:
                return datetime.now() - timedelta(days=1)

            # 절대 시간 처리
            patterns = [
                (r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.", "%Y-%m-%d"),
                (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
            ]
            
            for pattern, date_format in patterns:
                match = re.search(pattern, date_str)
                if match:
                    year, month, day = match.groups()
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    return datetime.strptime(date_str, date_format)
                    
            # 시간 정보가 포함된 경우
            if re.match(r'\d{4}\.\d{1,2}\.\d{1,2}\.\s*\d{1,2}:\d{2}', date_str):
                date_str = re.sub(r'(\d{4})\.(\d{1,2})\.(\d{1,2})\.\s*(\d{1,2}):(\d{2})', 
                                 r'\1-\2-\3 \4:\5', date_str)
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                
        except Exception as e:
            print(f"날짜 변환 오류: {e}, 원본: {date_str}")
            
        return None

    def is_valid_blog_url(self, url):
        """유효한 네이버 블로그 URL인지 확인"""
        return url and ("blog.naver.com" in url or "blog.me" in url)

    def search_blogs(self, query, start=1, retry_count=0, max_retries=3):
        """네이버 블로그 검색 (재시도 로직 포함)"""
        url = "https://search.naver.com/search.naver"
        params = {
            "ssc": "tab.blog.all",
            "query": query,
            "sm": "tab_jum",
            "start": start,
        }
        try:
            response = self.session.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.warning(f"검색 요청 실패 (시도 {retry_count + 1}/{max_retries}): {e}")
            
            if retry_count < max_retries - 1:
                time.sleep(2 ** retry_count)  # 지수 백오프
                return self.search_blogs(query, start, retry_count + 1, max_retries)
            
            self.logger.error(f"검색 요청 최종 실패: {e}")
            return None

    def extract_blog_info(self, html):
        """검색 결과에서 블로그 정보 추출"""
        soup = BeautifulSoup(html, "html.parser")
        blog_items = []

        for item in soup.select("div.view_wrap"):
            try:
                title_link = item.select_one("a.title_link")
                if not (title_link and title_link.get("href")):
                    continue

                url = title_link.get("href")
                if not self.is_valid_blog_url(url):
                    continue

                title = title_link.get_text(strip=True)

                summary_element = item.select_one("div.dsc_area a.dsc_link")
                summary = (
                    summary_element.get_text(strip=True) if summary_element else ""
                )

                date_element = item.select_one("span.sub_time")
                date = (
                    self.format_date(date_element.get_text(strip=True))
                    if date_element
                    else None
                )
                
                # 작성자 정보 추출

                blog_items.append(
                    {
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "date": date,
                    }
                )
            except Exception as e:
                self.logger.warning(f"항목 추출 중 오류 발생: {e}")
                continue
        return blog_items

    def get_blog_content(self, blog_url):
        """블로그 본문 내용 가져오기"""
        try:
            response = self.session.get(blog_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # iframe 처리
            iframe = soup.find("iframe", id="mainFrame")
            if iframe and iframe.get("src"):
                iframe_url = urljoin(blog_url, iframe["src"])
                response = self.session.get(iframe_url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

            # 본문 내용 추출
            content_div = soup.select_one("div.se-main-container, div.post-view")
            content_html = ""
            content_text = ""
            
            if content_div:
                content_html = str(content_div)
                content_text = re.sub(r"\s+", " ", content_div.get_text(strip=True))
            else:
                content_text = "본문 내용을 찾을 수 없습니다."

            # 이미지 URL 추출
            image_urls = []
            if content_div:
                for img in content_div.find_all("img"):
                    src = img.get("src") or img.get("data-src")
                    if src and src.startswith("http"):
                        image_urls.append(src)

            # 날짜 추출
            date_text = None
            date_selectors = [
                "span.se_publishDate",
                "span.pcol2",
                ".blog_date",
                ".publish_date",
                "span[class*='date']",
            ]
            for selector in date_selectors:
                date_element = soup.select_one(selector)
                if date_element:
                    date_text = self.format_date(date_element.get_text(strip=True))
                    if date_text:
                        break



            return {
                "content_html": content_html,
                "content_text": content_text,
                "date": date_text,
                "image_urls": image_urls,
            }

        except Exception as e:
            self.logger.error(f"  -> 본문 가져오기 실패: {e}")
            return {
                "content_html": "",
                "content_text": f"내용을 가져올 수 없습니다: {e}",
                "date": None,
                "image_urls": [],
            }

    def check_duplicate(self, blog_id, log_no):
        """중복 체크"""
        try:
            db = get_db()
            query = """
                SELECT id FROM raw_naver_blog_data 
                WHERE blog_id = %s AND log_no = %s
                LIMIT 1
            """
            result = db.execute_one(query, (blog_id, log_no))
            return result is not None
        except Exception as e:
            self.logger.error(f"중복 체크 오류: {e}")
            return False

    def save_to_database(self, brand_official_name, blog_data):
        """데이터베이스에 저장"""
        try:
            blog_id, log_no = self.extract_blog_id_and_log_no(blog_data['url'])
            
            # 중복 체크
            if blog_id and log_no and self.check_duplicate(blog_id, log_no):
                print(f"  -> 이미 저장된 포스트입니다: {blog_id}/{log_no}")
                self.logger.info(f"중복 포스트 건너뛰기: {blog_id}/{log_no}")
                return False
            
            # 데이터 준비
            data = {
                'brand_name': brand_official_name,  # DB 컬럼명에 맞게 변경
                'blog_url': blog_data['url'],
                'blog_id': blog_id,
                'log_no': log_no,
                'post_title': blog_data.get('title', ''),
                'post_content': blog_data.get('content_html', ''),
                'images': blog_data.get('image_urls', []),
                'posted_at': blog_data.get('date')
            }
            
            # 데이터베이스에 저장
            DataQueries.insert_raw_naver_data(data)
            print(f"  -> 저장 완료: {blog_data['title'][:40]}...")
            self.logger.info(f"포스트 저장 성공: {blog_data['title'][:40]}...")
            return True
            
        except Exception as e:
            print(f"  -> 저장 실패: {e}")
            self.logger.error(f"포스트 저장 실패: {e}")
            return False

    def crawl_brand_blogs(self, brand_official_name, max_pages=10, posts_per_page=10):
        """특정 브랜드의 블로그 크롤링"""
        print(f"\n브랜드 '{brand_official_name}' 블로그 크롤링 시작...")
        self.logger.info(f"브랜드 '{brand_official_name}' 크롤링 시작")
        
        saved_count = 0
        crawled_count = 0
        error_count = 0
        
        # 크롤링 세션 생성
        session_data = {
            'brand_official_name': brand_official_name,
            'platform': 'naver_blog',
            'crawl_type': 'full',
            'status': 'running',
            'config': {
                'query': brand_official_name,
                'max_pages': max_pages,
                'posts_per_page': posts_per_page
            }
        }
        
        # 세션 데이터베이스에 저장
        try:
            session_id = self.data_queries.create_crawl_session(session_data)
            self.logger.info(f"크롤링 세션 생성: {session_id}")
        except Exception as e:
            self.logger.error(f"세션 생성 실패: {e}")
            session_id = f"naver_{brand_official_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        for page in range(1, max_pages + 1):
            start = (page - 1) * 10 + 1
            print(f"\n페이지 {page} 크롤링 중... (start: {start})")
            
            # 검색
            html = self.search_blogs(brand_official_name, start=start)
            if not html:
                break
            
            # 블로그 정보 추출
            blogs_on_page = self.extract_blog_info(html)
            if not blogs_on_page:
                print("더 이상 블로그 게시물을 찾을 수 없습니다.")
                break
            
            # 각 블로그 크롤링
            for blog in blogs_on_page:
                crawled_count += 1
                
                print(f"  크롤링 중: {blog['title'][:40]}...")
                
                try:
                    # 본문 내용 가져오기
                    content_data = self.get_blog_content(blog["url"])
                    
                    # 데이터 병합
                    blog.update(content_data)
                    if content_data.get("date"):
                        blog["date"] = content_data["date"]
                    
                    # 데이터베이스 저장
                    if self.save_to_database(brand_official_name, blog):
                        saved_count += 1
                    
                    # 크롤링 간격
                    time.sleep(self.config.CRAWL_DELAY)
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"크롤링 오류: {e}")
                    continue
            
            # 페이지 간 대기
            time.sleep(self.config.PAGE_DELAY)
        
        # 크롤링 세션 업데이트
        try:
            session_update = {
                'status': 'completed',
                'pages_crawled': page - 1,
                'items_found': crawled_count,
                'items_saved': saved_count,
                'error_count': error_count
            }
            self.data_queries.update_crawl_session(session_id, session_update)
            self.logger.info(f"크롤링 세션 업데이트 완료: {session_id}")
        except Exception as e:
            self.logger.error(f"세션 업데이트 실패: {e}")
        
        print(f"\n크롤링 완료!")
        print(f"- 크롤링한 포스트: {crawled_count}개")
        print(f"- 저장된 포스트: {saved_count}개")
        print(f"- 오류 발생: {error_count}개")
        
        self.logger.info(f"크롤링 완료 - 크롤링: {crawled_count}, 저장: {saved_count}, 오류: {error_count}")
        
        return {
            'session_id': session_id,
            'brand_official_name': brand_official_name,
            'crawled_count': crawled_count,
            'saved_count': saved_count,
            'error_count': error_count
        }