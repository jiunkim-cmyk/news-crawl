#!/usr/bin/env python3
"""
주간 자동 크롤링 → 분석 → Slack 알림 스크립트

사용법:
    python weekly_report.py
    python weekly_report.py --dry-run   # Slack 발송 없이 테스트
"""
import os
import sys
import json
import argparse
from typing import List, Dict, Tuple
from datetime import datetime
from collections import Counter

import pandas as pd

# .env 파일 로드 (python-dotenv 있으면 사용)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from crawlers import NaverNewsCrawler, GoogleNewsCrawler
from slack_notifier import SlackNotifier


# --- 검색 설정 ---
KEYWORDS = [
    "DARIMATI BR-001",
    "DARIMATI running shoe",
    "DARIMATI",
    "다리마티",
    "darimati",
]

GOOGLE_LANGS = [("ko", "KR"), ("en", "US")]
NAVER_PAGES = 3


def crawl_all() -> Tuple[List[Dict], int]:
    """모든 키워드 + 소스로 크롤링 실행"""
    all_articles = []

    for kw in KEYWORDS:
        # Naver (한국어 키워드만)
        if any(ord(c) >= 0xAC00 for c in kw):  # 한글 포함 여부
            naver = NaverNewsCrawler(kw, max_pages=NAVER_PAGES)
            all_articles.extend(naver.crawl())

        # Google News (한국어 + 영어)
        for lang, country in GOOGLE_LANGS:
            google = GoogleNewsCrawler(kw, lang=lang, country=country)
            all_articles.extend(google.crawl())

    total = len(all_articles)
    return all_articles, total


def deduplicate(articles: List[Dict]) -> List[Dict]:
    """제목 기준 중복 제거"""
    seen = set()
    unique = []
    for a in articles:
        title = a["title"].strip()
        if title not in seen:
            seen.add(title)
            unique.append(a)
    return unique


def is_relevant(article: Dict) -> bool:
    """DARIMATI 직접 관련 기사인지 판별"""
    text = (article.get("title", "") + " " + article.get("description", "")).lower()
    relevant_terms = ["darimati", "br-001", "br001", "다리마티"]
    return any(term in text for term in relevant_terms)


def analyze(articles: List[Dict]) -> Dict:
    """수집 데이터 분석"""
    df = pd.DataFrame(articles) if articles else pd.DataFrame()

    relevant = [a for a in articles if is_relevant(a)]
    noise = [a for a in articles if not is_relevant(a)]

    # 소스별 카운트
    by_source = dict(Counter(a["source"] for a in articles)) if articles else {}

    # 키워드별 카운트
    by_keyword = dict(Counter(a["keyword"] for a in articles)) if articles else {}

    # 언론사별 카운트 (상위 5)
    press_counts = Counter(a["press"] for a in articles)
    top_press = dict(press_counts.most_common(5))

    return {
        "total": len(articles),
        "relevant": len(relevant),
        "noise": len(noise),
        "relevant_articles": relevant,
        "by_source": by_source,
        "by_keyword": by_keyword,
        "top_press": top_press,
    }


def generate_insights(analysis: Dict, prev_analysis: Dict = None) -> List[str]:
    """분석 결과에서 인사이트 생성"""
    insights = []
    relevant = analysis["relevant"]
    total = analysis["total"]

    if relevant == 0:
        insights.append(
            "DARIMATI 직접 관련 기사가 아직 검색되지 않습니다. "
            "오가닉 미디어 커버리지가 부족한 상태입니다."
        )
    else:
        insights.append(
            f"DARIMATI 직접 관련 기사 {relevant}건 발견. "
            f"(전체 {total}건 중 {relevant/total*100:.0f}%)"
        )

    if total > 0 and relevant == 0:
        insights.append(
            f"수집 {total}건 모두 노이즈 — '다리'+'마티' 분리 매칭 또는 비관련 기사입니다."
        )

    # 주간 변화 비교 (이전 데이터 있을 때)
    if prev_analysis:
        diff = relevant - prev_analysis.get("relevant", 0)
        if diff > 0:
            insights.append(f"지난주 대비 관련 기사 +{diff}건 증가")
        elif diff == 0:
            insights.append("지난주와 동일한 커버리지 수준")

    # Google News 인덱싱 확인
    google_count = analysis["by_source"].get("google", 0)
    naver_count = analysis["by_source"].get("naver", 0)
    if google_count > 0:
        insights.append(f"Google News {google_count}건, Naver {naver_count}건 수집")

    return insights


def generate_next_steps(analysis: Dict) -> List[str]:
    """다음 주 핵심 액션 아이템 생성"""
    steps = []
    relevant = analysis["relevant"]

    if relevant == 0:
        steps.extend([
            "Kickstarter 캠페인 종료 후 '펀딩 성공' PR 발행 준비",
            "러닝 전문 매체(Runner's World, Believe in the Run) 리뷰 샘플 발송",
            "자사 블로그에 SEO 최적화 콘텐츠 게시 (DARIMATI BR-001 키워드)",
            "한국 러닝 커뮤니티(런데이, 러너스하이) 타겟 콘텐츠 배포",
        ])
    elif relevant < 5:
        steps.extend([
            "발견된 기사의 2차 확산 유도 (SNS 공유, 커뮤니티 포스팅)",
            "기사 작성 매체에 후속 인터뷰 또는 리뷰 제안",
            "추가 매체 아웃리치 진행",
        ])
    else:
        steps.extend([
            "커버리지 포트폴리오 정리 및 미디어 킷 업데이트",
            "미디어 클리핑 보고서 작성",
            "성과 기반 다음 PR 전략 수립",
        ])

    return steps


def save_weekly_data(articles: List[Dict], analysis: Dict):
    """주간 데이터 저장"""
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 기사 데이터
    if articles:
        json_path = f"data/weekly_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        csv_path = f"data/weekly_{timestamp}.csv"
        df = pd.DataFrame(articles)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # 분석 요약 (Slack 발송 로그)
    os.makedirs("reports", exist_ok=True)
    summary_path = f"reports/weekly_{timestamp}.json"
    summary = {
        "date": datetime.now().isoformat(),
        "total": analysis["total"],
        "relevant": analysis["relevant"],
        "noise": analysis["noise"],
        "by_source": analysis["by_source"],
        "by_keyword": analysis["by_keyword"],
        "top_press": analysis["top_press"],
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[저장] data/weekly_{timestamp}.* , reports/weekly_{timestamp}.json")
    return summary_path


def load_previous_analysis() -> Dict:
    """가장 최근 주간 분석 데이터 로드"""
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return {}

    weekly_files = sorted(
        [f for f in os.listdir(reports_dir) if f.startswith("weekly_") and f.endswith(".json")],
        reverse=True,
    )

    if not weekly_files:
        return {}

    try:
        with open(os.path.join(reports_dir, weekly_files[0]), "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def main():
    parser = argparse.ArgumentParser(description="DARIMATI 주간 자동 리포트")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Slack 발송 없이 크롤링 + 분석만 실행",
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"DARIMATI 주간 리포트 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    # 1. 크롤링
    print("[Step 1] 크롤링 시작...")
    all_articles, total_raw = crawl_all()
    articles = deduplicate(all_articles)
    print(f"  원본 {total_raw}건 → 중복 제거 후 {len(articles)}건\n")

    # 2. 분석
    print("[Step 2] 분석 중...")
    prev_analysis = load_previous_analysis()
    analysis = analyze(articles)
    insights = generate_insights(analysis, prev_analysis)
    next_steps = generate_next_steps(analysis)

    print(f"  관련 기사: {analysis['relevant']}건 / 노이즈: {analysis['noise']}건")
    print(f"  인사이트 {len(insights)}건, 액션 아이템 {len(next_steps)}건\n")

    # 3. 저장
    print("[Step 3] 데이터 저장...")
    save_weekly_data(articles, analysis)

    # 4. 콘솔 출력
    print(f"\n{'='*60}")
    print("인사이트:")
    for ins in insights:
        print(f"  • {ins}")
    print("\n다음 주 핵심 Step:")
    for i, step in enumerate(next_steps, 1):
        print(f"  {i}. {step}")
    print(f"{'='*60}\n")

    # 5. Slack 발송
    if args.dry_run:
        print("[Dry Run] Slack 발송 스킵")
        return

    try:
        notifier = SlackNotifier()
        crawl_stats = {
            "total": total_raw,
            "unique": len(articles),
            "by_source": ", ".join(f"{k}: {v}건" for k, v in analysis["by_source"].items()),
            "keywords": ", ".join(KEYWORDS),
        }
        success = notifier.send_weekly_report(
            crawl_stats=crawl_stats,
            top_articles=analysis["relevant_articles"][:5],
            insights=insights,
            next_steps=next_steps,
        )
        if success:
            print("[완료] Slack 리포트 발송 성공!")
        else:
            print("[실패] Slack 발송에 실패했습니다.")
            sys.exit(1)
    except ValueError as e:
        print(f"[경고] {e}")
        print("  → .env 파일에 SLACK_WEBHOOK_URL을 설정해주세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
