import os
import json
from typing import List, Dict
from datetime import datetime

import requests


class SlackNotifier:
    """Slack Incoming Webhook을 통한 알림 발송"""

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError(
                "SLACK_WEBHOOK_URL이 설정되지 않았습니다. "
                ".env 파일 또는 환경변수를 확인하세요."
            )

    def send(self, blocks: List[Dict]) -> bool:
        """Slack Block Kit 메시지 발송"""
        payload = {"blocks": blocks}
        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200 and resp.text == "ok":
                print("[Slack] 메시지 발송 성공")
                return True
            else:
                print(f"[Slack] 발송 실패: {resp.status_code} {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"[Slack] 발송 오류: {e}")
            return False

    def send_weekly_report(
        self,
        crawl_stats: Dict,
        top_articles: List[Dict],
        insights: List[str],
        next_steps: List[str],
    ) -> bool:
        """주간 리포트 포맷팅 후 발송"""
        today = datetime.now().strftime("%Y-%m-%d")
        blocks = []

        # 헤더
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"DARIMATI 주간 뉴스 리포트 ({today})",
            },
        })

        blocks.append({"type": "divider"})

        # 수집 현황
        stats_lines = [
            f"*총 수집*: {crawl_stats.get('total', 0)}건",
            f"*중복 제거 후*: {crawl_stats.get('unique', 0)}건",
            f"*소스별*: {crawl_stats.get('by_source', '-')}",
            f"*검색 키워드*: {crawl_stats.get('keywords', '-')}",
        ]
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":newspaper:  *수집 현황*\n" + "\n".join(stats_lines),
            },
        })

        blocks.append({"type": "divider"})

        # 주요 기사
        if top_articles:
            article_lines = []
            for i, a in enumerate(top_articles[:5], 1):
                article_lines.append(
                    f"{i}. <{a.get('link', '#')}|{a.get('title', '제목 없음')}> "
                    f"- _{a.get('press', '알 수 없음')}_"
                )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":mag:  *주요 기사 TOP 5*\n" + "\n".join(article_lines),
                },
            })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":mag:  *주요 기사*\n_이번 주 DARIMATI 직접 관련 기사 없음_",
                },
            })

        blocks.append({"type": "divider"})

        # 인사이트
        insight_lines = [f"• {ins}" for ins in insights]
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":bulb:  *인사이트*\n" + "\n".join(insight_lines),
            },
        })

        blocks.append({"type": "divider"})

        # 다음 주 핵심 Step
        step_lines = [f"*{i}.* {step}" for i, step in enumerate(next_steps, 1)]
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":rocket:  *다음 주 핵심 Step*\n" + "\n".join(step_lines),
            },
        })

        # 푸터
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_news-crawl 자동 리포트 | {today}_",
                }
            ],
        })

        return self.send(blocks)
