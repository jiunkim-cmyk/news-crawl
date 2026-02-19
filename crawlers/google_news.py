import json
from typing import List, Dict

import feedparser
from datetime import datetime


class GoogleNewsCrawler:
    """Google News RSS 크롤러"""

    RSS_URL = "https://news.google.com/rss/search"

    def __init__(self, keyword: str, lang: str = "ko", country: str = "KR"):
        self.keyword = keyword
        self.lang = lang
        self.country = country
        self.articles = []

    def crawl(self) -> List[Dict]:
        """Google News RSS 피드에서 기사 수집"""
        self.articles = []

        url = (
            f"{self.RSS_URL}"
            f"?q={self.keyword}"
            f"&hl={self.lang}"
            f"&gl={self.country}"
            f"&ceid={self.country}:{self.lang}"
        )

        feed = feedparser.parse(url)

        if feed.bozo:
            print(f"[구글] RSS 파싱 경고: {feed.bozo_exception}")

        for entry in feed.entries:
            article = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "press": entry.get("source", {}).get("title", "알 수 없음"),
                "description": self._clean_html(entry.get("summary", "")),
                "date": entry.get("published", ""),
                "source": "google",
                "keyword": self.keyword,
                "crawled_at": datetime.now().isoformat(),
            }
            self.articles.append(article)

        print(f"[구글] 총 {len(self.articles)}건 수집 완료")
        return self.articles

    @staticmethod
    def _clean_html(text: str) -> str:
        """HTML 태그 제거"""
        from bs4 import BeautifulSoup

        return BeautifulSoup(text, "html.parser").get_text(strip=True)

    def save(self, filepath: str):
        """수집 결과를 JSON 파일로 저장"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)
        print(f"[구글] {filepath}에 저장 완료")
