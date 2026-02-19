#!/bin/bash
# DARIMATI 주간 리포트 cron job 설정 스크립트
#
# 사용법: bash setup_cron.sh
# 기본: 매주 월요일 오전 9시 실행

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"
SCRIPT="$PROJECT_DIR/weekly_report.py"
LOG="$PROJECT_DIR/logs/cron.log"

# 로그 디렉토리 생성
mkdir -p "$PROJECT_DIR/logs"

# cron 스케줄 (매주 월요일 09:00)
CRON_SCHEDULE="0 9 * * 1"
CRON_CMD="cd $PROJECT_DIR && $PYTHON $SCRIPT >> $LOG 2>&1"

# 기존 cron에서 이 프로젝트 관련 항목 제거 후 추가
(crontab -l 2>/dev/null | grep -v "weekly_report.py") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_CMD") | crontab -

echo "✓ Cron job 등록 완료"
echo "  스케줄: 매주 월요일 09:00"
echo "  스크립트: $SCRIPT"
echo "  로그: $LOG"
echo ""
echo "현재 crontab:"
crontab -l
