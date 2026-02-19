import os
import json
import argparse
from typing import List, Dict
from datetime import datetime

import pandas as pd

from crawlers import NaverNewsCrawler, GoogleNewsCrawler


def merge_and_deduplicate(all_articles: List[Dict]) -> List[Dict]:
    """중복 기사 제거 (제목 기준)"""
    seen_titles = set()
    unique = []
    for article in all_articles:
        title = article["title"].strip()
        if title not in seen_titles:
            seen_titles.add(title)
            unique.append(article)
    return unique


def save_results(articles: List[Dict], keyword: str):
    """결과를 JSON + CSV로 저장"""
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"data/{keyword}_{timestamp}"

    # JSON
    json_path = f"{base_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    # CSV
    csv_path = f"{base_name}.csv"
    df = pd.DataFrame(articles)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"\n저장 완료:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    return json_path, csv_path


def print_summary(articles: List[Dict]):
    """수집 결과 요약 출력"""
    if not articles:
        print("\n수집된 기사가 없습니다.")
        return

    df = pd.DataFrame(articles)
    print(f"\n{'='*60}")
    print(f"수집 결과 요약")
    print(f"{'='*60}")
    print(f"총 기사 수: {len(articles)}건")
    print(f"소스별: {df['source'].value_counts().to_dict()}")
    print(f"언론사별 상위 5:")
    for press, count in df["press"].value_counts().head(5).items():
        print(f"  - {press}: {count}건")
    print(f"\n최근 기사 5건:")
    for i, row in df.head(5).iterrows():
        print(f"  [{row['press']}] {row['title']}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="다리마티 뉴스 크롤러")
    parser.add_argument(
        "-k", "--keyword", default="다리마티", help="검색 키워드 (기본: 다리마티)"
    )
    parser.add_argument(
        "-p", "--pages", type=int, default=3, help="네이버 검색 페이지 수 (기본: 3)"
    )
    parser.add_argument(
        "-s",
        "--source",
        choices=["all", "naver", "google"],
        default="all",
        help="크롤링 소스 (기본: all)",
    )
    args = parser.parse_args()

    print(f"키워드: '{args.keyword}' 뉴스 수집 시작\n")
    all_articles = []

    if args.source in ("all", "naver"):
        naver = NaverNewsCrawler(args.keyword, max_pages=args.pages)
        all_articles.extend(naver.crawl())

    if args.source in ("all", "google"):
        google = GoogleNewsCrawler(args.keyword)
        all_articles.extend(google.crawl())

    # 중복 제거
    articles = merge_and_deduplicate(all_articles)
    print(f"\n중복 제거 후: {len(articles)}건")

    # 요약 출력
    print_summary(articles)

    # 저장
    if articles:
        save_results(articles, args.keyword)


if __name__ == "__main__":
    main()
