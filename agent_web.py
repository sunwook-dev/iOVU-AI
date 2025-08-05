#!/usr/bin/env python3
"""
다중 페이지 전용 LangGraph SEO/GEO(Generative Engine Optimization) 최적화 시스템
@tool 데코레이터 + LangGraph 워크플로우 + 사용자 인터페이스
"""

from typing import Dict, List, Optional, TypedDict, Literal, Annotated, Set, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from dataclasses import dataclass, asdict
import asyncio
import os
import json
import time
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# from pathlib import Path

# 환경변수 로드
load_dotenv()

# Selenium 임포트 (선택적)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import WebDriverException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

    # Options 클래스를 더미로 정의
    class Options:
        def __init__(self):
            pass

        def add_argument(self, arg):
            pass

    print("⚠️ Selenium이 설치되지 않았습니다. 기본 HTTP 크롤링만 사용됩니다.")


class DatabaseManager:
    """데이터베이스 연결 및 쿼리 관리"""

    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                database=os.getenv("DB_NAME", "modular_agents_db"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", "1234"),
            )
            print("✅ 데이터베이스 연결 성공")
        except Error as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise

    def get_latest_brand_url(self):
        """가장 최근에 업데이트된 브랜드의 official_site_url 가져오기"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT brand_official_name, official_site_url, updated_at
            FROM 01_brands 
            WHERE official_site_url IS NOT NULL 
            AND official_site_url != ''
            ORDER BY updated_at DESC 
            LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            if result:
                print(
                    f"📊 최신 브랜드: {result['brand_official_name']} - {result['official_site_url']}"
                )
                return result
            else:
                print("❌ 브랜드 정보를 찾을 수 없습니다.")
                return None

        except Error as e:
            print(f"❌ 브랜드 정보 조회 실패: {e}")
            return None

    def close(self):
        """데이터베이스 연결 종료"""
        if self.connection and self.connection.is_connected():
            self.connection.close()


# ===== LangGraph State 정의 =====
class MultiPageSEOWorkflowState(TypedDict):
    """다중 페이지 SEO/GEO 워크플로우 상태"""

    # 메시지 히스토리
    messages: Annotated[List, add_messages]

    # 사용자 입력
    user_url: str
    user_mode: Literal["analyze", "optimize", "full"]
    api_key: str
    max_pages: int

    # 워크플로우 진행 상태
    current_stage: str
    next_action: str

    # 크롤링 결과
    crawl_results: List[Dict]
    crawled_files: List[str]

    # 페이지별 분석 결과
    page_analyses: List[Dict]

    # 종합 분석 결과
    site_seo_analysis: Dict
    site_geo_analysis: Dict
    site_performance: Dict
    site_structured_data: Dict
    site_keywords: Dict

    # 최적화 결과
    optimized_pages: List[Dict]
    optimization_summary: Dict

    meta_results: Dict  # 메타태그 생성 결과
    jsonld_results: Dict  # JSON-LD 생성 결과
    faq_results: Dict  # FAQ 생성 결과
    final_optimization: List[Dict]  # 최종 HTML 파일 정보
    final_html_files: List[Dict]

    # 설정
    business_type: str
    target_keywords: str

    # 결과
    output_files: List[str]
    final_summary: Dict


# ===== JSON-LD 템플릿 시스템 =====
BUSINESS_SCHEMA_TEMPLATES = {
    "법무법인": {
        "main": {
            "@context": "https://schema.org",
            "@type": ["LegalService", "ProfessionalService"],
            "name": "{company_name}",
            "description": "{description}",
            "serviceType": "법률 서비스",
            "areaServed": "대한민국",
            "url": "{url}",
        },
        "about": {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "mainEntity": {"@type": "LegalService", "name": "{company_name}"},
        },
        "service": {
            "@context": "https://schema.org",
            "@type": "Service",
            "serviceType": "법률 상담",
            "provider": {"@type": "LegalService", "name": "{company_name}"},
        },
    },
    "병원": {
        "main": {
            "@context": "https://schema.org",
            "@type": "MedicalOrganization",
            "name": "{company_name}",
            "description": "{description}",
            "medicalSpecialty": "종합의료",
            "url": "{url}",
        }
    },
    "쇼핑몰": {
        "main": {
            "@context": "https://schema.org",
            "@type": "OnlineStore",
            "name": "{company_name}",
            "description": "{description}",
            "url": "{url}",
            "paymentAccepted": ["신용카드", "계좌이체", "무통장입금"],
        },
        "product": {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "{product_name}",
            "description": "{product_description}",
            "availability": "InStock",
        },
    },
    "IT회사": {
        "main": {
            "@context": "https://schema.org",
            "@type": "Corporation",
            "name": "{company_name}",
            "description": "{description}",
            "industry": "정보기술",
            "url": "{url}",
        }
    },
    "카페": {
        "main": {
            "@context": "https://schema.org",
            "@type": "CafeOrCoffeeShop",
            "name": "{company_name}",
            "description": "{description}",
            "cuisine": "카페, 음료",
            "url": "{url}",
        }
    },
    # 기본 템플릿
    "default": {
        "main": {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "{company_name}",
            "description": "{description}",
            "url": "{url}",
        },
        "about": {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "mainEntity": {"@type": "Organization", "name": "{company_name}"},
        },
        "contact": {
            "@context": "https://schema.org",
            "@type": "ContactPage",
            "mainEntity": {"@type": "Organization", "name": "{company_name}"},
        },
        "faq": {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "mainEntity": {"@type": "Organization", "name": "{company_name}"},
        },
        "team": {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "mainEntity": {"@type": "Organization", "name": "{company_name}"},
        },
        "other": {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "{company_name}",
            "description": "{description}",
            "url": "{url}",
        },
        "product": {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "{company_name}",
            "description": "{description}",
        },
    },
}


class StreamlinedSEOGEOCrawler:
    """LLM 분석을 위한 다중 페이지 HTML 수집 크롤러"""

    def __init__(self, base_url: str, max_pages: int = 9):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.max_product_pages = 3
        self.parsed_base = urlparse(base_url)
        self.crawled_urls: Set[str] = set()
        self.results: List[Dict[str, Any]] = []

        # Chrome 옵션 설정 (Selenium 사용 가능한 경우만)
        if SELENIUM_AVAILABLE:
            self.chrome_options = Options()
            self.chrome_options.add_argument("--headless")
            self.chrome_options.add_argument("--no-sandbox")
            self.chrome_options.add_argument("--disable-dev-shm-usage")
            self.chrome_options.add_argument("--disable-gpu")
            self.chrome_options.add_argument("--window-size=1920,1080")
            self.chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        else:
            self.chrome_options = None

        # 우선순위 페이지 정의
        self.priority_pages = [
            ("main", ["", "/", "/index", "/index.html", "/home", "/main"]),
            (
                "about",
                [
                    "/about",
                    "/info",
                    "/company",
                    "/소개",
                    "/회사소개",
                    "/회사",
                    "/기업소개",
                    "/company-info",
                    "/about-us",
                ],
            ),
            (
                "service",
                [
                    "/service",
                    "/services",
                    "/서비스",
                    "/업무분야",
                    "/전문분야",
                    "/업무영역",
                    "/practice-areas",
                ],
            ),
            (
                "product",
                [
                    "/product",
                    "/products",
                    "/goods",
                    "/shop",
                    "/상품",
                    "/제품",
                    "/item",
                    "/아이템",
                ],
            ),
            (
                "faq",
                [
                    "/faq",
                    "/FAQ",
                    "/질문",
                    "/문의사항",
                    "/cs/faq",
                    "/help/faq",
                    "/자주묻는질문",
                    "/고객지원",
                    "/help",
                ],
            ),
            (
                "contact",
                [
                    "/contact",
                    "/contacts",
                    "/연락처",
                    "/문의",
                    "/상담신청",
                    "/오시는길",
                    "/location",
                    "/contact-us",
                ],
            ),
            (
                "team",
                [
                    "/team",
                    "/members",
                    "/변호사",
                    "/구성원",
                    "/직원소개",
                    "/팀소개",
                    "/lawyers",
                    "/attorneys",
                    "/staff",
                ],
            ),
        ]

        # 상품 페이지 식별 패턴
        self.product_url_patterns = [
            r"/product/\d+",
            r"/goods/\d+",
            r"/item/\d+",
            r"/shop/\d+",
            r"/p/\d+",
            r"product_no=\d+",
            r"goods_no=\d+",
            r"item_id=\d+",
            r"/상품/\d+",
            r"/제품/\d+",
        ]

    def discover_priority_urls(self) -> List[str]:
        """우선순위 기반 URL 발견"""
        print("🔍 우선순위 페이지 발견 중...")

        # 1. Sitemap에서 URL 수집
        sitemap_urls = self.get_sitemap_urls()
        # print(f"📋 Sitemap에서 {len(sitemap_urls)}개 URL 발견")

        # 2. 메인페이지에서 내부 링크 수집
        main_page_urls = self.get_internal_links_from_page(self.base_url)
        # print(f"🔗 메인페이지에서 {len(main_page_urls)}개 링크 발견")

        # 3. 직접 경로 확인
        direct_urls = self.check_direct_paths()
        # print(f"🎯 직접 경로에서 {len(direct_urls)}개 URL 확인")

        # 4. 상품 페이지 수집
        product_urls = self.discover_product_pages()
        # print(f"🛍️ 상품 페이지 {len(product_urls)}개 발견")

        # 모든 URL 통합 및 분류
        all_urls = set(sitemap_urls + main_page_urls + direct_urls + product_urls)

        # 🚨 안전장치: URL이 하나도 없으면 최소한 메인 페이지라도 추가
        if not all_urls:
            # print("⚠️ 발견된 URL이 없어 메인 페이지를 강제 추가합니다.")
            all_urls.add(self.base_url)

        # print(f"🌐 총 {len(all_urls)}개 고유 URL 수집")

        priority_urls = self.categorize_and_prioritize_urls(list(all_urls))

        # 🚨 추가 안전장치: 분류 후에도 URL이 없으면 메인 페이지 추가
        if not priority_urls:
            # print("⚠️ 분류된 URL이 없어 메인 페이지를 최종 추가합니다.")
            priority_urls = [(self.base_url, "main")]

        final_urls = priority_urls[: self.max_pages]

        # print(f"\n🎯 최종 크롤링 대상 ({len(final_urls)}개):")
        for i, (url, page_type) in enumerate(final_urls, 1):
            print(f"  {i}. [{page_type.upper()}] {url}")

        return [url for url, _ in final_urls]

    def get_sitemap_urls(self) -> List[str]:
        """sitemap.xml에서 URL 추출"""
        sitemap_candidates = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/sitemaps/sitemap.xml",
            f"{self.base_url}/wp-sitemap.xml",
        ]

        urls: Set[str] = set()

        for sitemap_url in sitemap_candidates:
            try:
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "xml")
                    for loc in soup.find_all("loc"):
                        url = loc.get_text().strip()
                        if self.is_valid_internal_url(url):
                            urls.add(url)
            except Exception:
                continue

        return list(urls)

    def get_internal_links_from_page(self, url: str) -> List[str]:
        """특정 페이지에서 내부 링크 추출"""
        if not SELENIUM_AVAILABLE:
            # print(f"⚠️ Selenium 없이 {url} 처리 중...")
            return self._get_links_with_requests(url)

        driver = None
        urls: Set[str] = set()

        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            time.sleep(3)

            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and self.is_valid_internal_url(href):
                        urls.add(href)
                except Exception:
                    continue

        except Exception as e:
            print(f"⚠️ {url}에서 링크 추출 실패: {e}")
            # Selenium 실패시 requests로 fallback
            return self._get_links_with_requests(url)
        finally:
            if driver:
                driver.quit()

        return list(urls)

    def _get_links_with_requests(self, url: str) -> List[str]:
        """requests를 사용한 링크 추출 (Selenium 대체)"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", href=True)

            urls = set()
            for link in links:
                href = link.get("href")
                if href and self.is_valid_internal_url(href):
                    # 상대 URL을 절대 URL로 변환
                    if href.startswith("/"):
                        href = self.base_url + href
                    elif not href.startswith("http"):
                        href = urljoin(url, href)
                    urls.add(href)

            return list(urls)
        except Exception as e:
            print(f"⚠️ requests로 {url} 링크 추출 실패: {e}")
            return []

    def check_direct_paths(self) -> List[str]:
        """우선순위 경로들을 직접 확인"""
        valid_urls = []

        for page_type, paths in self.priority_pages:
            if page_type == "product":  # 상품 페이지는 별도 처리
                continue

            for path in paths:
                if path in ["", "/"]:
                    test_url = self.base_url
                else:
                    test_url = self.base_url + path

                if self.check_url_exists(test_url):
                    valid_urls.append(test_url)
                    # print(f"✅ {page_type.upper()} 페이지 발견: {test_url}")

        return valid_urls

    def discover_product_pages(self) -> List[str]:
        """상품 페이지 URL 수집"""
        print("🛍️ 상품 페이지 수집 시작...")
        product_urls = set()

        # Selenium이 없어도 requests로 상품 링크 찾기
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 상품 링크 선택자들로 검색
            product_selectors = [
                'a[href*="/product/"]',
                'a[href*="/goods/"]',
                'a[href*="/item/"]',
                'a[href*="/shop/"]',
                'a[href*="/p/"]',
                'a[href*="product_no="]',
                'a[href*="goods_no="]',
                ".product-item a",
                ".goods-item a",
                ".item-link",
                ".product-link",
                '[class*="product"] a',
                '[class*="goods"] a',
                '[class*="item"] a',
            ]

            found_products = set()
            for selector in product_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get("href")
                        if href and self.is_product_url(href):
                            # 상대 URL을 절대 URL로 변환
                            if href.startswith("/"):
                                href = self.base_url + href
                            elif not href.startswith("http"):
                                href = urljoin(self.base_url, href)

                            if self.is_valid_internal_url(href):
                                found_products.add(href)
                                if len(found_products) >= self.max_product_pages * 2:
                                    break
                except Exception:
                    continue

                if len(found_products) >= self.max_product_pages * 2:
                    break

            product_urls.update(found_products)
            # print(f"   메인페이지에서 {len(found_products)}개 상품 링크 발견")

        except Exception as e:
            pass
            # print(f"⚠️ 메인페이지 상품 링크 수집 실패: {e}")

        # 유효성 검증을 더 관대하게
        valid_products = []
        for url in list(product_urls)[: self.max_product_pages * 2]:
            # check_url_exists 호출을 더 관대하게 처리
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code in [200, 301, 302]:
                    valid_products.append(url)
                    if len(valid_products) >= self.max_product_pages:
                        break
            except:
                # HEAD 요청 실패시 GET으로 재시도
                try:
                    response = requests.get(url, timeout=5, allow_redirects=True)
                    if response.status_code in [200, 301, 302]:
                        valid_products.append(url)
                        if len(valid_products) >= self.max_product_pages:
                            break
                except:
                    continue

        # print(f"✅ 최종 유효한 상품 페이지: {len(valid_products)}개")
        return valid_products

    def categorize_and_prioritize_urls(self, urls: List[str]) -> List[tuple]:
        """URL을 우선순위별로 분류하고 정렬"""
        categorized = {}

        # 각 우선순위 카테고리 초기화
        for page_type, _ in self.priority_pages:
            categorized[page_type] = []
        categorized["other"] = []

        # URL 분류
        for url in urls:
            path = urlparse(url).path.lower()
            query = urlparse(url).query.lower()
            full_url_lower = url.lower()
            categorized_flag = False

            # 상품 페이지 우선 확인
            if self.is_product_url(url):
                categorized["product"].append(url)
                categorized_flag = True
            else:
                # 기존 로직으로 분류
                for page_type, keywords in self.priority_pages:
                    if page_type == "product":  # 상품은 이미 위에서 처리
                        continue
                    if self.matches_page_type(path, query, full_url_lower, keywords):
                        categorized[page_type].append(url)
                        categorized_flag = True
                        break

            if not categorized_flag:
                categorized["other"].append(url)

        # 우선순위별로 최적의 URL 선택
        final_urls = []

        for page_type, _ in self.priority_pages:
            urls_in_category = categorized[page_type]
            if urls_in_category:
                if page_type == "product":
                    # 상품 페이지는 최대 3개 선택
                    selected_products = urls_in_category[: self.max_product_pages]
                    for product_url in selected_products:
                        final_urls.append((product_url, page_type))
                else:
                    # 다른 페이지는 1개씩
                    best_url = self.select_best_url(urls_in_category, page_type)
                    final_urls.append((best_url, page_type))

        # 기타 URL 추가 (남은 슬롯이 있다면)
        remaining_slots = self.max_pages - len(final_urls)
        if remaining_slots > 0 and categorized["other"]:
            for url in categorized["other"][:remaining_slots]:
                final_urls.append((url, "other"))

        return final_urls

    def is_product_url(self, url: str) -> bool:
        """상품 페이지 URL인지 확인"""
        for pattern in self.product_url_patterns:
            if re.search(pattern, url, re.I):
                return True
        return False

    def matches_page_type(
        self, path: str, query: str, full_url: str, keywords: List[str]
    ) -> bool:
        """경로가 특정 페이지 타입의 키워드와 일치하는지 확인"""
        # 메인페이지 특별 처리
        if "" in keywords or "/" in keywords:
            if path in [
                "",
                "/",
                "/index",
                "/index.html",
                "/home",
                "/main",
            ] or path.endswith("/index"):
                return True

        # 다른 키워드들 확인
        for keyword in keywords:
            if keyword in ["", "/"]:
                continue
            if keyword in path or keyword in query or keyword in full_url:
                return True

        return False

    def select_best_url(self, urls: List[str], page_type: str) -> str:
        """카테고리별로 가장 적절한 URL 선택"""
        if not urls:
            return ""
        if len(urls) == 1:
            return urls[0]

        # 간단한 로직: 가장 짧은 URL 선택
        return min(urls, key=len)

    def check_url_exists(self, url: str) -> bool:
        """URL이 존재하는지 확인 (더 관대한 검증)"""
        try:
            # HEAD 요청 먼저 시도
            response = requests.head(url, timeout=8, allow_redirects=True)
            if response.status_code in [
                200,
                301,
                302,
                403,
            ]:  # 403도 허용 (일부 사이트에서 HEAD 차단)
                return True
        except Exception:
            pass

        try:
            # GET 요청으로 재시도
            response = requests.get(url, timeout=8, allow_redirects=True)
            if response.status_code in [200, 301, 302]:
                return True
        except Exception:
            pass

        # 기본 페이지들은 더 관대하게 처리
        path = urlparse(url).path.lower()
        if path in ["", "/", "/index", "/index.html", "/home", "/main"]:
            return True

        return False

    def is_valid_internal_url(self, url: str) -> bool:
        """내부 URL인지 검증 (더 관대한 버전)"""
        try:
            if not url or url.strip() == "":
                return False

            # 절대 URL인 경우 도메인 체크
            if url.startswith("http"):
                parsed = urlparse(url)
                if parsed.netloc and parsed.netloc != self.parsed_base.netloc:
                    return False

            # 상대 URL인 경우 유효한 것으로 간주
            elif url.startswith("/"):
                return True

            # 제외할 확장자
            excluded_extensions = [
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".zip",
                ".doc",
                ".docx",
            ]
            if any(url.lower().endswith(ext) for ext in excluded_extensions):
                return False

            # 제외할 프로토콜
            excluded_patterns = [
                "javascript:",
                "mailto:",
                "tel:",
                "#",
                "data:",
                "blob:",
            ]
            if any(url.lower().startswith(pattern) for pattern in excluded_patterns):
                return False

            return True
        except Exception:
            return False

    def crawl_single_page(
        self, url: str, page_type: str = None
    ) -> Optional[Dict[str, Any]]:
        """단일 페이지 HTML 수집"""
        if url in self.crawled_urls:
            return None

        # page_type이 제공되지 않았으면 감지
        if page_type is None:
            page_type = self.detect_page_type(url)

        print(f"🔍 크롤링 중")
        # print(f"🔍 [{page_type.upper()}] 크롤링 중: {url}")

        if not SELENIUM_AVAILABLE:
            return self._crawl_with_requests(url, page_type)

        driver = None
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)

            # 페이지 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)

            # 페이지 HTML 전체 가져오기
            page_source = driver.page_source

            # HTML 파일로 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_type}_{timestamp}.html"
            filepath = f"outputs/{filename}"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(page_source)

            # 메타데이터 생성
            metadata = {
                "url": url,
                "page_type": page_type,
                "crawl_timestamp": datetime.now().isoformat(),
                "filename": filepath,
                "file_size": len(page_source.encode("utf-8")),
                "html_content": page_source,  # 분석용으로 HTML 포함
            }

            print(f"✅ 크롤링 데이터 저장 완료")
            self.crawled_urls.add(url)
            return metadata

        except Exception as e:
            print(f"❌ [{page_type.upper()}] Selenium 크롤링 실패 {url}: {e}")
            return self._crawl_with_requests(url, page_type)
        finally:
            if driver:
                driver.quit()

    def _crawl_with_requests(
        self, url: str, page_type: str
    ) -> Optional[Dict[str, Any]]:
        """requests를 사용한 크롤링 (Selenium 대체)"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            page_source = response.text

            # HTML 파일로 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{page_type}_{timestamp}.html"
            filepath = f"outputs/{filename}"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(page_source)

            # 메타데이터 생성
            metadata = {
                "url": url,
                "page_type": page_type,
                "crawl_timestamp": datetime.now().isoformat(),
                "filename": filepath,
                "file_size": len(page_source.encode("utf-8")),
                "html_content": page_source,
            }

            # print(f"✅ [{page_type.upper()}] requests로 저장 완료: {filename}")
            self.crawled_urls.add(url)
            return metadata

        except Exception as e:
            print(f"❌ [{page_type.upper()}] requests 크롤링도 실패 {url}: {e}")
            return None

    def detect_page_type(self, url: str) -> str:
        """페이지 타입 감지"""
        if self.is_product_url(url):
            return "product"

        path = urlparse(url).path.lower()
        query = urlparse(url).query.lower()
        full_url = url.lower()

        for page_type, keywords in self.priority_pages:
            if page_type == "product":
                continue
            if self.matches_page_type(path, query, full_url, keywords):
                return page_type

        return "other"

    def crawl_site(self) -> List[Dict[str, Any]]:
        """전체 사이트 크롤링 실행"""
        print(f"🚀 {self.base_url}  크롤링 시작")  # 다중 페이지
        # print(f"📊 최대 {self.max_pages}개 페이지 (상품 {self.max_product_pages}개 포함)")

        # URL 발견 및 크롤링
        urls_to_crawl = self.discover_priority_urls()

        if not urls_to_crawl:
            print("❌ 크롤링할 URL을 찾을 수 없습니다.")
            return []

        # print(f"\n📋 크롤링 시작 - {len(urls_to_crawl)}개 페이지")
        print(f"\n📋 크롤링 시작")

        # 각 URL 크롤링
        for i, url in enumerate(urls_to_crawl, 1):
            # print(f"\n{'='*50}")
            # print(f"진행률: {i}/{len(urls_to_crawl)}")
            result = self.crawl_single_page(url)
            if result:
                self.results.append(result)

            # 서버 부하 방지
            if i < len(urls_to_crawl):
                time.sleep(2)

        # print(f"\n🎉 다중 페이지 크롤링 완료! 총 {len(self.results)}개 페이지 수집")
        print(f"\n🎉 페이지 크롤링 완료!")
        return self.results


# ===== @tool 함수들 =====
@tool
def crawl_full_website(base_url: str, max_pages: int = 9) -> dict:
    """
    sitemap.xml 기반으로 전체 웹사이트를 크롤링합니다.

    Args:
        base_url: 크롤링할 기본 URL
        max_pages: 최대 크롤링할 페이지 수

    Returns:
        크롤링 결과 딕셔너리
    """
    try:
        crawler = StreamlinedSEOGEOCrawler(base_url, max_pages)
        crawl_results = crawler.crawl_site()

        if not crawl_results:
            return {
                "error": "크롤링된 페이지가 없습니다",
                "base_url": base_url,
                "pages_crawled": 0,
            }

        # 페이지 타입별 분류
        page_types = {}
        for result in crawl_results:
            page_type = result["page_type"]
            page_types[page_type] = page_types.get(page_type, 0) + 1

        return {
            "base_url": base_url,
            "pages_crawled": len(crawl_results),
            "crawl_results": crawl_results,
            "page_types": page_types,
            "success": True,
            "crawl_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "error": f"크롤링 실패: {str(e)}",
            "base_url": base_url,
            "pages_crawled": 0,
            "success": False,
        }


@tool
def analyze_page_from_html(
    html_content: str, url: str, page_type: str = "unknown"
) -> dict:
    """
    HTML 콘텐츠로부터 개별 페이지를 분석합니다.

    Args:
        html_content: 분석할 HTML 콘텐츠
        url: 페이지 URL
        page_type: 페이지 타입

    Returns:
        페이지 분석 결과
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # SEO 요소 분석
        analysis = {
            "url": url,
            "page_type": page_type,
            "title": {
                "content": (
                    soup.find("title").get_text().strip() if soup.find("title") else ""
                ),
                "length": (
                    len(soup.find("title").get_text().strip())
                    if soup.find("title")
                    else 0
                ),
                "good": False,
            },
            "meta_description": {"content": "", "length": 0, "good": False},
            "headings": {
                "h1_count": len(soup.find_all("h1")),
                "h1_content": [h1.get_text().strip() for h1 in soup.find_all("h1")],
                "h2_count": len(soup.find_all("h2")),
                "good": False,
            },
            "images": {
                "total": len(soup.find_all("img")),
                "without_alt": 0,
                "good": False,
            },
            "links": {"internal": 0, "external": 0, "good": False},
            "structured_data": {
                "json_ld_count": len(
                    soup.find_all("script", {"type": "application/ld+json"})
                ),
                "good": False,
            },
            "content_quality": {
                "word_count": len(soup.get_text().split()),
                "paragraph_count": len(soup.find_all("p")),
                "good": False,
            },
        }

        # Meta Description 분석
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc_content = meta_desc.get("content").strip()
            analysis["meta_description"]["content"] = desc_content
            analysis["meta_description"]["length"] = len(desc_content)
            analysis["meta_description"]["good"] = 120 <= len(desc_content) <= 160

        # Title 품질 평가
        title_length = analysis["title"]["length"]
        analysis["title"]["good"] = 30 <= title_length <= 60

        # Headings 품질 평가
        analysis["headings"]["good"] = analysis["headings"]["h1_count"] == 1

        # Images Alt 텍스트 확인
        images_without_alt = len(
            [img for img in soup.find_all("img") if not img.get("alt")]
        )
        analysis["images"]["without_alt"] = images_without_alt
        analysis["images"]["good"] = (
            images_without_alt == 0 if analysis["images"]["total"] > 0 else True
        )

        # 링크 분석
        domain = urlparse(url).netloc
        links = soup.find_all("a", href=True)
        internal_links = 0
        external_links = 0

        for link in links:
            href = link.get("href")
            if href.startswith("http"):
                if domain in href:
                    internal_links += 1
                else:
                    external_links += 1
            elif href.startswith("/"):
                internal_links += 1

        analysis["links"]["internal"] = internal_links
        analysis["links"]["external"] = external_links
        analysis["links"]["good"] = internal_links > 0

        # 구조화된 데이터 평가
        analysis["structured_data"]["good"] = (
            analysis["structured_data"]["json_ld_count"] > 0
        )

        # 콘텐츠 품질 평가
        word_count = analysis["content_quality"]["word_count"]
        analysis["content_quality"]["good"] = word_count >= 300

        # 개별 페이지 SEO 점수 계산
        score_factors = [
            analysis["title"]["good"],
            analysis["meta_description"]["good"],
            analysis["headings"]["good"],
            analysis["images"]["good"],
            analysis["links"]["good"],
            analysis["structured_data"]["good"],
            analysis["content_quality"]["good"],
        ]

        seo_score = (sum(score_factors) / len(score_factors)) * 100
        analysis["seo_score"] = round(seo_score, 1)

        return analysis

    except Exception as e:
        return {
            "error": f"페이지 분석 실패: {str(e)}",
            "url": url,
            "page_type": page_type,
            "seo_score": 0,
        }


@tool
def calculate_site_geo_scores(crawl_results: list) -> dict:
    """
    크롤링된 전체 사이트의 GEO 점수를 계산합니다.

    Args:
        crawl_results: 크롤링 결과 리스트

    Returns:
        사이트 전체 GEO 점수
    """
    try:
        total_pages = len(crawl_results)
        if total_pages == 0:
            return {"error": "분석할 페이지가 없습니다"}

        # 각 페이지별 GEO 점수 계산
        page_geo_scores = []

        for result in crawl_results:
            html_content = result.get("html_content", "")
            url = result.get("url", "")

            if not html_content:
                continue

            soup = BeautifulSoup(html_content, "html.parser")
            page_text = soup.get_text()

            # GEO 6가지 기준 평가
            geo_scores = {
                "clarity": evaluate_clarity(soup, page_text)["score"],
                "structure": evaluate_structure(soup, page_text)["score"],
                "context": evaluate_context(soup, page_text)["score"],
                "alignment": evaluate_alignment(soup, page_text)["score"],
                "timeliness": evaluate_timeliness(soup, page_text)["score"],
                "originality": evaluate_originality(soup, page_text)["score"],
            }

            page_total = sum(geo_scores.values()) / len(geo_scores)

            page_geo_scores.append(
                {
                    "url": url,
                    "page_type": result.get("page_type", "unknown"),
                    "scores": geo_scores,
                    "total_score": round(page_total, 1),
                }
            )

        # 사이트 전체 평균 계산
        if not page_geo_scores:
            return {"error": "GEO 점수를 계산할 수 있는 페이지가 없습니다"}

        site_averages = {
            "clarity": sum(p["scores"]["clarity"] for p in page_geo_scores)
            / len(page_geo_scores),
            "structure": sum(p["scores"]["structure"] for p in page_geo_scores)
            / len(page_geo_scores),
            "context": sum(p["scores"]["context"] for p in page_geo_scores)
            / len(page_geo_scores),
            "alignment": sum(p["scores"]["alignment"] for p in page_geo_scores)
            / len(page_geo_scores),
            "timeliness": sum(p["scores"]["timeliness"] for p in page_geo_scores)
            / len(page_geo_scores),
            "originality": sum(p["scores"]["originality"] for p in page_geo_scores)
            / len(page_geo_scores),
        }

        site_total_geo = sum(site_averages.values()) / len(site_averages)

        return {
            "site_geo_score": round(site_total_geo, 1),
            "site_averages": {k: round(v, 1) for k, v in site_averages.items()},
            "page_scores": page_geo_scores,
            "pages_analyzed": len(page_geo_scores),
            "recommendations": generate_site_geo_recommendations(site_averages),
        }

    except Exception as e:
        return {"error": f"사이트 GEO 점수 계산 실패: {str(e)}", "site_geo_score": 0}


@tool
def calculate_site_average_scores(page_analyses: list) -> dict:
    """
    개별 페이지 분석 결과를 종합하여 사이트 평균 점수를 계산합니다.

    Args:
        page_analyses: 페이지별 분석 결과 리스트

    Returns:
        사이트 종합 분석 결과
    """
    try:
        if not page_analyses:
            return {"error": "분석할 페이지가 없습니다"}

        valid_analyses = [
            p for p in page_analyses if not p.get("error") and p.get("seo_score", 0) > 0
        ]

        if not valid_analyses:
            return {"error": "유효한 분석 결과가 없습니다"}

        # 평균 점수 계산
        avg_seo_score = sum(p["seo_score"] for p in valid_analyses) / len(
            valid_analyses
        )

        # 페이지 타입별 분류
        page_types = {}
        for analysis in valid_analyses:
            page_type = analysis.get("page_type", "unknown")
            if page_type not in page_types:
                page_types[page_type] = []
            page_types[page_type].append(analysis)

        # 페이지 타입별 평균 점수
        type_averages = {}
        for page_type, analyses in page_types.items():
            type_avg = sum(a["seo_score"] for a in analyses) / len(analyses)
            type_averages[page_type] = round(type_avg, 1)

        # 종합 문제점 분석
        common_issues = analyze_common_issues(valid_analyses)

        # 우선순위 개선 항목
        priority_improvements = generate_priority_improvements(
            valid_analyses, common_issues
        )

        return {
            "site_average_seo_score": round(avg_seo_score, 1),
            "pages_analyzed": len(valid_analyses),
            "page_type_averages": type_averages,
            "page_analyses": valid_analyses,
            "common_issues": common_issues,
            "priority_improvements": priority_improvements,
            "success": True,
        }

    except Exception as e:
        return {"error": f"사이트 평균 점수 계산 실패: {str(e)}", "success": False}


# ===== GEO 평가 함수들 =====
def evaluate_clarity(soup: BeautifulSoup, page_text: str) -> dict:
    """명확성 평가"""
    score = 0
    details = {"specific_facts": 0, "clear_statements": 0, "contact_info": 0}

    # 구체적인 사실/수치 확인
    numeric_patterns = re.findall(r"\d+[%년도원달러$€₩]|\d+\.\d+", page_text)
    details["specific_facts"] = len(numeric_patterns)
    if len(numeric_patterns) >= 10:
        score += 30
    elif len(numeric_patterns) >= 5:
        score += 20
    elif len(numeric_patterns) >= 1:
        score += 10

    # 명확한 진술문 확인
    clear_indicators = ["입니다", "합니다", "제공합니다", "전문", "최고"]
    clear_count = sum(
        page_text.lower().count(indicator) for indicator in clear_indicators
    )
    details["clear_statements"] = clear_count
    if clear_count >= 20:
        score += 25
    elif clear_count >= 10:
        score += 15
    elif clear_count >= 5:
        score += 10

    # 연락처 정보
    contact_patterns = [
        r"(\d{2,3}-\d{3,4}-\d{4})",
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    ]
    contact_count = sum(
        len(re.findall(pattern, page_text)) for pattern in contact_patterns
    )
    details["contact_info"] = contact_count
    if contact_count >= 2:
        score += 45
    elif contact_count >= 1:
        score += 25

    return {"score": min(score, 100), "details": details}


def evaluate_structure(soup: BeautifulSoup, page_text: str) -> dict:
    """구조성 평가"""
    score = 0
    details = {"headings": 0, "lists": 0, "schema": 0}

    # 헤딩 구조
    h_tags = len(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]))
    details["headings"] = h_tags
    if h_tags >= 5:
        score += 30
    elif h_tags >= 3:
        score += 20
    elif h_tags >= 1:
        score += 10

    # 리스트 구조
    lists = len(soup.find_all(["ul", "ol", "dl"]))
    details["lists"] = lists
    if lists >= 3:
        score += 25
    elif lists >= 1:
        score += 15

    # Schema 마크업
    schema_count = len(soup.find_all("script", {"type": "application/ld+json"}))
    details["schema"] = schema_count
    if schema_count >= 1:
        score += 45

    return {"score": min(score, 100), "details": details}


def evaluate_context(soup: BeautifulSoup, page_text: str) -> dict:
    """맥락성 평가"""
    score = 0
    details = {"word_count": 0, "topics": 0}

    word_count = len(page_text.split())
    details["word_count"] = word_count
    if word_count >= 1000:
        score += 40
    elif word_count >= 500:
        score += 25
    elif word_count >= 200:
        score += 15

    # 주제 다양성
    paragraphs = soup.find_all("p")
    unique_topics = set()
    for p in paragraphs:
        words = re.findall(r"[가-힣]{2,}", p.get_text())
        unique_topics.update(words)

    details["topics"] = len(unique_topics)
    if len(unique_topics) >= 50:
        score += 35
    elif len(unique_topics) >= 25:
        score += 20
    elif len(unique_topics) >= 10:
        score += 10

    # 멀티미디어
    multimedia = len(soup.find_all(["img", "video", "iframe"]))
    if multimedia >= 5:
        score += 25
    elif multimedia >= 1:
        score += 15

    return {"score": min(score, 100), "details": details}


def evaluate_alignment(soup: BeautifulSoup, page_text: str) -> dict:
    """정합성 평가"""
    score = 0
    details = {"alt_quality": 0, "consistency": 0}

    # 이미지 ALT 품질
    images = soup.find_all("img")
    quality_alt = sum(
        1 for img in images if img.get("alt") and len(img.get("alt", "")) >= 5
    )
    details["alt_quality"] = quality_alt
    if images and quality_alt / len(images) >= 0.8:
        score += 50
    elif images and quality_alt / len(images) >= 0.5:
        score += 30

    # 용어 일관성
    title = soup.find("title")
    h1 = soup.find("h1")
    if title and h1:
        title_words = set(title.get_text().lower().split())
        h1_words = set(h1.get_text().lower().split())
        if title_words.intersection(h1_words):
            score += 50
            details["consistency"] = 1

    return {"score": min(score, 100), "details": details}


def evaluate_timeliness(soup: BeautifulSoup, page_text: str) -> dict:
    """시의성 평가"""
    score = 0
    details = {"dates": 0, "recent_keywords": 0}

    # 날짜 및 최신성 키워드
    date_patterns = [r"20\d{2}년", r"최근", r"최신", r"새로운"]
    date_count = sum(
        len(re.findall(pattern, page_text, re.I)) for pattern in date_patterns
    )
    details["dates"] = date_count
    if date_count >= 10:
        score += 60
    elif date_count >= 5:
        score += 40
    elif date_count >= 1:
        score += 20

    # 시의성 키워드
    current_keywords = ["현재", "지금", "오늘", "이번", "트렌드"]
    current_count = sum(
        page_text.lower().count(keyword) for keyword in current_keywords
    )
    details["recent_keywords"] = current_count
    if current_count >= 5:
        score += 40
    elif current_count >= 2:
        score += 20

    return {"score": min(score, 100), "details": details}


def evaluate_originality(soup: BeautifulSoup, page_text: str) -> dict:
    """독창성 평가"""
    score = 0
    details = {"insights": 0, "data": 0}

    # 독창적 통찰
    insight_keywords = ["경험상", "분석하면", "발견했습니다", "연구"]
    insight_count = sum(
        page_text.lower().count(keyword) for keyword in insight_keywords
    )
    details["insights"] = insight_count
    if insight_count >= 5:
        score += 50
    elif insight_count >= 2:
        score += 30
    elif insight_count >= 1:
        score += 15

    # 고유 데이터/통계
    data_indicators = ["조사", "통계", "데이터", "자체"]
    data_count = sum(page_text.lower().count(keyword) for keyword in data_indicators)
    details["data"] = data_count
    if data_count >= 5:
        score += 50
    elif data_count >= 2:
        score += 30
    elif data_count >= 1:
        score += 15

    return {"score": min(score, 100), "details": details}


def generate_site_geo_recommendations(site_averages: dict) -> list:
    """사이트 전체 GEO 추천사항 생성"""
    recommendations = []

    for criterion, score in site_averages.items():
        if score < 60:
            if criterion == "clarity":
                recommendations.append("전 페이지에 구체적 정보와 연락처 보강 필요")
            elif criterion == "structure":
                recommendations.append("사이트 전체 헤딩 구조와 Schema 마크업 개선")
            elif criterion == "context":
                recommendations.append("모든 페이지의 콘텐츠 분량과 깊이 확대")
            elif criterion == "alignment":
                recommendations.append("이미지 ALT 속성과 용어 일관성 전사적 개선")
            elif criterion == "timeliness":
                recommendations.append("사이트 전체 최신 정보 업데이트")
            elif criterion == "originality":
                recommendations.append("독창적 콘텐츠와 고유 데이터 전 페이지 확대")

    return recommendations


def analyze_common_issues(page_analyses: list) -> dict:
    """페이지들의 공통 문제점 분석"""
    issues = {
        "title_issues": 0,
        "description_issues": 0,
        "h1_issues": 0,
        "alt_issues": 0,
        "schema_issues": 0,
        "content_issues": 0,
    }

    total_pages = len(page_analyses)

    for analysis in page_analyses:
        if not analysis.get("title", {}).get("good"):
            issues["title_issues"] += 1
        if not analysis.get("meta_description", {}).get("good"):
            issues["description_issues"] += 1
        if not analysis.get("headings", {}).get("good"):
            issues["h1_issues"] += 1
        if not analysis.get("images", {}).get("good"):
            issues["alt_issues"] += 1
        if not analysis.get("structured_data", {}).get("good"):
            issues["schema_issues"] += 1
        if not analysis.get("content_quality", {}).get("good"):
            issues["content_issues"] += 1

    # 비율로 변환
    for issue_type in issues:
        issues[issue_type] = round((issues[issue_type] / total_pages) * 100, 1)

    return issues


def generate_priority_improvements(page_analyses: list, common_issues: dict) -> list:
    """우선순위 개선 항목 생성"""
    improvements = []

    # 80% 이상의 페이지에 문제가 있는 항목을 우선순위로
    if common_issues["title_issues"] >= 80:
        improvements.append(
            {
                "priority": "높음",
                "issue": "Title 태그 최적화",
                "affected_pages": f"{common_issues['title_issues']}%",
                "impact": "검색 결과 클릭률 20-30% 향상",
            }
        )

    if common_issues["description_issues"] >= 80:
        improvements.append(
            {
                "priority": "높음",
                "issue": "Meta Description 개선",
                "affected_pages": f"{common_issues['description_issues']}%",
                "impact": "검색 결과 요약 품질 개선",
            }
        )

    if common_issues["schema_issues"] >= 60:
        improvements.append(
            {
                "priority": "중간",
                "issue": "구조화된 데이터 추가",
                "affected_pages": f"{common_issues['schema_issues']}%",
                "impact": "리치 스니펫 및 AI 검색 대응",
            }
        )

    if common_issues["h1_issues"] >= 70:
        improvements.append(
            {
                "priority": "중간",
                "issue": "H1 태그 구조 정리",
                "affected_pages": f"{common_issues['h1_issues']}%",
                "impact": "페이지 구조 및 접근성 개선",
            }
        )

    if common_issues["alt_issues"] >= 50:
        improvements.append(
            {
                "priority": "낮음",
                "issue": "이미지 ALT 속성 추가",
                "affected_pages": f"{common_issues['alt_issues']}%",
                "impact": "접근성 및 이미지 검색 개선",
            }
        )

    return improvements


# ===== JSON-LD 생성 함수들 =====
def extract_page_data_from_analysis(
    seo_analysis: dict, url: str, page_type: str
) -> dict:
    """이미 분석된 데이터에서 JSON-LD용 데이터 추출"""
    try:
        # 이미 분석된 데이터에서 추출
        title_data = seo_analysis.get("title", {})
        desc_data = seo_analysis.get("meta_description", {})
        h1_data = seo_analysis.get("headings", {})

        company_name = title_data.get("content", "")
        description = desc_data.get("content", "")

        # H1에서 추가 정보 (이미 추출됨)
        h1_contents = h1_data.get("h1_content", [])
        if h1_contents and not company_name:
            company_name = h1_contents[0]

        # 간단한 정리
        if company_name:
            # 불필요한 부분 제거 (예: "- 홈페이지", "| 회사명" 등)
            company_name = re.sub(r"\s*[-|]\s*.*$", "", company_name).strip()

        return {
            "company_name": company_name or "웹사이트",
            "description": description or "비즈니스 웹사이트입니다.",
            "url": url,
            "page_type": page_type,
            "h1_content": h1_contents[0] if h1_contents else "",
        }

    except Exception as e:
        return {
            "company_name": "웹사이트",
            "description": "비즈니스 웹사이트입니다.",
            "url": url,
            "page_type": page_type,
            "h1_content": "",
        }


def generate_template_schema(
    business_type: str, page_type: str, page_data: dict
) -> dict:
    """템플릿 기반 JSON-LD 생성"""
    try:
        # 비즈니스 타입 매핑
        template_key = business_type
        if business_type not in BUSINESS_SCHEMA_TEMPLATES:
            template_key = "default"

        # 페이지 타입별 템플릿 선택
        templates = BUSINESS_SCHEMA_TEMPLATES[template_key]
        if page_type not in templates:
            if "main" in templates:
                page_type = "main"  # 기본값
            else:
                page_type = list(templates.keys())[0]  # 첫 번째 사용 가능한 템플릿

        # 템플릿 복사 및 데이터 치환
        schema_template = json.loads(json.dumps(templates[page_type]))

        # 문자열 치환
        schema_json = json.dumps(schema_template, ensure_ascii=False)
        for key, value in page_data.items():
            placeholder = "{" + key + "}"
            schema_json = schema_json.replace(placeholder, str(value))

        # 남은 placeholder 제거
        import re

        schema_json = re.sub(r"\{[^}]+\}", "정보없음", schema_json)

        schema = json.loads(schema_json)

        html_schema = f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>'

        return {
            "generated_schemas": [schema],
            "schema_types": [schema.get("@type", "Organization")],
            "html_schemas": [html_schema],
            "combined_html": html_schema,
            "extraction_notes": f"템플릿 기반 {business_type} {page_type} 스키마",
            "generation_method": "template_based",
            "success": True,
        }

    except Exception as e:
        # print(f"      ❌ 템플릿 스키마 생성 실패: {e}")
        return generate_fallback_jsonld(
            business_type,
            page_type,
            page_data.get("company_name", ""),
            page_data.get("description", ""),
        )


def generate_fallback_jsonld(
    business_type: str, page_type: str, title: str, description: str
) -> dict:
    """LLM 생성 실패시 기본 JSON-LD 반환"""

    # 비즈니스 타입별 기본 스키마 매핑
    business_schema_mapping = {
        "법무법인": "LegalService",
        "병원": "MedicalOrganization",
        "카페": "CafeOrCoffeeShop",
        "IT회사": "Corporation",
        "쇼핑몰": "OnlineStore",
        "온라인쇼핑몰": "OnlineStore",
        "이커머스": "OnlineStore",
        "교육기관": "EducationalOrganization",
        "부동산": "RealEstateAgent",
        "미용실": "BeautySalon",
    }

    schema_type = business_schema_mapping.get(business_type, "Organization")

    basic_schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": title or f"{business_type} 웹사이트",
        "description": description or f"{business_type} 전문 서비스를 제공합니다.",
    }

    # 페이지 타입별 추가 속성
    if page_type == "main":
        basic_schema["@type"] = ["Organization", schema_type]
    elif page_type == "contact":
        basic_schema["contactPoint"] = {
            "@type": "ContactPoint",
            "contactType": "customer service",
        }

    schema_html = f'<script type="application/ld+json">\n{json.dumps(basic_schema, ensure_ascii=False, indent=2)}\n</script>'

    return {
        "business_type": business_type,
        "page_type": page_type,
        "generated_schemas": [basic_schema],
        "schema_types": [schema_type],
        "html_schemas": [schema_html],
        "combined_html": schema_html,
        "extraction_notes": f"{business_type} 기본 템플릿 사용",
        "generation_method": "fallback_template",
        "success": True,
    }


@tool
def generate_jsonld_with_llm(
    business_type: str,
    seo_analysis: dict,
    page_type: str,
    api_key: str,
    url: str = "",
    use_llm_enhancement: bool = True,
) -> dict:
    """
    하이브리드 JSON-LD 생성: 템플릿 우선 + LLM 보완

    Args:
        business_type: 비즈니스 타입
        seo_analysis: SEO 분석 결과
        page_type: 페이지 타입
        api_key: OpenAI API 키
        url: 페이지 URL
        use_llm_enhancement: True면 LLM으로 개선 시도, False면 템플릿만 사용
    Returns:
        생성된 JSON-LD 스키마들
    """
    try:
        # print(f"      🔧 하이브리드 JSON-LD 생성: {business_type} {page_type}")

        # 1단계: 이미 분석된 데이터에서 정보 추출 (HTML 재파싱 없음)
        page_data = extract_page_data_from_analysis(seo_analysis, url, page_type)
        # print(f"         📊 기존 분석에서 추출: {page_data['company_name']}")

        # 2단계: 템플릿 기반 기본 스키마 생성
        template_result = generate_template_schema(business_type, page_type, page_data)
        print(f"         ✅ 템플릿 스키마 생성 완료")

        # 3단계: LLM 개선 시도 (선택적) - 필요시에만
        if api_key and use_llm_enhancement:
            # LLM은 원본 HTML이 필요하므로 별도 처리
            # 하지만 실패해도 템플릿으로 대체 가능
            pass  # 여기서는 템플릿 우선으로 단순화

        return template_result

    except Exception as e:
        print(f"      ❌ 하이브리드 JSON-LD 생성 실패: {e}")
        return generate_fallback_jsonld(
            business_type,
            page_type,
            page_data.get("company_name", ""),
            page_data.get("description", ""),
        )


@tool
def generate_meta_tags_with_llm(
    html_content: str,
    url: str,
    page_type: str,
    seo_analysis: dict,
    business_type: str,
    api_key: str,
) -> dict:
    """
    LLM을 사용하여 최적화된 메타태그 생성

    Args:
        html_content: HTML 콘텐츠
        url: 페이지 URL
        page_type: 페이지 타입
        seo_analysis: SEO 분석 결과
        business_type: 비즈니스 타입
        api_key: OpenAI API 키

    Returns:
        생성된 메타태그들
    """
    try:
        # HTML에서 텍스트 추출
        if "<html" in html_content or "<div" in html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            content_text = soup.get_text()
        else:
            content_text = html_content

        # 콘텐츠 길이 제한
        if len(content_text) > 3000:
            content_text = content_text[:3000] + "..."

        if not api_key:
            # API 키가 없으면 기본 메타태그 생성
            return generate_basic_meta_tags(seo_analysis, url, page_type, business_type)

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

        meta_generation_prompt = f"""
        다음 정보를 바탕으로 SEO 최적화된 메타태그들을 생성해주세요.
        
        **페이지 정보:**
        - URL: {url}
        - 페이지 타입: {page_type}
        - 비즈니스 타입: {business_type}
        - 현재 Title: {seo_analysis.get('title', {}).get('content', '')}
        - 현재 Description: {seo_analysis.get('meta_description', {}).get('content', '')}
        
        **웹페이지 콘텐츠:**
        {content_text}
        
        **생성 지침:**
        1. Title: 30-60자, 키워드 포함, 클릭 유도
        2. Meta Description: 120-160자, 요약 + 행동 유도
        3. Keywords: 관련 키워드 5-10개
        4. Open Graph 태그: 소셜 미디어 최적화
        5. Twitter Card 태그
        6. 기타 SEO 메타태그들
        
        JSON 형식으로 응답해주세요:
        ```json
        {{
            "title": "최적화된 타이틀",
            "meta_description": "최적화된 메타 디스크립션",
            "keywords": ["키워드1", "키워드2", "키워드3"],
            "og_title": "Open Graph 타이틀",
            "og_description": "Open Graph 디스크립션",
            "og_type": "website",
            "twitter_title": "트위터 타이틀",
            "twitter_description": "트위터 디스크립션",
            "canonical_url": "{url}",
            "robots": "index, follow",
            "html_meta_tags": "완성된 HTML 메타태그들"
        }}
        ```
        """

        response = llm.invoke([HumanMessage(content=meta_generation_prompt)])
        response_text = response.content.strip()

        # JSON 블록 추출
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        meta_data = json.loads(response_text)

        # HTML 메타태그 생성
        html_tags = f"""
<title>{meta_data.get('title', '')}</title>
<meta name="description" content="{meta_data.get('meta_description', '')}">
<meta name="keywords" content="{', '.join(meta_data.get('keywords', []))}">
<meta name="robots" content="{meta_data.get('robots', 'index, follow')}">
<link rel="canonical" href="{meta_data.get('canonical_url', url)}">

<!-- Open Graph -->
<meta property="og:title" content="{meta_data.get('og_title', '')}">
<meta property="og:description" content="{meta_data.get('og_description', '')}">
<meta property="og:type" content="{meta_data.get('og_type', 'website')}">
<meta property="og:url" content="{url}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{meta_data.get('twitter_title', '')}">
<meta name="twitter:description" content="{meta_data.get('twitter_description', '')}">
"""

        return {
            "title": meta_data.get("title", ""),
            "meta_description": meta_data.get("meta_description", ""),
            "keywords": meta_data.get("keywords", []),
            "og_tags": {
                "title": meta_data.get("og_title", ""),
                "description": meta_data.get("og_description", ""),
                "type": meta_data.get("og_type", "website"),
            },
            "twitter_tags": {
                "title": meta_data.get("twitter_title", ""),
                "description": meta_data.get("twitter_description", ""),
            },
            "html_meta_tags": html_tags,
            "generation_method": "llm_optimized",
            "success": True,
        }

    except Exception as e:
        print(f"⚠️ 메타태그 생성 실패: {e}")
        return generate_basic_meta_tags(seo_analysis, url, page_type, business_type)


def generate_basic_meta_tags(
    seo_analysis: dict, url: str, page_type: str, business_type: str
) -> dict:
    """기본 메타태그 생성 (API 키 없을 때)"""
    try:
        title = seo_analysis.get("title", {}).get("content", f"{page_type} 페이지")
        description = seo_analysis.get("meta_description", {}).get(
            "content", f"{business_type} {page_type} 페이지입니다."
        )

        # 기본 키워드 생성
        keywords = [business_type, page_type, "웹사이트"]

        html_tags = f"""
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{', '.join(keywords)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">

<!-- Open Graph -->
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
"""

        return {
            "title": title,
            "meta_description": description,
            "keywords": keywords,
            "og_tags": {"title": title, "description": description, "type": "website"},
            "twitter_tags": {"title": title, "description": description},
            "html_meta_tags": html_tags,
            "generation_method": "basic_template",
            "success": True,
        }
    except Exception as e:
        return {
            "title": "",
            "meta_description": "",
            "keywords": [],
            "html_meta_tags": "",
            "generation_method": "fallback",
            "success": False,
            "error": str(e),
        }


@tool
def generate_intelligent_faq_with_llm(
    website_content: str, business_type: str, api_key: str, keywords: list
) -> dict:
    """
    LLM을 사용하여 지능형 FAQ 생성

    Args:
        website_content: 웹사이트 콘텐츠
        business_type: 비즈니스 타입
        api_key: OpenAI API 키
        keywords: 키워드 리스트

    Returns:
        생성된 FAQ 데이터
    """
    try:
        if not api_key:
            # API 키가 없으면 기본 FAQ 생성
            return generate_basic_faq(business_type)

        if "<html" in website_content or "<div" in website_content:
            soup = BeautifulSoup(website_content, "html.parser")
            content_text = soup.get_text()
        else:
            content_text = website_content

        # 콘텐츠 길이 제한
        if len(content_text) > 3000:
            content_text = content_text[:3000] + "..."

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

        faq_prompt = f"""
        다음 웹사이트 콘텐츠를 바탕으로 {business_type}에 적합한 FAQ를 생성해주세요.
        
        **비즈니스 타입**: {business_type}
        **웹사이트 콘텐츠**: {content_text}
        
        다음 JSON 형식으로 5-7개의 FAQ를 생성해주세요:
        {{
            "generated_faqs": [
                {{
                    "question": "고객이 자주 묻는 질문",
                    "answer": "명확하고 도움이 되는 답변",
                    "category": "서비스/가격/절차 등"
                }}
            ],
            "faq_count": 생성된_FAQ_개수,
            "business_context": "비즈니스 맥락 설명"
        }}
        
        JSON 형식으로만 응답해주세요.
        """

        response = llm.invoke([HumanMessage(content=faq_prompt)])
        response_text = response.content.strip()

        # JSON 파싱
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        faq_data = json.loads(response_text)

        return {
            "generated_faqs": faq_data.get("generated_faqs", []),
            "faq_count": len(faq_data.get("generated_faqs", [])),
            "business_context": faq_data.get("business_context", ""),
            "generation_method": "llm_intelligent",
            "success": True,
        }

    except Exception as e:
        print(f"⚠️ FAQ 생성 실패: {e}")
        return generate_basic_faq(business_type)


def generate_basic_faq(business_type: str) -> dict:
    """기본 FAQ 생성 (API 키 없을 때)"""
    basic_faqs = [
        {
            "question": f"{business_type} 서비스는 어떤 것이 있나요?",
            "answer": f"다양한 {business_type} 관련 서비스를 제공합니다. 자세한 내용은 문의해 주세요.",
            "category": "서비스",
        },
        {
            "question": "상담은 어떻게 받을 수 있나요?",
            "answer": "전화나 온라인으로 상담 예약을 하실 수 있습니다.",
            "category": "상담",
        },
        {
            "question": "운영시간은 어떻게 되나요?",
            "answer": "평일 오전 9시부터 오후 6시까지 운영합니다.",
            "category": "운영",
        },
    ]

    return {
        "generated_faqs": basic_faqs,
        "faq_count": len(basic_faqs),
        "business_context": f"{business_type} 기본 FAQ",
        "generation_method": "basic_template",
        "success": True,
    }


# ===== LangGraph 노드 함수들 =====
# user_input_node를 db_input_node로 변경
def db_input_node(state: MultiPageSEOWorkflowState) -> MultiPageSEOWorkflowState:
    """DB에서 브랜드 정보를 자동으로 가져오는 노드"""
    print("🚀 DB 기반 SEO/GEO 최적화 시스템")
    print("=" * 60)

    # 데이터베이스에서 최신 브랜드 정보 가져오기
    try:
        db_manager = DatabaseManager()
        brand_info = db_manager.get_latest_brand_url()
        db_manager.close()
    except Exception as e:
        print(f"⚠️ DB 연결 실패: {e}")
        print("🧪 테스트 모드로 전환합니다.")
        # 테스트용 더미 데이터
        brand_info = {
            # "id": 1,
            "brand_official_name": "uniformbridge",
            "official_site_url": "https://uniformbridge.com/",  # 또는 원하는 테스트 URL
            "updated_at": datetime.now(),
        }
        if not brand_info:
            state["messages"] = [
                AIMessage(
                    content="❌ 데이터베이스에서 브랜드 정보를 가져올 수 없습니다."
                )
            ]
            state["next_action"] = "handle_error"
            return state

    # 브랜드 정보 설정
    state["brand_info"] = brand_info
    state["user_url"] = brand_info["official_site_url"]
    state["business_type"] = brand_info["brand_official_name"]

    # 환경변수에서 OpenAI API 키 가져오기
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        state["user_mode"] = "analyze"
    else:
        state["user_mode"] = "full"
        print("✅ OpenAI API 키가 환경변수에서 로드되었습니다.")

    state["api_key"] = api_key or ""
    state["max_pages"] = 9
    state["target_keywords"] = ""
    state["crawl_results"] = []
    state["crawled_files"] = []
    state["page_analyses"] = []

    # 시작 메시지 추가
    state["messages"] = [
        SystemMessage(
            content="당신은 DB 기반 다중 페이지 SEO/GEO 최적화 전문가입니다."
        ),
        HumanMessage(
            content=f"브랜드 {brand_info['brand_official_name']}의 웹사이트 {state['user_url']}을 처리해주세요."
        ),
    ]

    state["current_stage"] = "db_input_received"
    state["next_action"] = "start_crawling"

    print(f"✅ DB에서 브랜드 정보 로드 완료:")
    print(f"   • 브랜드: {brand_info['brand_official_name']}")
    print(f"   • URL: {state['user_url']}")
    print("📊 곧 크롤링을 시작합니다...")
    return state


def crawling_node(state: MultiPageSEOWorkflowState) -> MultiPageSEOWorkflowState:
    """다중 페이지 크롤링 노드"""
    print("🕷️ 사이트 전체 크롤링 시작...")

    try:
        url = state["user_url"]
        max_pages = state["max_pages"]

        # 다중 페이지 크롤링 실행
        # print(f"   📊 최대 {max_pages}개 페이지 크롤링...")
        crawl_result = crawl_full_website.invoke(
            {"base_url": url, "max_pages": max_pages}
        )

        if crawl_result.get("error"):
            state["messages"].append(
                AIMessage(content=f"크롤링 실패: {crawl_result['error']}")
            )
            state["next_action"] = "handle_error"
            return state

        crawl_results = crawl_result["crawl_results"]
        state["crawl_results"] = crawl_results

        # 크롤링된 파일 목록 저장
        crawled_files = [
            result["filename"] for result in crawl_results if "filename" in result
        ]
        state["crawled_files"] = crawled_files

        # print(f"   ✅ {len(crawl_results)}개 페이지 크롤링 완료")

        # 페이지 타입별 분포 출력
        page_types = crawl_result["page_types"]
        # print("   📋 페이지 타입별 분포:")
        for page_type, count in page_types.items():
            pass
            # print(f"      • {page_type.upper()}: {count}개")

        # 메시지 히스토리 업데이트
        state["messages"].append(
            AIMessage(
                content=f"""
        🕷️ 다중 페이지 크롤링이 완료되었습니다:
        
        📊 **크롤링 결과**:
        • 총 페이지 수: {len(crawl_results)}개
        • 페이지 타입: {', '.join([f'{k}({v})' for k, v in page_types.items()])}
        • 생성된 파일: {len(crawled_files)}개
        
        📁 **생성된 HTML 파일들**:
        {chr(10).join(['• ' + f for f in crawled_files[:10]])}
        {'• ...' if len(crawled_files) > 10 else ''}
        
        다음 단계로 각 페이지 분석을 시작합니다.
        """
            )
        )

        state["current_stage"] = "crawling_completed"
        state["next_action"] = "start_page_analysis"

    except Exception as e:
        state["messages"].append(AIMessage(content=f"크롤링 실패: {str(e)}"))
        state["next_action"] = "handle_error"
        print(f"❌ 크롤링 실패: {e}")

    return state


def enhanced_page_analysis_node(
    state: MultiPageSEOWorkflowState,
) -> MultiPageSEOWorkflowState:
    """강화된 페이지 분석 노드 - JSON-LD 자동 생성 포함"""
    print("📊 각 페이지별 SEO/GEO + JSON-LD 분석 중...")

    try:
        crawl_results = state["crawl_results"]
        page_analyses = []

        # 각 페이지별 통합 분석 + JSON-LD 생성
        for i, result in enumerate(crawl_results, 1):
            url = result["url"]
            page_type = result["page_type"]
            html_content = result.get("html_content", "")

            # print(f"   📄 [{page_type.upper()}] 분석 중... ({i}/{len(crawl_results)})")

            # 기존 SEO 분석
            seo_analysis = analyze_page_from_html.invoke(
                {"html_content": html_content, "url": url, "page_type": page_type}
            )

            # GEO 분석
            geo_analysis = calculate_site_geo_scores.invoke({"crawl_results": [result]})

            if not seo_analysis.get("error"):
                # 🆕 JSON-LD 자동 생성 추가
                print(f"      🤖 JSON-LD 자동 생성...")
                jsonld_result = generate_jsonld_with_llm.invoke(
                    {
                        "business_type": state.get("business_type", "일반 비즈니스"),
                        "seo_analysis": seo_analysis,
                        "page_type": page_type,
                        "api_key": state["api_key"],
                        "url": url,
                    }
                )

                # 통합 분석 결과에 JSON-LD 정보 추가
                enhanced_analysis = {
                    "url": url,
                    "page_type": page_type,
                    "seo_score": seo_analysis.get("seo_score", 0),
                    "geo_score": geo_analysis.get("site_geo_score", 0),
                    "seo_analysis": seo_analysis,
                    "geo_analysis": geo_analysis,
                    "jsonld_schemas": jsonld_result,  # 🆕 JSON-LD 정보 추가
                    "title": seo_analysis.get("title", {}),
                    "meta_description": seo_analysis.get("meta_description", {}),
                    "headings": seo_analysis.get("headings", {}),
                    "images": seo_analysis.get("images", {}),
                    "links": seo_analysis.get("links", {}),
                    "structured_data": seo_analysis.get("structured_data", {}),
                    "content_quality": seo_analysis.get("content_quality", {}),
                }

                page_analyses.append(enhanced_analysis)
                print(
                    f"      ✅ SEO: {seo_analysis.get('seo_score', 0)}/100, JSON-LD: {len(jsonld_result.get('generated_schemas', []))}개 스키마"
                )
            else:
                print(f"      ❌ 분석 실패")

        state["page_analyses"] = page_analyses

        # 사이트 종합 점수 계산
        site_seo_result = calculate_site_average_scores.invoke(
            {"page_analyses": page_analyses}
        )
        state["site_seo_analysis"] = site_seo_result

        # 메시지 히스토리 업데이트에 JSON-LD 정보 추가
        total_schemas = sum(
            len(p.get("jsonld_schemas", {}).get("generated_schemas", []))
            for p in page_analyses
        )

        state["messages"].append(
            AIMessage(
                content=f"""
        📊 개별 페이지 SEO/GEO + JSON-LD 분석이 완료되었습니다:
        
        **분석된 페이지**: {len(page_analyses)}개
        **생성된 JSON-LD 스키마**: {total_schemas}개
        
        **페이지별 JSON-LD 생성 현황**:
        {chr(10).join([f'• [{p["page_type"].upper()}] {len(p.get("jsonld_schemas", {}).get("generated_schemas", []))}개 스키마' for p in page_analyses])}
        
        다음 단계로 최적화를 진행합니다.
        """
            )
        )

        state["current_stage"] = "enhanced_analysis_completed"
        state["next_action"] = "site_geo_analysis"

    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"강화된 페이지 분석 실패: {str(e)}")
        )
        state["next_action"] = "handle_error"
        print(f"❌ 강화된 페이지 분석 실패: {e}")

    return state


def site_geo_analysis_node(
    state: MultiPageSEOWorkflowState,
) -> MultiPageSEOWorkflowState:
    """사이트 전체 GEO 분석 노드"""
    print("🎯 사이트 전체 GEO 분석 중...")

    try:
        crawl_results = state["crawl_results"]

        # 사이트 전체 GEO 점수 계산
        print("   📊 6가지 기준으로 사이트 전체 GEO 점수 계산...")
        geo_result = calculate_site_geo_scores.invoke({"crawl_results": crawl_results})

        if geo_result.get("error"):
            print(f"   ❌ GEO 분석 실패: {geo_result['error']}")
            state["site_geo_analysis"] = {"error": geo_result["error"]}
        else:
            state["site_geo_analysis"] = geo_result

            print(f"   ✅ 사이트 전체 GEO 점수: {geo_result['site_geo_score']:.1f}/100")
            print(f"   📋 세부 점수:")
            site_averages = geo_result["site_averages"]
            for criterion, score in site_averages.items():
                print(f"      • {criterion}: {score:.1f}/100")

        state["current_stage"] = "geo_analysis_completed"
        state["next_action"] = "generate_meta"

        # 메시지 히스토리 업데이트
        if not geo_result.get("error"):
            state["messages"].append(
                AIMessage(
                    content=f"""
            🎯 사이트 전체 GEO 분석이 완료되었습니다:
            
            **전체 사이트 GEO 점수**: {geo_result['site_geo_score']:.1f}/100
            **분석된 페이지**: {geo_result['pages_analyzed']}개
            
            **세부 점수 (사이트 평균)**:
            • 명확성 (Clarity): {site_averages.get('clarity', 0):.1f}/100
            • 구조성 (Structure): {site_averages.get('structure', 0):.1f}/100
            • 맥락성 (Context): {site_averages.get('context', 0):.1f}/100
            • 정합성 (Alignment): {site_averages.get('alignment', 0):.1f}/100
            • 시의성 (Timeliness): {site_averages.get('timeliness', 0):.1f}/100
            • 독창성 (Originality): {site_averages.get('originality', 0):.1f}/100
            
            **사이트 전체 추천사항**:
            {chr(10).join(['• ' + rec for rec in geo_result.get('recommendations', [])])}
            """
                )
            )

        print("✅ 사이트 전체 GEO 분석 완료")

    except Exception as e:
        state["messages"].append(AIMessage(content=f"사이트 GEO 분석 실패: {str(e)}"))
        state["next_action"] = "handle_error"
        print(f"❌ 사이트 GEO 분석 실패: {e}")

    return state


def meta_tags_generation_node(
    state: MultiPageSEOWorkflowState,
) -> MultiPageSEOWorkflowState:
    """메타태그 자동 생성 전용 노드"""
    print("🏷️ 메타태그 자동 생성 중...")

    try:
        crawl_results = state["crawl_results"]
        page_analyses = state["page_analyses"]
        business_type = state["business_type"]
        api_key = state["api_key"]
        meta_results = {}

        for result in crawl_results:
            url = result["url"]
            page_type = result["page_type"]
            html_content = result.get("html_content", "")

            page_analysis = next((p for p in page_analyses if p["url"] == url), {})

            # print(f"   🏷️ [{page_type.upper()}] 메타태그 생성 중...")

            meta_result = generate_meta_tags_with_llm.invoke(
                {
                    "html_content": html_content,
                    "url": url,
                    "page_type": page_type,
                    "seo_analysis": page_analysis.get("seo_analysis", {}),
                    "business_type": business_type,
                    "api_key": api_key,
                }
            )

            meta_results[url] = meta_result
            print(f"      ✅ 메타태그 생성 완료")

        state["meta_results"] = meta_results
        state["current_stage"] = "meta_generated"
        state["next_action"] = "generate_faqs"

        # print(f"✅ 메타태그 생성 완료: {len(meta_results)}개 페이지")

        return state

    except Exception as e:
        print(f"❌ 메타태그 생성 실패: {e}")
        state["next_action"] = "handle_error"
        return state


def faq_generation_node(state: MultiPageSEOWorkflowState) -> MultiPageSEOWorkflowState:
    """지능형 FAQ 생성 전용 노드"""
    print("📋 지능형 FAQ 생성 중...")

    try:
        crawl_results = state["crawl_results"]
        business_type = state["business_type"]
        api_key = state["api_key"]
        faq_results = {}

        for result in crawl_results:
            url = result["url"]
            page_type = result["page_type"]
            html_content = result.get("html_content", "")

            # print(f"   📋 [{page_type.upper()}] FAQ 생성 중...")

            faq_result = generate_intelligent_faq_with_llm.invoke(
                {
                    "website_content": html_content,
                    "business_type": business_type,
                    "api_key": api_key,
                    "keywords": [],
                }
            )

            faq_results[url] = faq_result
            # print(f"      ✅ {len(faq_result.get('generated_faqs', []))}개 FAQ 생성")

        state["faq_results"] = faq_results
        state["current_stage"] = "faq_generated"
        state["next_action"] = "final_optimization"

        total_faqs = sum(len(r.get("generated_faqs", [])) for r in faq_results.values())
        print(f"✅ FAQ 생성 완료")
        # print(f"✅ FAQ 생성 완료: 총 {total_faqs}개 FAQ")

        return state

    except Exception as e:
        print(f"❌ FAQ 생성 실패: {e}")
        state["next_action"] = "handle_error"
        return state


def final_optimization_node(
    state: MultiPageSEOWorkflowState,
) -> MultiPageSEOWorkflowState:
    """최종 HTML 생성 노드 - 모든 요소 통합"""
    print("📄 최종 HTML 파일 생성 중...")

    try:
        crawl_results = state["crawl_results"]
        meta_results = state.get("meta_results", {})
        faq_results = state.get("faq_results", {})

        final_html_files = []

        for result in crawl_results:
            url = result["url"]
            page_type = result["page_type"]
            original_html = result.get("html_content", "")

            # print(f"   📄 [{page_type.upper()}] 최종 HTML 생성 중...")

            # 각 요소 데이터 수집
            meta_data = meta_results.get(url, {})
            faq_data = faq_results.get(url, {})

            # JSON-LD 데이터는 page_analyses에서 가져오기
            page_analysis = next(
                (p for p in state.get("page_analyses", []) if p["url"] == url), {}
            )
            jsonld_data = page_analysis.get("jsonld_schemas", {})

            try:
                # HTML 통합 생성
                final_html, h1_optimization = integrate_all_elements_to_html(
                    original_html, meta_data, jsonld_data, faq_data, url, page_type
                )

                # 파일 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"final_complete_{page_type}_{timestamp}.html"
                filepath = f"outputs/{filename}"

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(final_html)

                final_html_files.append(
                    {
                        "url": url,
                        "page_type": page_type,
                        "filename": filepath,  # outputs/ 경로 포함
                        "has_meta": bool(meta_data.get("success")),
                        "has_jsonld": bool(jsonld_data.get("success")),
                        "has_faq": bool(faq_data.get("success")),
                        "h1_optimization": h1_optimization,
                    }
                )

                print(f"      ✅ 저장 완료: {filename}")

            except Exception as file_error:
                print(f"      ❌ {page_type} 파일 생성 실패: {file_error}")
                continue

        state["final_html_files"] = final_html_files
        state["output_files"] = state.get("output_files", [])
        state["output_files"].extend([f["filename"] for f in final_html_files])
        state["current_stage"] = "html_generated"
        state["next_action"] = "generate_summary"

        print(f"✅ 최종 HTML 생성 완료")
        # print(f"✅ 최종 HTML 생성 완료: {len(final_html_files)}개 파일")

        return state

    except Exception as e:
        import traceback

        print(f"❌ 최종 HTML 생성 실패: {e}")
        print(f"📍 에러 발생 위치:")
        print(traceback.format_exc())

        state["final_html_files"] = []
        state["next_action"] = "handle_error"
        return state


def integrate_all_elements_to_html(
    original_html: str,
    meta_data: dict,
    jsonld_data: dict,
    faq_data: dict,
    url: str,
    page_type: str,
) -> tuple:
    """간단한 HTML 통합"""
    # print(f"🔧 HTML 통합 시작: {page_type} 페이지")
    print(f"🔧 HTML 통합 시작")

    try:
        soup = BeautifulSoup(original_html, "html.parser")

        # 1. 메타태그 적용
        if meta_data.get("success"):
            title_tag = soup.find("title")
            if title_tag:
                title_tag.string = meta_data.get("title", "")
            else:
                new_title = soup.new_tag("title")
                new_title.string = meta_data.get("title", "")
                if soup.head:
                    soup.head.append(new_title)

        # 2. JSON-LD 스키마 적용
        if jsonld_data.get("success"):
            html_schemas = jsonld_data.get("html_schemas", [])
            for schema_html in html_schemas[:2]:  # 최대 2개만
                if schema_html and soup.head:
                    schema_soup = BeautifulSoup(schema_html, "html.parser")
                    script_tag = schema_soup.find("script")
                    if script_tag:
                        soup.head.append(script_tag)

        # 3. H1 태그 최적화
        h1_optimization = optimize_h1_tags(soup, page_type)

        # 4. FAQ 추가 (FAQ 페이지에만)
        if page_type == "faq" and faq_data.get("success"):
            faqs = faq_data.get("generated_faqs", [])
            if faqs and soup.body:
                faq_section = soup.new_tag("section", id="auto-generated-faq")
                faq_h2 = soup.new_tag("h2")
                faq_h2.string = "자주 묻는 질문"
                faq_section.append(faq_h2)

                for faq in faqs[:5]:  # 최대 5개만
                    faq_div = soup.new_tag("div", class_="faq-item")

                    q_h3 = soup.new_tag("h3")
                    q_h3.string = faq.get("question", "")
                    faq_div.append(q_h3)

                    a_p = soup.new_tag("p")
                    a_p.string = faq.get("answer", "")
                    faq_div.append(a_p)

                    faq_section.append(faq_div)

                soup.body.append(faq_section)

        return str(soup), h1_optimization

    except Exception as e:
        print(f"   ❌ HTML 통합 실패: {e}")
        return original_html, {"action_taken": "failed", "error": str(e)}


def optimize_h1_tags(soup, page_type: str) -> dict:
    """H1 태그 최적화"""
    h1_tags = soup.find_all("h1")
    h1_count = len(h1_tags)

    result = {
        "original_h1_count": h1_count,
        "action_taken": "none",
        "final_h1_count": h1_count,
    }

    if h1_count == 0:
        # H1 태그가 없으면 숨겨진 H1 생성
        hidden_h1 = soup.new_tag("h1")
        hidden_h1["style"] = (
            "position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;"
        )

        # 페이지 타입에 따른 적절한 제목 생성
        if page_type == "main":
            hidden_h1.string = "메인 페이지"
        elif page_type == "about":
            hidden_h1.string = "회사소개"
        elif page_type == "service":
            hidden_h1.string = "서비스 소개"
        elif page_type == "contact":
            hidden_h1.string = "연락처"
        elif page_type == "product":
            hidden_h1.string = "상품 정보"
        elif page_type == "faq":
            hidden_h1.string = "자주 묻는 질문"
        else:
            hidden_h1.string = f"{page_type.title()} 페이지"

        if soup.body:
            soup.body.insert(0, hidden_h1)

        result.update(
            {
                "action_taken": "created_hidden_h1",
                "final_h1_count": 1,
                "h1_content": hidden_h1.string,
            }
        )

    elif h1_count > 1:
        # 여러 개의 H1이 있으면 첫 번째만 남기고 나머지는 H2로 변경
        first_h1 = h1_tags[0]

        for i, h1 in enumerate(h1_tags[1:], 1):
            new_h2 = soup.new_tag("h2")

            # 모든 속성 복사
            for attr, value in h1.attrs.items():
                new_h2[attr] = value

            # 내용 복사
            new_h2.clear()
            for content in h1.contents:
                new_h2.append(content)

            h1.replace_with(new_h2)

        result.update(
            {
                "action_taken": "converted_multiple_h1_to_h2",
                "final_h1_count": 1,
                "h1_content": first_h1.get_text(),
                "original_h1_converted": h1_count - 1,
            }
        )

    else:
        # H1이 정확히 1개면 그대로 유지
        result.update(
            {
                "action_taken": "maintained_single_h1",
                "final_h1_count": 1,
                "h1_content": h1_tags[0].get_text(),
            }
        )

    return result


def multi_page_summary_node(
    state: MultiPageSEOWorkflowState,
) -> MultiPageSEOWorkflowState:
    """다중 페이지 종합 요약 노드"""
    print("📋 사이트 전체 최종 요약 생성 중...")

    try:
        if not state.get("api_key"):
            # API 키가 없으면 기본 요약만 생성
            basic_summary = generate_basic_summary(state)
            state["final_summary"] = basic_summary
            state["current_stage"] = "completed"
            state["next_action"] = "end"
            return state

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=state["api_key"])

        # 종합 분석 메타데이터 생성
        summary_metadata = generate_multi_page_summary_metadata(state)

        # 콘솔 출력
        print_multi_page_analysis_summary(state, summary_metadata)

        summary_prompt = generate_multi_page_summary_prompt(state, summary_metadata)

        summary_messages = state["messages"] + [HumanMessage(content=summary_prompt)]
        summary_response = llm.invoke(summary_messages)

        # 최종 요약 데이터 구성
        final_summary = create_multi_page_final_summary(
            state, summary_metadata, summary_response.content
        )
        state["final_summary"] = final_summary

        # 종합 리포트 파일 생성
        report_files = generate_multi_page_report_files(
            state, summary_metadata, summary_response.content
        )
        state["output_files"].extend(report_files)

        # 메시지 히스토리 업데이트
        state["messages"].append(summary_response)

        state["current_stage"] = "completed"
        state["next_action"] = "end"

        # 최종 완료 요약 출력
        print_multi_page_final_summary(state, summary_metadata)

    except Exception as e:
        state["messages"].append(AIMessage(content=f"종합 요약 생성 실패: {str(e)}"))
        # API 키 오류시 기본 요약 생성
        basic_summary = generate_basic_summary(state)
        state["final_summary"] = basic_summary
        state["next_action"] = "end"
        print(f"❌ 종합 요약 생성 실패, 기본 요약 사용: {e}")

    return state


def generate_basic_summary(state: MultiPageSEOWorkflowState) -> dict:
    """API 키 없을 때 기본 요약 생성"""
    crawl_results = state.get("crawl_results", [])
    page_analyses = state.get("page_analyses", [])
    site_seo = state.get("site_seo_analysis", {})
    site_geo = state.get("site_geo_analysis", {})

    return {
        "success": True,
        "workflow_type": "LangGraph Multi-Page SEO/GEO Optimization",
        "website": state["user_url"],
        "business_type": state["business_type"],
        "processing_mode": state["user_mode"],
        "crawling_results": {
            "pages_crawled": len(crawl_results),
            "pages_analyzed": len(page_analyses),
        },
        "scores": {
            "site_seo": site_seo.get("site_average_seo_score", 0),
            "site_geo": (
                site_geo.get("site_geo_score", 0) if not site_geo.get("error") else 0
            ),
        },
        "output_files": state.get("output_files", []),
        "completion_time": datetime.now().isoformat(),
        "note": "API 키 없이 기본 분석 완료",
    }


def error_handler_node(state: MultiPageSEOWorkflowState) -> MultiPageSEOWorkflowState:
    """에러 처리 노드"""
    print("❌ 에러 처리 중...")

    # 에러 로그 생성
    error_messages = [msg for msg in state["messages"] if "실패" in str(msg.content)]

    error_summary = {
        "success": False,
        "errors": [str(msg.content) for msg in error_messages],
        "current_stage": state.get("current_stage", "unknown"),
        "url": state.get("user_url", ""),
        "max_pages": state.get("max_pages", 0),
        "pages_crawled": len(state.get("crawl_results", [])),
        "pages_analyzed": len(state.get("page_analyses", [])),
        "timestamp": datetime.now().isoformat(),
    }

    state["final_summary"] = error_summary
    state["current_stage"] = "error"
    state["next_action"] = "end"

    # 에러 로그 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = f"outputs/db_seo_error_{timestamp}.json"

    with open(error_file, "w", encoding="utf-8") as f:
        json.dump(error_summary, f, ensure_ascii=False, indent=2)

    state["output_files"] = [error_file]

    print(f"📝 에러 로그 저장: {error_file}")
    for error in error_summary["errors"]:
        print(f"   • {error}")

    return state


# ===== 다중 페이지 요약 및 리포트 생성 함수들 =====
def generate_multi_page_summary_metadata(state: MultiPageSEOWorkflowState) -> dict:
    """다중 페이지 분석 메타데이터 생성"""

    crawl_results = state.get("crawl_results", [])
    page_analyses = state.get("page_analyses", [])
    site_seo = state.get("site_seo_analysis", {})
    site_geo = state.get("site_geo_analysis", {})
    final_html_files = state.get("final_html_files", [])
    h1_analysis = analyze_h1_optimizations(final_html_files)

    metadata = {
        "crawl_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workflow_type": "LangGraph 다중페이지 SEO/GEO 최적화",
        "base_url": state.get("user_url", ""),
        "max_pages_requested": state.get("max_pages", 0),
        "pages_crawled": len(crawl_results),
        "pages_analyzed": len(page_analyses),
        "pages_optimized": len(final_html_files),
        "business_type": state.get("business_type", "Unknown"),
        "processing_mode": state.get("user_mode", "unknown"),
        "h1_optimization_results": h1_analysis,
        # 점수 및 등급
        "site_seo_score": site_seo.get("site_average_seo_score", 0),
        "site_geo_score": (
            site_geo.get("site_geo_score", 0) if not site_geo.get("error") else 0
        ),
        "overall_grade": "C+",
        # 페이지 타입별 분포
        "page_type_distribution": {},
        "page_type_averages": site_seo.get("page_type_averages", {}),
        # GEO 세부 점수
        "geo_details": (
            site_geo.get("site_averages", {}) if not site_geo.get("error") else {}
        ),
        # 문제점 및 개선사항
        "common_issues": site_seo.get("common_issues", {}),
        "site_geo_recommendations": (
            site_geo.get("recommendations", []) if not site_geo.get("error") else []
        ),
        "priority_improvements": site_seo.get("priority_improvements", []),
        # 파일 생성
        "files_generated": len(state.get("output_files", [])),
        # ROI 및 예상 효과
        "investment_required": "개발자 40-80시간 (약 200-400만원)",
        "expected_roi": "4-8개월 내 400-800% ROI",
        "timeline_to_results": "최적화 후 2-6개월",
    }

    # 페이지 타입별 분포 계산
    page_types = {}
    for result in crawl_results:
        page_type = result.get("page_type", "other")
        page_types[page_type] = page_types.get(page_type, 0) + 1
    metadata["page_type_distribution"] = page_types

    # 전체 점수 기반 등급 계산
    avg_score = (metadata["site_seo_score"] + metadata["site_geo_score"]) / 2
    if avg_score >= 90:
        metadata["overall_grade"] = "A+"
    elif avg_score >= 80:
        metadata["overall_grade"] = "A"
    elif avg_score >= 70:
        metadata["overall_grade"] = "B+"
    elif avg_score >= 60:
        metadata["overall_grade"] = "B"
    else:
        metadata["overall_grade"] = "C+"

    return metadata


def analyze_h1_optimizations(final_html_files: list) -> dict:
    """H1 태그 최적화 결과 분석"""
    total_pages = len(final_html_files)

    if total_pages == 0:
        return {}

    original_no_h1 = 0
    original_multiple_h1 = 0
    original_single_h1 = 0
    actions_taken = []

    for file_info in final_html_files:
        h1_opt = file_info.get("h1_optimization", {})
        original_count = h1_opt.get("original_h1_count", 0)
        action = h1_opt.get("action_taken", "none")

        if original_count == 0:
            original_no_h1 += 1
        elif original_count == 1:
            original_single_h1 += 1
        else:
            original_multiple_h1 += 1

        actions_taken.append(
            {
                "page_type": file_info.get("page_type", "unknown"),
                "original_h1_count": original_count,
                "action": action,
                "final_h1_content": h1_opt.get("h1_content", ""),
            }
        )

    return {
        "total_pages_analyzed": total_pages,
        "original_no_h1_pages": original_no_h1,
        "original_single_h1_pages": original_single_h1,
        "original_multiple_h1_pages": original_multiple_h1,
        "pages_needed_h1_creation": original_no_h1,
        "pages_needed_h1_consolidation": original_multiple_h1,
        "h1_optimization_actions": actions_taken,
        "h1_compliance_rate": (
            round((original_single_h1 / total_pages) * 100, 1) if total_pages > 0 else 0
        ),
    }


def print_multi_page_analysis_summary(state: MultiPageSEOWorkflowState, metadata: dict):
    """다중 페이지 분석 결과 콘솔 출력"""

    print(f"\n{'='*70}")
    # print("🚀 다중 페이지 SEO/GEO 분석 완료")
    print("🚀 SEO/GEO 분석 완료")
    print(f"{'='*70}")

    # 크롤링 정보
    print(f"🕷️ 크롤링 정보:")
    print(f"   - 기본 URL: {metadata['base_url']}")
    # print(f"   - 요청 페이지: 최대 {metadata['max_pages_requested']}개")
    # print(f"   - 크롤링된 페이지: {metadata['pages_crawled']}개")
    # print(f"   - 분석된 페이지: {metadata['pages_analyzed']}개")
    # print(f"   - 최적화된 페이지: {metadata['pages_optimized']}개")
    print(f"   - 분석 시간: {metadata['crawl_timestamp']}")

    # H1 태그 분석 결과 출력 추가
    h1_analysis = metadata.get("h1_optimization_results", {})
    if h1_analysis:
        print(f"\n🏷️ H1 태그 최적화 결과:")
        print(f"   - 분석된 페이지: {h1_analysis.get('total_pages_analyzed', 0)}개")
        print(
            f"   - 원래 H1 없던 페이지: {h1_analysis.get('original_no_h1_pages', 0)}개 → 숨겨진 H1 생성"
        )
        print(
            f"   - 원래 H1 여러개 페이지: {h1_analysis.get('original_multiple_h1_pages', 0)}개 → H2로 변환"
        )
        print(
            f"   - 원래 H1 적절한 페이지: {h1_analysis.get('original_single_h1_pages', 0)}개 → 유지"
        )
        print(
            f"   - 최종 H1 준수율: {h1_analysis.get('h1_compliance_rate', 0)}% → 100%"
        )

    # 페이지 타입별 분포
    print(f"\n📊 페이지 타입별 분포:")
    for page_type, count in metadata["page_type_distribution"].items():
        avg_score = metadata["page_type_averages"].get(page_type, 0)
        print(f"   • {page_type.upper()}: {count}개 (평균 {avg_score}/100)")

    # 종합 평가
    print(f"\n📋 사이트 종합 평가:")
    print(f"   전체 등급: {metadata['overall_grade']}")
    print(f"   사이트 SEO 점수: {metadata['site_seo_score']:.1f}/100")
    print(f"   사이트 GEO 점수: {metadata['site_geo_score']:.1f}/100")

    # GEO 세부 점수
    if metadata["geo_details"]:
        print(f"\n🎯 GEO 세부 점수 (사이트 평균):")
        for criterion, score in metadata["geo_details"].items():
            print(f"   • {criterion}: {score:.1f}/100")

    # 주요 문제점
    if metadata["common_issues"]:
        print(f"\n⚠️ 사이트 공통 문제점:")
        for issue_type, percentage in metadata["common_issues"].items():
            if percentage >= 50:
                issue_name = {
                    "title_issues": "Title 태그 문제",
                    "description_issues": "Meta Description 문제",
                    "h1_issues": "H1 태그 문제",
                    "alt_issues": "ALT 속성 문제",
                    "schema_issues": "구조화된 데이터 누락",
                    "content_issues": "콘텐츠 품질 문제",
                }.get(issue_type, issue_type)
                print(f"   • {issue_name}: {percentage}% 페이지 영향")

    # 우선순위 개선사항
    if metadata["priority_improvements"]:
        print(f"\n🚨 우선순위 개선사항:")
        for i, improvement in enumerate(metadata["priority_improvements"][:5], 1):
            print(f"   {i}. {improvement.get('issue', '')}")
            print(f"      → 영향 범위: {improvement.get('affected_pages', '')} 페이지")
            print(f"      → 예상 효과: {improvement.get('impact', '')}")

    # ROI 예측
    print(f"\n💰 ROI 예측 (사이트 전체):")
    print(f"   - 필요 투자: {metadata['investment_required']}")
    print(f"   - 예상 수익률: {metadata['expected_roi']}")
    print(f"   - 결과까지 기간: {metadata['timeline_to_results']}")


def generate_multi_page_summary_prompt(
    state: MultiPageSEOWorkflowState, metadata: dict
) -> str:
    """다중 페이지 종합 요약 프롬프트 생성"""

    h1_info = ""
    h1_analysis = metadata.get("h1_optimization_results", {})
    if h1_analysis:
        h1_info = f"""
        **H1 태그 최적화 결과:**
        - H1 없던 페이지: {h1_analysis.get('original_no_h1_pages', 0)}개 (숨겨진 H1 자동 생성)
        - H1 여러개 페이지: {h1_analysis.get('original_multiple_h1_pages', 0)}개 (H2로 변환)
        - H1 준수율: {h1_analysis.get('h1_compliance_rate', 0)}% → 100% 달성
        """

    geo_detailed_prompt = (
        f"""
    **GEO 세부 분석 (AI 검색엔진 최적화):**
    
    **현재 GEO 점수 분석:**
    - Clarity (명확성): {metadata['geo_details'].get('clarity', 0):.1f}/100
    - Structure (구조성): {metadata['geo_details'].get('structure', 0):.1f}/100  
    - Context (맥락성): {metadata['geo_details'].get('context', 0):.1f}/100
    - Alignment (정합성): {metadata['geo_details'].get('alignment', 0):.1f}/100
    - Timeliness (시의성): {metadata['geo_details'].get('timeliness', 0):.1f}/100
    - Originality (독창성): {metadata['geo_details'].get('originality', 0):.1f}/100
    """
        if metadata["geo_details"]
        else ""
    )

    prompt = f"""
    다중 페이지 LangGraph SEO/GEO 최적화 작업이 완료되었습니다.
    사이트 전체를 크롤링하고 분석한 종합 리포트를 작성해주세요.
    
    **사이트 정보:**
    - 기본 URL: {state['user_url']}
    - 비즈니스 타입: {state['business_type']}
    - 처리 모드: {state['user_mode']}
    
    **크롤링 결과:**
    - 요청 페이지: 최대 {metadata['max_pages_requested']}개
    - 크롤링된 페이지: {metadata['pages_crawled']}개
    - 분석된 페이지: {metadata['pages_analyzed']}개
    - 페이지 타입 분포: {metadata['page_type_distribution']}
    
    **종합 분석 결과:**
    - 전체 등급: {metadata['overall_grade']}
    - 사이트 SEO 점수: {metadata['site_seo_score']}/100
    - 사이트 GEO 점수: {metadata['site_geo_score']}/100
    
    {h1_info}

    **페이지 타입별 평균 점수:**
    {chr(10).join([f'- {k.upper()}: {v}/100' for k, v in metadata['page_type_averages'].items()])}
    
    {geo_detailed_prompt}
    
    **사이트 공통 문제점:**
    {chr(10).join([f'- {k}: {v}% 페이지 영향' for k, v in metadata['common_issues'].items() if v >= 50])}
    
    **ROI 정보:**
    - 필요 투자: {metadata['investment_required']}
    - 예상 수익률: {metadata['expected_roi']}
    - 결과까지 기간: {metadata['timeline_to_results']}
    
    다음 구조로 상세하고 실용적인 다중 페이지 리포트를 마크다운 형식으로 작성해주세요:
    
    # 🚀 다중 페이지 SEO/GEO 최적화 완료 리포트
    
    ## 📊 실행 요약 (Executive Summary)
    - 핵심 메시지 및 전체 성과
    - 사이트 전체 점수 및 등급
    - 크롤링 및 최적화 규모
    
    ## 🕷️ 크롤링 결과 분석
    ### 📄 페이지 수집 현황
    ### 🎯 페이지 타입별 분포 및 점수
    ### 📊 사이트 구조 분석
    
    ## 🔍 사이트 전체 SEO/GEO 분석
    ### 📈 종합 점수 현황
    ### 🎯 GEO 6가지 기준 사이트 평균 (AI 검색엔진 최적화)
    
    ## 🛠️ 적용된 다중 페이지 최적화
    ### ✅ 페이지별 최적화 결과
    ### 📁 생성된 파일들
    ### 🔧 사이트 전체 개선사항
    
    ## 📈 예상 효과 및 ROI (사이트 전체)
    ### 단기 효과 (1-8주)
    ### 중기 효과 (2-6개월)
    ### 장기 효과 (6개월-1년)
    ### 💰 사이트 전체 투자 대비 수익 전망
    
    ## 🚀 다음 단계 권장사항
    ### 즉시 실행 항목 (우선순위별)
    ### 중기 사이트 개선 계획
    ### 장기 SEO/GEO 전략
    
    ## 📊 모니터링 및 지속 관리 방안
    ### 추적해야 할 지표 (페이지별/사이트 전체)
    ### 권장 도구 및 주기
    ### 콘텐츠 업데이트 전략

    다중 페이지 크롤링과 사이트 전체 최적화의 가치를 강조하고,
    기존 단일 페이지 분석 대비 장점을 명확히 보여주세요.
    """

    return prompt


def create_multi_page_final_summary(
    state: MultiPageSEOWorkflowState, metadata: dict, report_content: str
) -> dict:
    """다중 페이지 최종 요약 데이터 생성"""

    return {
        "success": True,
        "workflow_type": "LangGraph Multi-Page SEO/GEO Optimization",
        "website": state["user_url"],
        "business_type": state["business_type"],
        "processing_mode": state["user_mode"],
        # 크롤링 결과
        "crawling_results": {
            "max_pages_requested": metadata["max_pages_requested"],
            "pages_crawled": metadata["pages_crawled"],
            "pages_analyzed": metadata["pages_analyzed"],
            "pages_optimized": metadata["pages_optimized"],
            "page_type_distribution": metadata["page_type_distribution"],
        },
        # 점수 및 등급
        "scores": {
            "overall_grade": metadata["overall_grade"],
            "site_seo": metadata["site_seo_score"],
            "site_geo": metadata["site_geo_score"],
            "page_type_averages": metadata["page_type_averages"],
        },
        # GEO 세부 점수
        "geo_details": metadata["geo_details"],
        # 분석 결과
        "analysis_results": {
            "common_issues": metadata["common_issues"],
            "priority_improvements": metadata["priority_improvements"],
            "site_geo_recommendations": metadata["site_geo_recommendations"],
        },
        # ROI 정보
        "roi_projection": {
            "investment_required": metadata["investment_required"],
            "expected_roi": metadata["expected_roi"],
            "timeline_to_results": metadata["timeline_to_results"],
        },
        # 파일 및 출력
        "output_files": state.get("output_files", []),
        "files_generated": metadata["files_generated"],
        # 리포트 내용
        "detailed_report": report_content,
        "completion_time": datetime.now().isoformat(),
        # 다음 단계
        "next_steps": {
            "immediate": [
                imp.get("issue", "") for imp in metadata["priority_improvements"][:3]
            ],
            "monitoring_required": True,
            "follow_up_recommended": "4-8주 후 재분석 (사이트 전체)",
        },
    }


def generate_multi_page_report_files(
    state: MultiPageSEOWorkflowState, metadata: dict, report_content: str
) -> list:
    """다중 페이지 리포트 파일들 생성"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_files = []

    # 1. 메인 리포트 (마크다운)
    main_report_file = f"outputs/db_seo_geo_report_{timestamp}.md"

    with open(main_report_file, "w", encoding="utf-8") as f:
        f.write(f"# 다중 페이지 SEO/GEO 최적화 완료 리포트\n\n")
        f.write(f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**워크플로우**: {metadata['workflow_type']}\n")
        f.write(f"**대상 웹사이트**: {state['user_url']}\n")
        f.write(f"**크롤링 규모**: {metadata['pages_crawled']}개 페이지\n")
        f.write(f"**비즈니스 타입**: {state['business_type']}\n\n")
        f.write("---\n\n")
        f.write(report_content)

        # 추가 다중 페이지 메타데이터
        f.write(f"\n\n## 🔧 다중 페이지 분석 메타데이터\n\n")
        f.write(f"### 크롤링 정보\n")
        f.write(f"- **요청 페이지 수**: {metadata['max_pages_requested']}개\n")
        f.write(f"- **실제 크롤링된 페이지**: {metadata['pages_crawled']}개\n")
        f.write(f"- **성공적으로 분석된 페이지**: {metadata['pages_analyzed']}개\n")
        f.write(f"- **최적화 대상 페이지**: {metadata['pages_optimized']}개\n\n")

        f.write(f"### 페이지 타입별 상세 정보\n")
        for page_type, count in metadata["page_type_distribution"].items():
            avg_score = metadata["page_type_averages"].get(page_type, 0)
            f.write(
                f"- **{page_type.upper()}**: {count}개 페이지, 평균 SEO 점수 {avg_score}/100\n"
            )

        if metadata["geo_details"]:
            f.write(f"\n### 사이트 전체 GEO 점수 상세\n")
            for criterion, score in metadata["geo_details"].items():
                f.write(f"- **{criterion}**: {score:.1f}/100\n")

    generated_files.append(main_report_file)

    # 2. 페이지별 상세 데이터 (JSON)
    detailed_data_file = f"outputs/db_detailed_data_{timestamp}.json"

    detailed_data = {
        "metadata": metadata,
        "crawling_results": state.get("crawl_results", []),
        "page_analyses": state.get("page_analyses", []),
        "site_analysis": {
            "seo": state.get("site_seo_analysis", {}),
            "geo": state.get("site_geo_analysis", {}),
        },
        "generation_timestamp": datetime.now().isoformat(),
    }

    with open(detailed_data_file, "w", encoding="utf-8") as f:
        json.dump(detailed_data, f, ensure_ascii=False, indent=2)

    generated_files.append(detailed_data_file)

    return generated_files


def print_multi_page_final_summary(state: MultiPageSEOWorkflowState, metadata: dict):
    """다중 페이지 최종 완료 요약 출력"""

    print(f"\n{'='*70}")
    print("🎉 SEO/GEO 최적화 완료!")
    # print("🎉 다중 페이지 SEO/GEO 최적화 완료!")
    print(f"{'='*70}")

    # 전체 규모
    # print(f"📊 처리 규모:")
    # print(f"   • 크롤링된 페이지: {metadata['pages_crawled']}개")
    # print(f"   • 분석된 페이지: {metadata['pages_analyzed']}개")
    # print(f"   • 최적화된 페이지: {metadata['pages_optimized']}개")
    # print(f"   • 생성된 파일: {metadata['files_generated']}개")

    # 최종 점수
    print(f"\n📊 사이트 전체 최종 점수:")
    print(f"   전체 등급: {metadata['overall_grade']}")
    print(f"   사이트 SEO: {metadata['site_seo_score']:.1f}/100")
    print(f"   사이트 GEO: {metadata['site_geo_score']:.1f}/100")

    # 페이지 타입별 성과
    print(f"\n📄 페이지 타입별 성과:")
    for page_type, avg_score in metadata["page_type_averages"].items():
        count = metadata["page_type_distribution"].get(page_type, 0)
        print(f"평균 {avg_score}/100")
        # print(f"   • {page_type.upper()}: {count}개 페이지, 평균 {avg_score}/100")

    # 생성된 파일들
    print(f"\n📁 생성된 파일들:")
    for file in state["output_files"]:
        print(f"   • {file}")

    # ROI 요약
    print(f"\n💰 사이트 전체 ROI 요약:")
    print(f"   필요 투자: {metadata['investment_required']}")
    print(f"   예상 수익률: {metadata['expected_roi']}")
    print(f"   효과 발현 기간: {metadata['timeline_to_results']}")

    print(f"\n✨ LangGraph SEO/GEO 최적화가 성공적으로 완료되었습니다!")
    print(f"🌐 사이트 전체가 검색엔진과 AI 검색엔진에 최적화되었습니다!")


# ===== 조건부 라우팅 함수 =====
def route_next_action(state: MultiPageSEOWorkflowState) -> str:
    """다음 액션으로 라우팅"""
    return state.get("next_action", "end")


# ===== 워크플로우 생성 =====
def create_optimized_seo_langgraph() -> StateGraph:
    """3단계 분리형 최적화 워크플로우"""

    workflow = StateGraph(MultiPageSEOWorkflowState)

    # 노드 추가
    workflow.add_node("db_input", db_input_node)
    workflow.add_node("crawling", crawling_node)
    workflow.add_node("page_analysis", enhanced_page_analysis_node)
    workflow.add_node("site_geo_analysis", site_geo_analysis_node)
    workflow.add_node("meta_tags_generation", meta_tags_generation_node)
    workflow.add_node("faq_generation", faq_generation_node)
    workflow.add_node("final_optimization", final_optimization_node)
    workflow.add_node("multi_page_summary", multi_page_summary_node)
    workflow.add_node("error_handler", error_handler_node)

    # 엣지 연결
    workflow.add_conditional_edges(
        "db_input",
        route_next_action,
        {"start_crawling": "crawling", "handle_error": "error_handler", "end": END},
    )

    workflow.add_conditional_edges(
        "crawling",
        route_next_action,
        {
            "start_page_analysis": "page_analysis",
            "handle_error": "error_handler",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "page_analysis",
        route_next_action,
        {
            "site_geo_analysis": "site_geo_analysis",
            "generate_summary": "multi_page_summary",
            "handle_error": "error_handler",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "site_geo_analysis",
        route_next_action,
        {
            "generate_meta": "meta_tags_generation",
            "generate_summary": "multi_page_summary",
            "handle_error": "error_handler",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "meta_tags_generation",
        route_next_action,
        {
            "generate_faqs": "faq_generation",
            "handle_error": "error_handler",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "faq_generation",
        route_next_action,
        {
            "final_optimization": "final_optimization",
            "handle_error": "error_handler",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "final_optimization",
        route_next_action,
        {
            "generate_summary": "multi_page_summary",
            "handle_error": "error_handler",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "multi_page_summary",
        route_next_action,
        {"end": END, "handle_error": "error_handler"},
    )

    workflow.add_edge("error_handler", END)
    workflow.set_entry_point("db_input")

    return workflow


# ===== 메인 실행 클래스 =====
class CompleteMultiPageSEOOptimizer:
    """완전 통합 다중 페이지 SEO/GEO 최적화기"""

    def __init__(self):
        self.workflow = create_optimized_seo_langgraph()
        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)

    async def optimize_full_website(
        self,
        url: str = None,
        api_key: str = None,
        mode: str = "full",
        max_pages: int = 9,
    ) -> Dict:
        """다중 페이지 웹사이트 최적화 실행"""

        initial_state = {
            "user_url": url or "",
            "api_key": api_key or "",
            "user_mode": mode,
            "max_pages": max_pages,
            "messages": [],
            "current_stage": "starting",
            "next_action": "start_crawling",
            "crawl_results": [],
            "crawled_files": [],
            "page_analyses": [],
            "site_seo_analysis": {},
            "site_geo_analysis": {},
            "site_performance": {},
            "site_structured_data": {},
            "site_keywords": {},
            "optimized_pages": [],
            "optimization_summary": {},
            "meta_results": {},
            "jsonld_results": {},
            "faq_results": {},
            "final_optimization": [],
            "final_html_files": [],
            "business_type": "",
            "target_keywords": "",
            "output_files": [],
            "final_summary": {},
        }

        config = {"configurable": {"thread_id": "multipage_seo_geo_session"}}

        try:
            final_state = await self.app.ainvoke(initial_state, config)
            return final_state["final_summary"]
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# ===== 사용하기 쉬운 함수들 =====
async def quick_multi_page_optimize(
    url: str, api_key: str = None, mode: str = "full", max_pages: int = 9
) -> Dict:
    """빠른 다중 페이지 최적화"""
    optimizer = CompleteMultiPageSEOOptimizer()
    return await optimizer.optimize_full_website(url, api_key, mode, max_pages)


def interactive_multi_page_optimize():
    """대화형 다중 페이지 최적화"""
    optimizer = CompleteMultiPageSEOOptimizer()

    print("🚀 웹페이지 LangGraph SEO/GEO 최적화 시스템")
    # print("🚀 완전 통합 다중 페이지 LangGraph SEO/GEO 최적화 시스템")
    # print("=" * 70)
    # print("🕷️ sitemap.xml 기반 우선순위 페이지 크롤링")
    print("🔥 사이트 전체 분석 + 자동 최적화 + 종합 리포트")
    print("📊 페이지별 분석 및 사이트 전체 평균 점수 제공")
    print()

    # 스트리밍으로 진행상황 표시
    for chunk in optimizer.app.stream(
        {
            "user_url": "",
            "api_key": "",
            "user_mode": "full",
            "max_pages": 9,
            "messages": [],
            "current_stage": "starting",
            "next_action": "start_crawling",
            "crawl_results": [],
            "crawled_files": [],
            "page_analyses": [],
            "site_seo_analysis": {},
            "site_geo_analysis": {},
            "site_performance": {},
            "site_structured_data": {},
            "site_keywords": {},
            "optimized_pages": [],
            "optimization_summary": {},
            "meta_results": {},
            "jsonld_results": {},
            "faq_results": {},
            "final_optimization": [],
            "final_html_files": [],
            "business_type": "",
            "target_keywords": "",
            "output_files": [],
            "final_summary": {},
        },
        {"configurable": {"thread_id": "interactive_session"}},
    ):
        stage = list(chunk.keys())[0]
        print(f"🔄 현재 단계: {stage}")


# ===== 메인 실행 =====
async def main():
    print("🚀 DB 기반 웹페이지 LangGraph SEO/GEO 최적화 시스템")
    print("=" * 70)
    print("🗄️ 데이터베이스에서 최신 브랜드 URL 자동 가져오기")
    print("📁 결과물은 outputs/ 폴더에 저장됩니다")
    print()

    # .env 파일 체크
    if not os.path.exists(".env"):
        print("⚠️ .env 파일이 없습니다. 환경변수를 설정해주세요.")
        return

    # 바로 실행 (사용자 입력 없음)
    try:
        optimizer = CompleteMultiPageSEOOptimizer()
        result = await optimizer.optimize_full_website()

        if result.get("success"):
            print("\n🎉 DB 기반 웹페이지 SEO/GEO 최적화 완료!")
            # ... 결과 출력 ...
        else:
            print(f"❌ 최적화 실패: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())
