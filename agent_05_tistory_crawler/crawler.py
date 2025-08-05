import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urljoin, urlparse, parse_qs, quote
import json
from datetime import datetime
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Selenium imports for Google search
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  undetected_chromedriver가 설치되지 않았습니다. 구글 검색이 제한됩니다.")

from database.queries.data_queries import DataQueries
from database.queries.brand_queries import BrandQueries
from database.utils import get_db
from config import Config


class TistoryCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        self.config = Config
        self.logger = self._setup_logger()
        self.data_queries = DataQueries()
        self.driver = None  # Chrome 드라이버 인스턴스 재사용

    def _check_captcha(self, driver) -> bool:
        """
        구글 리캡차 페이지 여부를 확인.
        현재는 element 탐색 후 True/False만 리턴하고,
        탐지 시 사용자에게 캡차 해결 안내만 띄웁니다.
        """
        try:
            # google 리캡차 div 검사
            self.driver.find_element("css selector", "div#recaptcha")
            print(
                "[캡차] Google reCAPTCHA가 감지되었습니다. 수동으로 해결 후 엔터를 눌러 주세요."
            )
            input()
            return True
        except Exception:
            return False

    def _setup_logger(self):
        """로거 설정"""
        # logs 디렉토리 생성
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)

        # 로거 생성
        logger = logging.getLogger("TistoryCrawler")
        logger.setLevel(logging.INFO)

        # 파일 핸들러 설정 (10MB, 5개 파일 로테이션)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, f'crawler_{datetime.now().strftime("%Y%m%d")}.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)

        # 포맷터 설정
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # 핸들러 추가
        logger.addHandler(file_handler)

        return logger

    def _check_content_quality(self, title, content):
        """콘텐츠 품질 체크 (키워드 필터링)"""
        if not title or not content:
            return False

        # 콘텐츠 길이 체크
        if len(content) < self.config.MIN_CONTENT_LENGTH:
            return False

        # 네거티브 키워드 체크
        for neg_keyword in self.config.NEGATIVE_KEYWORDS:
            if neg_keyword in title or neg_keyword in content:
                self.logger.debug(f"네거티브 키워드 발견: {neg_keyword}")
                return False

        # 포지티브 키워드 체크 (최소 하나는 포함되어야 함)
        found_positive = False
        for pos_keyword in self.config.POSITIVE_KEYWORDS:
            if pos_keyword in title.lower() or pos_keyword in content.lower():
                found_positive = True
                break

        if not found_positive:
            self.logger.debug("패션 관련 키워드가 없음")
            return False

        return True

    def random_delay(self, min_sec=None, max_sec=None):
        """랜덤 딜레이 (봇 탐지 회피)"""
        if min_sec is None:
            min_sec = self.config.CRAWL_DELAY
        if max_sec is None:
            max_sec = self.config.CRAWL_DELAY * 2

        delay = random.uniform(min_sec, max_sec)
        self.logger.debug(f"대기 시간: {delay:.2f}초")
        time.sleep(delay)

    def extract_blog_info(self, url):
        """티스토리 URL에서 블로그명과 포스트 ID 추출 (entry_id가 없으면 마지막 path segment 사용)"""
        try:
            parsed = urlparse(url)

            if ".tistory.com" in parsed.netloc:
                blog_name = parsed.netloc.split(".")[0]
                path_parts = parsed.path.strip("/").split("/")

                if path_parts and path_parts[0].isdigit():
                    post_id = path_parts[0]
                elif len(path_parts) >= 2 and path_parts[0] == "entry":
                    # /entry/post-title 형식: 마지막 path segment를 entry_id로 사용
                    post_id = path_parts[-1] if path_parts[-1] else None
                elif path_parts:
                    # 기타 케이스: 마지막 path segment 사용
                    post_id = path_parts[-1]
                else:
                    post_id = None

                return blog_name, post_id

        except Exception as e:
            print(f"URL 파싱 오류: {e}")

        return None, None

    def search_tistory(self, keyword, page=1):
        """티스토리 검색 (구글 검색 사용)"""
        # Selenium이 설치되어 있으면 사용
        if SELENIUM_AVAILABLE:
            return self.search_tistory_selenium(keyword, page)
        else:
            # 기존 requests 방식 시도
            return self.search_tistory_requests(keyword, page)

    def _get_or_create_driver(self):
        """드라이버 인스턴스 가져오기 또는 생성"""
        if self.driver is None:
            self.logger.info("새 Chrome 드라이버 시작")
            options = uc.ChromeOptions()
            options.add_argument("--log-level=3")
            if self.config.USE_HEADLESS:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.driver = uc.Chrome(options=options)
        return self.driver

    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome 드라이버 종료")
            except:
                pass
            finally:
                self.driver = None

    def search_tistory_selenium(self, keyword, page=1):
        """Selenium을 사용한 구글 검색 (봇 탐지 우회)"""
        print("  Selenium으로 구글 검색 시작...")
        query = f'"{keyword}" site:tistory.com'
        start = (page - 1) * 10

        try:
            driver = self._get_or_create_driver()

            # 구글 검색 페이지 방문
            url = f"https://www.google.com/search?q={query}&start={start}"
            driver.get(url)

            # 페이지 로딩 대기 (랜덤)
            self.random_delay(2, 4)

            # CAPTCHA 체크
            if self._check_captcha(driver):
                if self.config.ENABLE_MANUAL_CAPTCHA:
                    print("  [!!] 캐플가 감지되었습니다. 수동으로 해결하세요.")
                    input("     캐플를 해결한 후 Enter 키를 누르세요...")
                else:
                    self.logger.warning("CAPTCHA 발생, 대체 검색으로 전환")
                    return self.search_tistory_direct(keyword, page)

            # 검색 결과 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.g, div[data-ved]")
                )
            )

            # HTML 파싱
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # URL 추출
            urls = []
            search_results = soup.select("div.g, div[data-ved]")

            for item in search_results:
                link_tag = item.select_one("a")
                if link_tag and "href" in link_tag.attrs:
                    href = link_tag["href"]
                    if href.startswith("http") and "tistory.com" in href:
                        # 필터링
                        path = urlparse(href).path
                        if (
                            "/category" not in href
                            and "/tag" not in href
                            and len(path) > 1
                        ):
                            normalized_url = href.rstrip("/")
                            if normalized_url not in urls:
                                urls.append(normalized_url)

            print(f"  Selenium 검색에서 {len(urls)}개 URL 발견")
            return urls

        except Exception as e:
            print(f"  Selenium 검색 오류: {e}")
            self.logger.error(f"Selenium 검색 오류: {e}")
            return self.search_tistory_direct(keyword, page)

    def search_tistory_requests(self, keyword, page=1):
        """기존 requests 방식 검색 (백업)"""
        try:
            # 티스토리는 자체 검색 API가 제한적이므로 구글 검색 사용
            query = f'"{keyword}" site:tistory.com'
            start = (page - 1) * 10

            url = f"https://www.google.com/search"
            params = {"q": query, "start": start, "hl": "ko"}

            # 더 실제같은 헤더 추가
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            response = self.session.get(
                url, params=params, headers=headers, timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 구글 검색 결과에서 URL 추출 (다양한 셀렉터 시도)
            urls = []

            # 방법 1: 일반적인 검색 결과
            for g in soup.select("div.g"):
                link = g.select_one("a")
                if link and link.get("href"):
                    href = link["href"]
                    if "tistory.com" in href and "/m/" not in href:
                        urls.append(href)

            # 방법 2: 다른 형식의 결과
            if not urls:
                for link in soup.select("a"):
                    href = link.get("href", "")
                    if (
                        "tistory.com" in href
                        and href.startswith("http")
                        and "/m/" not in href
                    ):
                        urls.append(href)

            # 구글이 차단했는지 확인
            if (
                "captcha" in response.text.lower()
                or "unusual traffic" in response.text.lower()
            ):
                print("  ⚠️  구글에서 비정상적인 트래픽으로 감지됨")
                return self.search_tistory_direct(keyword, page)

            print(f"  구글 검색에서 {len(urls)}개 URL 발견")
            return urls

        except Exception as e:
            print(f"구글 검색 오류: {e}")
            return self.search_tistory_direct(keyword, page)

    def search_tistory_direct(self, keyword, page=1):
        """티스토리 직접 검색 (대체 방법)"""
        try:
            print("  티스토리 직접 검색 시도 중...")

            urls = []

            # Daum 검색 API 사용
            try:
                daum_url = "https://search.daum.net/search"
                params = {"w": "blog", "q": f"{keyword} tistory", "p": page}

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9",
                }

                response = self.session.get(
                    daum_url,
                    params=params,
                    headers=headers,
                    timeout=self.config.REQUEST_TIMEOUT,
                )
                soup = BeautifulSoup(response.text, "html.parser")

                # Daum 검색 결과 파싱
                for item in soup.select("div.wrap_tit a, a.f_link_b"):
                    href = item.get("href", "")
                    if "tistory.com" in href and href.startswith("http"):
                        if href not in urls:
                            urls.append(href)
                        if len(urls) >= 10:
                            break

                print(f"  Daum 검색에서 {len(urls)}개 URL 발견")
            except Exception as e:
                print(f"  Daum 검색 오류: {e}")

            # Naver 검색도 시도
            if len(urls) < 10:
                try:
                    naver_url = "https://search.naver.com/search.naver"
                    params = {
                        "where": "blog",
                        "query": f"{keyword} tistory",
                        "start": (page - 1) * 10 + 1,
                    }

                    response = self.session.get(
                        naver_url,
                        params=params,
                        headers=headers,
                        timeout=self.config.REQUEST_TIMEOUT,
                    )
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Naver 검색 결과 파싱
                    for item in soup.select("a.link_bf_title, a.api_txt_lines"):
                        href = item.get("href", "")
                        if "tistory.com" in href and href.startswith("http"):
                            if href not in urls:
                                urls.append(href)
                            if len(urls) >= 20:
                                break

                    print(
                        f"  Naver 검색에서 추가로 {len(urls) - len(urls[:10])}개 URL 발견"
                    )
                except Exception as e:
                    print(f"  Naver 검색 오류: {e}")

            # 직접 알려진 패션 블로그들 체크
            if not urls and keyword.lower() in [
                "uniform bridge",
                "유니폼브릿지",
                "유니폼 브릿지",
            ]:
                print("  알려진 패션 블로그에서 직접 검색...")
                # 실제 존재하는 패션 티스토리 블로그들
                fashion_blogs = [
                    "https://fashionseoul.com",
                    "https://ohou.tistory.com",
                    "https://musinsa.tistory.com",
                ]

                for blog_base in fashion_blogs:
                    try:
                        # 블로그 메인 페이지 접속
                        response = self.session.get(blog_base, timeout=5)
                        if (
                            response.status_code == 200
                            and "tistory.com" in response.url
                        ):
                            soup = BeautifulSoup(response.text, "html.parser")
                            # 최근 포스트 링크 추출
                            for link in soup.select("a"):
                                href = link.get("href", "")
                                text = link.get_text().lower()
                                if keyword.lower() in text or "유니폼" in text:
                                    full_url = urljoin(response.url, href)
                                    if (
                                        "tistory.com" in full_url
                                        and full_url not in urls
                                    ):
                                        urls.append(full_url)
                    except:
                        continue

            print(f"  직접 검색에서 {len(urls)}개 URL 발견")
            return urls[:10]  # 최대 10개

        except Exception as e:
            print(f"직접 검색 오류: {e}")
            return []

    def get_post_content(self, url):
        """티스토리 포스트 상세 내용 가져오기"""
        try:
            # 모바일 URL을 데스크톱 URL로 변경
            if "/m/" in url or "/m." in url:
                url = url.replace("/m/", "/").replace("/m.", ".")

            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 제목 추출
            title = None
            title_selectors = [
                'meta[property="og:title"]',
                "h1.title",
                "h1.entry-title",
                "h1",
                "title",
            ]

            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if selector.startswith("meta"):
                        title = elem.get("content", "")
                    else:
                        title = elem.get_text(strip=True)
                    if title:
                        break

            # 본문 추출
            content_selectors = [
                "div.entry-content",
                "div.tt_article_useless_p_margin",
                "div.contents_style",
                "div.article_view",
                "article.article",
                "div.post-content",
                "div#content",
                "div.area_view",
            ]

            content_html = ""
            content_text = ""

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 불필요한 요소 제거
                    for elem in content_elem.select(
                        "script, style, iframe, .adsbygoogle"
                    ):
                        elem.decompose()

                    content_html = str(content_elem)
                    content_text = content_elem.get_text(separator="\n", strip=True)
                    break

            # 이미지 추출
            images = []
            if content_elem:
                for img in content_elem.select("img"):
                    src = (
                        img.get("src")
                        or img.get("data-src")
                        or img.get("data-original")
                    )
                    if src and not src.startswith("data:"):
                        full_url = urljoin(url, src)
                        images.append(full_url)

            # 카테고리 추출
            category = ""
            category_elem = soup.select_one(
                '.category, .post-category, meta[property="article:section"]'
            )
            if category_elem:
                if category_elem.name == "meta":
                    category = category_elem.get("content", "")
                else:
                    category = category_elem.get_text(strip=True)

            # 태그 추출
            tags = []
            tag_elems = soup.select('.tag, .post-tag, a[rel="tag"]')
            for tag in tag_elems:
                tag_text = tag.get_text(strip=True)
                if tag_text and not tag_text.startswith("#"):
                    tag_text = f"#{tag_text}"
                tags.append(tag_text)

            # 작성자 추출
            author = ""
            author_elem = soup.select_one(".author, .by-author, .post-author")
            if author_elem:
                author = author_elem.get_text(strip=True)

            # 날짜 추출
            date_elem = soup.select_one(
                'time, .date, .post-date, meta[property="article:published_time"]'
            )
            posted_at = None
            if date_elem:
                if date_elem.name == "meta":
                    date_str = date_elem.get("content", "")
                elif date_elem.name == "time":
                    date_str = date_elem.get("datetime", "") or date_elem.get_text(
                        strip=True
                    )
                else:
                    date_str = date_elem.get_text(strip=True)

                # 날짜 파싱 시도
                posted_at = self.parse_date(date_str)

            # 키워드 필터링 적용
            if not self._check_content_quality(title, content_text):
                self.logger.info(f"콘텐츠 품질 기준 미달: {url}")
                return None

            return {
                "title": title or "Untitled",
                "content_html": content_html,
                "content_text": content_text,
                "images": images,
                "category": category,
                "tags": tags,
                "author": author,
                "posted_at": posted_at,
            }

        except Exception as e:
            print(f"포스트 크롤링 오류: {e}")
            return None

    def parse_date(self, date_str):
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        try:
            # ISO 형식
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            # 다양한 날짜 형식 시도
            patterns = [
                ("%Y-%m-%d %H:%M:%S", None),
                ("%Y-%m-%d %H:%M", None),
                ("%Y-%m-%d", None),
                ("%Y. %m. %d. %H:%M", None),
                ("%Y. %m. %d.", None),
                ("%Y.%m.%d %H:%M", None),
                ("%Y.%m.%d", None),
            ]

            for pattern, _ in patterns:
                try:
                    return datetime.strptime(date_str.strip(), pattern)
                except:
                    continue

        except Exception as e:
            print(f"날짜 파싱 오류: {e}, 원본: {date_str}")

        return None

    def check_duplicate(self, blog_name, entry_id, blog_url=None):
        """중복 체크 (entry_id, blog_name, blog_url 기준)"""
        if not blog_name:
            return False
        try:
            db = get_db()
            if entry_id:
                query = """
                    SELECT id FROM 05_raw_tistory_data 
                    WHERE blog_name = %s AND entry_id = %s
                    LIMIT 1
                """
                result = db.execute_one(query, (blog_name, entry_id))
            elif blog_url:
                query = """
                    SELECT id FROM 05_raw_tistory_data 
                    WHERE blog_name = %s AND blog_url = %s
                    LIMIT 1
                """
                result = db.execute_one(query, (blog_name, blog_url))
            else:
                # entry_id와 blog_url 모두 없으면 blog_name만으로 체크 (예외적 상황)
                query = """
                    SELECT id FROM 05_raw_tistory_data 
                    WHERE blog_name = %s
                    LIMIT 1
                """
                result = db.execute_one(query, (blog_name,))
            return result is not None
        except Exception as e:
            print(f"중복 체크 오류: {e}")
            return False


    def save_to_database(self, brand_official_name, url, post_data):
        """데이터베이스에 저장 (테이블 컬럼에 맞춤)"""
        try:
            blog_name, entry_id = self.extract_blog_info(url)

            # 중복 체크 (entry_id가 없으면 blog_url까지 전달)
            if self.check_duplicate(blog_name, entry_id, url):
                print(f"  -> 이미 저장된 포스트입니다: {blog_name}/{entry_id if entry_id else url}")
                return False

            # 데이터 준비 (05_raw_tistory_data 테이블 컬럼에 맞게)
            data = {
                "brand_name": brand_official_name,
                "blog_name": blog_name,
                "entry_id": entry_id,
                "blog_url": url,
                "post_title": post_data.get("title", ""),
                "post_content": post_data.get("content_html", ""),
                "author_name": post_data.get("author", ""),
                "category": post_data.get("category", ""),
                "tags": post_data.get("tags", []),
                "images": post_data.get("images", []),
                "posted_at": post_data.get("posted_at"),
                "crawled_at": datetime.now(),
            }

            # 필수값 체크
            if not blog_name or not entry_id:
                print(f"  -> 저장 스킵: blog_name 또는 entry_id 없음 | url: {url}")
                return False
            if not data["post_title"] or not data["post_content"]:
                print(f"  -> 저장 스킵: 제목/본문 없음 | url: {url}")
                return False

            # 데이터베이스에 저장
            DataQueries.insert_raw_tistory_data(data)
            print(f"  -> 저장 완료: {post_data.get('title', 'Untitled')[:40]}...")
            return True

        except Exception as e:
            print(f"  -> 저장 실패: {e}")
            return False

    def crawl_brand_blogs(self, brand_official_name, max_pages=10):
        """브랜드 티스토리 블로그 크롤링 (brand_official_name 기반)"""
        print(f"\n브랜드 '{brand_official_name}' 티스토리 블로그 크롤링 시작...")

        saved_count = 0
        crawled_count = 0

        for page in range(1, max_pages + 1):
            print(f"\n페이지 {page} 검색 중...")

            # 검색
            urls = self.search_tistory(brand_official_name, page)
            if not urls:
                print("더 이상 검색 결과가 없습니다.")
                break

            print(f"  {len(urls)}개 URL 발견")

            # 각 URL 크롤링
            for url in urls:
                crawled_count += 1
                print(f"\n크롤링 중 [{crawled_count}]: {url[:70]}...")

                # 포스트 내용 가져오기
                post_data = self.get_post_content(url)
                if not post_data:
                    print("  -> 콘텐츠 추출 실패")
                    continue

                # 이미지 개수 체크
                if len(post_data.get("images", [])) < self.config.MIN_IMAGES:
                    print(f"  -> 이미지 부족 ({len(post_data.get('images', []))}개)")
                    self.logger.info(
                        f"이미지 부족: {url} ({len(post_data.get('images', []))}개)"
                    )
                    continue

                # 데이터베이스 저장
                if self.save_to_database(brand_official_name, url, post_data):
                    saved_count += 1

                # 크롤링 간격 (랜덤)
                self.random_delay()

            # 페이지 간 대기 (랜덤)
            self.random_delay(self.config.PAGE_DELAY, self.config.PAGE_DELAY * 2)

        print(f"\n크롤링 완료!")
        print(f"- 크롤링한 포스트: {crawled_count}개")
        print(f"- 저장된 포스트: {saved_count}개")

        self.logger.info(
            f"브랜드 '{brand_official_name}' 크롤링 완료 - 크롤링: {crawled_count}, 저장: {saved_count}"
        )

        return {
            "brand_name": brand_official_name,
            "crawled_count": crawled_count,
            "saved_count": saved_count,
        }
