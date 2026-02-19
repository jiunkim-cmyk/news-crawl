import time
import json
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from datetime import datetime


class NaverNewsCrawler:
    """네이버 뉴스 검색 크롤러"""

    BASE_URL = "https://search.naver.com/search.naver"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, keyword: str, max_pages: int = 5):
        self.keyword = keyword
        self.max_pages = max_pages
        self.articles = []

    def crawl(self) -> List[Dict]:
        """뉴스 기사 목록 크롤링"""
        self.articles = []

        for page in range(1, self.max_pages + 1):
            start = (page - 1) * 10 + 1
            params = {
                "where": "news",
                "query": self.keyword,
                "start": start,
                "sort": 1,  # 최신순
            }

            try:
                resp = requests.get(
                    self.BASE_URL, params=params, headers=self.HEADERS, timeout=10
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"[네이버] 페이지 {page} 요청 실패: {e}")
                continue

            articles = self._parse_page(resp.text)
            if not articles:
                break

            self.articles.extend(articles)
            print(f"[네이버] 페이지 {page} - {len(articles)}건 수집")
            time.sleep(1)  # 서버 부하 방지

        print(f"[네이버] 총 {len(self.articles)}건 수집 완료")
        return self.articles

    def _parse_page(self, html: str) -> List[Dict]:
        """검색 결과 페이지 파싱"""
        soup = BeautifulSoup(html, "html.parser")
        articles = []

        news_items = soup.select("div.news_area")
        for item in news_items:
            article = self._parse_item(item)
            if article:
                articles.append(article)

        return articles

    def _parse_item(self, item) -> Optional[Dict]:
        """개별 뉴스 아이템 파싱"""
        try:
            # 제목 & 링크
            title_tag = item.select_one("a.news_tit")
            if not title_tag:
                return None
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")

            # 언론사
            press_tag = item.select_one("a.info.press")
            press = press_tag.get_text(strip=True) if press_tag else "알 수 없음"

            # 요약
            desc_tag = item.select_one("div.news_dsc") or item.select_one(
                "a.api_txt_lines.dsc_txt_wrap"
            )
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            # 날짜
            date_tag = item.select_one("span.info")
            date_text = date_tag.get_text(strip=True) if date_tag else ""

            return {
                "title": title,
                "link": link,
                "press": press,
                "description": description,
                "date": date_text,
                "source": "naver",
                "keyword": self.keyword,
                "crawled_at": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"[네이버] 파싱 오류: {e}")
            return None

    def save(self, filepath: str):
        """수집 결과를 JSON 파일로 저장"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)
        print(f"[네이버] {filepath}에 저장 완료")
