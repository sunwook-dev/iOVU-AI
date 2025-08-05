import time
import random
import os
import json
from playwright.async_api import async_playwright
from datetime import datetime
from typing import List, Optional
import re

# 데이터베이스 import를 위한 프로젝트 루트 경로 추가 (DB 사용 시)
# project_root = os.path.dirname(os.path.dirname(os.path.dirname(
#     os.path.abspath(__file__))))
# sys.path.append(project_root)

# from database.queries import BrandQueries, DataQueries
from .config import Config


class InstagramCrawler:
    def __init__(self, username: str = None, password: str = None):
        """Instagram 크롤러 초기화"""
        self.username = username or Config.INSTAGRAM_USERNAME
        self.password = password or Config.INSTAGRAM_PASSWORD

        # 로그인 정보 검증
        if not self.username or not self.password:
            raise ValueError(
                "Instagram 로그인 정보가 설정되지 않았습니다. 환경 변수를 확인하세요."
            )

        self.data_dir = Config.DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        # self.data_queries = DataQueries()  # DB 사용 시 활성화

    @staticmethod
    def random_sleep(min_sec=5, max_sec=9):
        """탐지 방지를 위한 랜덤 대기"""
        delay = random.uniform(min_sec, max_sec)
        print(f"[*] {delay:.2f}초 대기 중...")
        time.sleep(delay)

    @staticmethod
    def extract_post_id(url: str) -> Optional[str]:
        """URL에서 Instagram 게시물 ID 추출 (일반 게시물 + 릴스)"""
        # 일반 게시물 패턴 /p/
        match = re.search(r"/p/([A-Za-z0-9_-]+)/", url)
        if match:
            return match.group(1)

        # 릴스 패턴 /reel/
        match = re.search(r"/reel/([A-Za-z0-9_-]+)/", url)
        if match:
            return match.group(1)

        return None

    async def get_post_detail(self, page, href):
        """게시물 상세 페이지에서 크롤링하는 함수"""
        posted_at = ""
        content = ""
        imgs = []
        comments = []
        like_count = 0
        comment_count = 0

        if not href:
            return None

        post_id = self.extract_post_id(href)
        if not post_id:
            return None

        new_page = await page.context.new_page()
        try:
            await new_page.goto(href, wait_until="domcontentloaded")
            # 페이지 전체가 로딩될 때까지 대기
            await new_page.wait_for_load_state("networkidle", timeout=30000)

            # 게시물 내용 크롤링 (여러 selector 시도)
            content_selectors = [
                "h1._ap3a._aaco._aacu._aacx._aad7._aade",  # 기본 캡션 선택자
                "h1._aacl._aaco._aacu._aacx._aad7._aade",  # 대체 캡션 선택자
                "div[role='button'] span._aacl._aaco._aacu._aacx._aad7._aade",
                # 버튼 내 텍스트
                "article div[data-testid='post-content'] span",  # 새로운 구조
                "article span[dir='auto']",  # 자동 방향 설정된 텍스트
                "div._a9zs h1",  # 간소화된 선택자
                "span._aacl._aaco._aacu._aacx._aad7._aade",  # 직접 span 선택자
                "div[style*='word-wrap'] span",  # 텍스트 래핑이 적용된 요소
            ]

            for selector in content_selectors:
                content_elem = await new_page.query_selector(selector)
                if content_elem:
                    content = await content_elem.inner_text()
                    if content and content.strip():  # 빈 내용이 아닌 경우만
                        break

            # 만약 위의 선택자로 찾지 못했다면, 더 넓은 범위에서 텍스트 검색
            if not content:
                try:
                    # article 내의 모든 span 요소에서 해시태그나 멘션이 포함된 텍스트 찾기
                    all_spans = await new_page.query_selector_all("article span")
                    for span in all_spans:
                        text = await span.inner_text()
                        if text and ("#" in text or "@" in text) and len(text) > 10:
                            content = text
                            break
                except Exception:
                    pass

            # 이미지/비디오 src 추출
            img_elems = await new_page.query_selector_all("article img[src]")
            vid_elems = await new_page.query_selector_all("article video[src]")
            media_urls = []

            for img in img_elems:
                src = await img.get_attribute("src")
                if src and not src.startswith("data:"):
                    media_urls.append(src)

            for vid in vid_elems:
                src = await vid.get_attribute("src")
                if src:
                    media_urls.append(src)

            imgs = list(set(media_urls))  # 중복 제거

            # 좋아요 수 추출
            like_selectors = [
                "button[type='button'] span.html-span.xdj266r",
                "section span._ac2a",
                "div span._ac2a",
            ]

            for selector in like_selectors:
                like_elem = await new_page.query_selector(selector)
                if like_elem:
                    like_text = await like_elem.inner_text()
                    # 숫자만 추출
                    like_numbers = re.findall(r"[\d,]+", like_text)
                    if like_numbers:
                        like_count = int(like_numbers[0].replace(",", ""))
                        break

            # 댓글 추출 (최대 10개)
            comment_selectors = [
                "div[role='button'] span._aacl._aaco._aacu._aacx._aad7._aade",
                "span._ap3a._aaco._aacu._aacx._aad7._aade",
            ]

            for selector in comment_selectors:
                comment_elems = await new_page.query_selector_all(selector)
                if comment_elems:
                    for i, comment in enumerate(comment_elems[:10]):
                        text = await comment.inner_text()
                        if text and text != content:  # 본문과 중복 제거
                            comments.append(text)
                    break

            comment_count = len(comments)

            # time 태그의 datetime 속성 추출
            time_elem = await new_page.query_selector("time")
            if time_elem:
                datetime_str = await time_elem.get_attribute("datetime")
                if not datetime_str:
                    datetime_str = await time_elem.get_attribute("title")

                if datetime_str:
                    try:
                        # ISO 형식 처리
                        if "T" in datetime_str:
                            posted_at = datetime.fromisoformat(
                                datetime_str.replace("Z", "+00:00")
                            )
                            posted_at = posted_at.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            # 한국어 형식 처리
                            posted_at = datetime.strptime(
                                datetime_str, "%Y년 %m월 %d일"
                            )
                            posted_at = posted_at.strftime("%Y-%m-%d")
                    except Exception:
                        posted_at = datetime_str

        except Exception as e:
            print(f"상세 크롤링 실패 ({href}): {str(e)}")
        finally:
            await new_page.close()

        # 디버깅: 추출된 콘텐츠 확인
        if content:
            print(
                f"[DEBUG] 콘텐츠 추출 성공: {content[:100]}..."
                if len(content) > 100
                else f"[DEBUG] 콘텐츠: {content}"
            )
            hashtags = re.findall(r"#[\w가-힣]+(?:_[\w가-힣]+)*", content)
            mentions = re.findall(r"@[\w.]+(?:_[\w.]+)*", content)
            if hashtags:
                print(f"[DEBUG] 해시태그 발견: {hashtags}")
            if mentions:
                print(f"[DEBUG] 멘션 발견: {mentions}")
        else:
            print(f"[DEBUG] 콘텐츠 추출 실패: {href}")

        # 해시태그와 멘션 추출
        extracted_hashtags = self._extract_hashtags(content)
        extracted_mentions = self._extract_mentions(content)

        return {
            "post_id": post_id,
            "content": content,
            "img": imgs,
            "comments": comments,
            "date": posted_at,
            "like_count": like_count,
            "comment_count": comment_count,
            "hashtags": extracted_hashtags,
            "mentions": extracted_mentions,
        }

    async def login(self, page):
        """Instagram 로그인"""
        try:
            await page.goto("https://www.instagram.com/accounts/login/")
            await page.wait_for_selector("input[name='username']", timeout=10000)
            self.random_sleep(1, 3)

            await page.fill("input[name='username']", self.username)
            await page.fill("input[name='password']", self.password)
            await page.click("button[type='submit']")

            self.random_sleep(8, 10)

            # 로그인 성공 확인
            if await page.query_selector(
                "svg[aria-label='홈']"
            ) or await page.query_selector("svg[aria-label='Home']"):
                print("[*] Instagram 로그인 성공")
            else:
                print("[!] 로그인 확인 실패, 계속 진행...")

        except Exception as e:
            print(f"[!] 로그인 중 오류 발생: {str(e)}")
            raise

    async def crawl_posts(
        self,
        page,
        target_url,
        target_name,
        max_scroll_round=1,
        crawl_batch_size=20,
        file_suffix=None,
    ):
        """Instagram 계정에서 게시물 크롤링"""
        await page.goto(target_url)
        self.random_sleep()
        post_info = []
        crawled_post_ids = set()
        post_number = 1

        # 태그된 게시물 페이지 여부 확인
        is_tagged = "/tagged/" in target_url

        # 페이지당 최대 게시물 수 설정
        max_posts = Config.MAX_POSTS_PER_PAGE

        for r in range(1, max_scroll_round + 1):
            # 태그된 게시물과 일반 게시물 모두 동일한 방식으로 처리
            # Instagram의 게시물은 모두 a 태그로 감싸져 있고, 그 안에 img가 있음

            # 여러 선택자를 시도해서 게시물 링크들을 찾음
            post_selectors = [
                "article a[href*='/p/'], article a[href*='/reel/']",  # 일반 게시물 + 릴스 링크
                "div._aagu",  # 일반 게시물 컨테이너
                "article div[role='button']",  # 대체 선택자
                "a[href*='/p/'] img, a[href*='/reel/'] img",  # 이미지를 포함한 게시물/릴스 링크
            ]

            post_elements = []
            for selector in post_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    elements = await page.query_selector_all(selector)
                    if elements:
                        post_elements = elements
                        print(
                            f"[{file_suffix if file_suffix else ''}] 선택자 '{selector}'로 {len(elements)}개 요소 발견"
                        )
                        break
                except Exception:
                    continue

            if not post_elements:
                print(
                    f"[{file_suffix if file_suffix else ''}] 게시물을 찾을 수 없음, 다음 라운드 시도"
                )
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                self.random_sleep(2, 4)
                continue

            print(
                f"[{file_suffix if file_suffix else ''}][{r}] 현재까지 렌더링된 게시물 수: {len(post_elements)}"
            )
            new_posts = []

            for post in post_elements:
                # 게시물 링크 찾기
                href = None

                # 현재 요소가 a 태그인지 확인
                tag_name = await post.evaluate("node => node.tagName.toLowerCase()")

                if tag_name == "a":
                    # 이미 a 태그라면 직접 href 가져오기
                    href = await post.get_attribute("href")
                else:
                    # a 태그가 아니라면 부모나 자식에서 a 태그 찾기
                    parent_a = await post.evaluate_handle("node => node.closest('a')")
                    if parent_a:
                        href = await parent_a.get_attribute("href")
                    else:
                        # 자식에서 a 태그 찾기 (일반 게시물 + 릴스)
                        child_a = await post.query_selector(
                            "a[href*='/p/'], a[href*='/reel/']"
                        )
                        if child_a:
                            href = await child_a.get_attribute("href")

                # href 검증 및 정규화 (일반 게시물 + 릴스)
                if href and ("/p/" in href or "/reel/" in href):
                    if not href.startswith("http"):
                        href = "https://www.instagram.com" + href

                # 중복 체크용 post_id 추출
                post_id = self.extract_post_id(href)
                if post_id and post_id not in crawled_post_ids:
                    new_posts.append((post, href))
                    crawled_post_ids.add(post_id)

                    # 최대 게시물 수에 도달했는지 확인
                    if len(post_info) + len(new_posts) >= max_posts:
                        new_posts = new_posts[: max_posts - len(post_info)]
                        break

                    if len(new_posts) >= crawl_batch_size:
                        break

            print(
                f"[{file_suffix if file_suffix else ''}][{r}] 이번 라운드에서 크롤링할 게시물 수: {len(new_posts)}"
            )

            for post, href in new_posts:
                detail = await self.get_post_detail(page, href)
                post_data = {
                    "number": post_number,
                    "href": href,
                    "date": detail["date"] if detail else None,
                    "content": detail["content"] if detail else "",
                    "img": detail["img"] if detail else [],
                    "comments": detail["comments"] if detail else [],
                    "like_count": detail["like_count"] if detail else 0,
                    "comment_count": detail["comment_count"] if detail else 0,
                    "hashtags": detail["hashtags"] if detail else [],
                    "mentions": detail["mentions"] if detail else [],
                }
                post_info.append(post_data)
                post_number += 1

                # 최대 게시물 수에 도달하면 중지
                if len(post_info) >= max_posts:
                    print(
                        f"[{file_suffix if file_suffix else ''}] 최대 게시물 수 도달 ({max_posts})"
                    )
                    break

            # 최대 게시물 수에 도달하면 스크롤 중지
            if len(post_info) >= max_posts:
                break

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.random_sleep(1.5, 3.8)

        # JSON 파일로 저장 (백업용)
        file_path = os.path.join(
            self.data_dir,
            f"{target_name}{'_' + file_suffix if file_suffix else ''}.json",
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(post_info, f, ensure_ascii=False, indent=4)
        print(
            f"✅ {target_name}{'_' + file_suffix if file_suffix else ''}.json 저장 완료"
        )

        return post_info

    async def run(self, instagram_handle: str):
        """메인 실행 메서드 (JSON 저장용)"""
        # DB 사용 버전 (주석 처리)
        # brand_queries = BrandQueries()
        # data_queries = DataQueries()

        # 브랜드 정보 가져오기 (DB 사용 시)
        # brand_info = brand_queries.get_brand_by_id(brand_id)
        # if not brand_info:
        #     print(f"브랜드를 찾을 수 없습니다: {brand_id}")
        #     return

        # 채널 정보 가져오기 (DB 사용 시)
        # channels = brand_queries.get_brand_channels(brand_id)
        # if not channels or not channels.get('instagram_handle'):
        #     print(f"브랜드의 Instagram 핸들을 찾을 수 없습니다: {brand_info['brand_official_name']}")
        #     return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            await self.login(page)

            print(f"\n[*] Instagram 크롤링 시작: @{instagram_handle}")

            # 메인 게시물 크롤링
            target_url = f"https://www.instagram.com/{instagram_handle}/"
            posts_data = await self.crawl_posts(
                page,
                target_url,
                instagram_handle,
                max_scroll_round=Config.MAX_SCROLL_ROUND,
                crawl_batch_size=Config.CRAWL_BATCH_SIZE,
            )

            # JSON으로 상세 정보 저장
            if posts_data:
                detailed_posts = []
                for post in posts_data:
                    if not post.get("href"):
                        continue

                    post_id = self.extract_post_id(post["href"])
                    if not post_id:
                        continue

                    # 상세 정보 구성
                    detailed_post = {
                        "post_id": post_id,
                        "post_url": post["href"],
                        "caption": post.get("content", ""),
                        "media_urls": post.get("img", []),
                        "like_count": post.get("like_count", 0),
                        "comment_count": post.get("comment_count", 0),
                        "comments": post.get("comments", []),
                        "hashtags": post.get(
                            "hashtags", []
                        ),  # raw_data에서 직접 가져오기
                        "mentions": post.get(
                            "mentions", []
                        ),  # raw_data에서 직접 가져오기
                        "posted_at": post.get("date"),
                        "crawled_at": datetime.now().isoformat(),
                        "raw_data": post,
                    }
                    detailed_posts.append(detailed_post)

                # 상세 정보 JSON 저장
                detailed_file_path = os.path.join(
                    self.data_dir, f"{instagram_handle}_detailed.json"
                )
                with open(detailed_file_path, "w", encoding="utf-8") as f:
                    json.dump(detailed_posts, f, ensure_ascii=False, indent=4)
                print(
                    f"✅ {instagram_handle}_detailed.json 저장 완료 ({len(detailed_posts)}개 게시물)"
                )

                # DB 저장 코드 (주석 처리)
                # saved_count = 0
                # for post in posts_data:
                #     if not post.get('href'):
                #         continue
                #
                #     post_id = self.extract_post_id(post['href'])
                #     if not post_id:
                #         continue
                #
                #     # 중복 체크
                #     existing = self.data_queries.check_instagram_post_exists(brand_id, post_id)
                #     if existing:
                #         print(f"[*] 이미 존재하는 게시물 건너뛰기: {post_id}")
                #         continue
                #
                #     # 개별 게시물 저장
                #     instagram_data = {
                #         'brand_id': brand_id,
                #         'channel_id': channels['id'],
                #         'post_id': post_id,
                #         'post_url': post['href'],
                #         'caption': post.get('content', ''),
                #         'media_type': 'image',  # TODO: 비디오/캐러셀 타입 구분
                #         'media_urls': post.get('img', []),
                #         'like_count': post.get('like_count', 0),
                #         'comment_count': post.get('comment_count', 0),
                #         'hashtags': self._extract_hashtags(post.get('content', '')),
                #         'mentions': self._extract_mentions(post.get('content', '')),
                #         'posted_at': post.get('date'),
                #         'crawled_at': datetime.now(),
                #         'raw_data': post
                #     }
                #
                #     try:
                #         self.data_queries.insert_raw_instagram_data(instagram_data)
                #         saved_count += 1
                #     except Exception as e:
                #         print(f"[!] 게시물 저장 실패 ({post_id}): {str(e)}")
                #
                # print(f"[*] {saved_count}개 게시물 데이터베이스 저장 완료")

            # 태그된 게시물 크롤링
            tagged_url = f"https://www.instagram.com/{instagram_handle}/tagged/"
            tagged_data = await self.crawl_posts(
                page,
                tagged_url,
                instagram_handle,
                max_scroll_round=Config.MAX_SCROLL_ROUND,
                crawl_batch_size=Config.CRAWL_BATCH_SIZE,
                file_suffix="tagged",
            )

            # 태그된 게시물 상세 정보 JSON 저장
            if tagged_data:
                detailed_tagged = []
                for post in tagged_data:
                    if not post.get("href"):
                        continue

                    post_id = self.extract_post_id(post["href"])
                    if not post_id:
                        continue

                    # 상세 정보 구성
                    detailed_post = {
                        "post_id": post_id,
                        "post_url": post["href"],
                        "caption": post.get("content", ""),
                        "media_urls": post.get("img", []),
                        "like_count": post.get("like_count", 0),
                        "comment_count": post.get("comment_count", 0),
                        "comments": post.get("comments", []),
                        "hashtags": post.get(
                            "hashtags", []
                        ),  # raw_data에서 직접 가져오기
                        "mentions": post.get(
                            "mentions", []
                        ),  # raw_data에서 직접 가져오기
                        "posted_at": post.get("date"),
                        "crawled_at": datetime.now().isoformat(),
                        "is_tagged": True,  # 태그된 게시물 표시
                        "raw_data": post,
                    }
                    detailed_tagged.append(detailed_post)

                # 태그된 게시물 상세 정보 JSON 저장
                tagged_detailed_file_path = os.path.join(
                    self.data_dir, f"{instagram_handle}_tagged_detailed.json"
                )
                with open(tagged_detailed_file_path, "w", encoding="utf-8") as f:
                    json.dump(detailed_tagged, f, ensure_ascii=False, indent=4)
                print(
                    f"✅ {instagram_handle}_tagged_detailed.json 저장 완료 ({len(detailed_tagged)}개 게시물)"
                )

                # DB 저장 코드 (주석 처리)
                # saved_count = 0
                # for post in tagged_data:
                #     if not post.get('href'):
                #         continue
                #
                #     post_id = self.extract_post_id(post['href'])
                #     if not post_id:
                #         continue
                #
                #     # 중복 체크
                #     existing = self.data_queries.check_instagram_post_exists(brand_id, post_id)
                #     if existing:
                #         print(f"[*] 이미 존재하는 태그된 게시물 건너뛰기: {post_id}")
                #         continue
                #
                #     # 개별 게시물 저장
                #     instagram_data = {
                #         'brand_id': brand_id,
                #         'channel_id': channels['id'],
                #         'post_id': post_id,
                #         'post_url': post['href'],
                #         'caption': post.get('content', ''),
                #         'media_type': 'image',  # TODO: 비디오/캐러셀 타입 구분
                #         'media_urls': post.get('img', []),
                #         'like_count': post.get('like_count', 0),
                #         'comment_count': post.get('comment_count', 0),
                #         'hashtags': self._extract_hashtags(post.get('content', '')),
                #         'mentions': self._extract_mentions(post.get('content', '')),
                #         'posted_at': post.get('date'),
                #         'crawled_at': datetime.now(),
                #         'is_tagged': True,  # 태그된 게시물 표시
                #         'raw_data': post
                #     }
                #
                #     try:
                #         self.data_queries.insert_raw_instagram_data(instagram_data)
                #         saved_count += 1
                #     except Exception as e:
                #         print(f"[!] 태그된 게시물 저장 실패 ({post_id}): {str(e)}")
                #
                # print(f"[*] {saved_count}개 태그된 게시물 데이터베이스 저장 완료")

            await browser.close()

    def _extract_hashtags(self, text: str) -> List[str]:
        """텍스트에서 해시태그 추출"""
        if not text:
            return []
        # 한글, 영문, 숫자, 언더스코어를 포함한 해시태그 패턴
        hashtags = re.findall(r"#[\w가-힣]+(?:_[\w가-힣]+)*", text)
        # 중복 제거 및 정리
        cleaned_hashtags = []
        for tag in hashtags:
            if len(tag) > 1:  # '#' 만 있는 경우 제외
                cleaned_hashtags.append(tag)
        return list(set(cleaned_hashtags))

    def _extract_mentions(self, text: str) -> List[str]:
        """텍스트에서 멘션 추출"""
        if not text:
            return []
        # 영문, 숫자, 언더스코어, 마침표를 포함한 멘션 패턴
        mentions = re.findall(r"@[\w.]+(?:_[\w.]+)*", text)
        # 중복 제거 및 정리
        cleaned_mentions = []
        for mention in mentions:
            if len(mention) > 1:  # '@' 만 있는 경우 제외
                cleaned_mentions.append(mention)
        return list(set(cleaned_mentions))
