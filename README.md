# News Crawl - 다리마티 뉴스 수집 & 인사이트 분석

다리마티 관련 뉴스 기사를 수집하고 인사이트를 분석하는 프로젝트

## 목표

- 다리마티 관련 뉴스 기사 자동 수집 (크롤링)
- 수집된 기사 데이터 정리 및 저장
- 키워드/트렌드 분석
- 인사이트 리포트 생성

## 프로젝트 구조

```
news-crawl/
├── README.md
├── crawlers/        # 뉴스 크롤러 스크립트
├── data/            # 수집된 기사 데이터
├── analysis/        # 분석 결과
└── reports/         # 인사이트 리포트
```

## 기술 스택

- Python
- BeautifulSoup / Requests (크롤링)
- Pandas (데이터 처리)

## 사용법

```bash
pip install -r requirements.txt

# 기본 실행 (다리마티 키워드, 네이버+구글, 한국어+영어)
python main.py

# 커스텀 키워드 검색
python main.py -k "DARIMATI BR-001" "DARIMATI running shoe" "다리마티"

# 구글 뉴스만, 영어만
python main.py -k "DARIMATI" -s google -l en

# 네이버 5페이지 검색
python main.py -k "다리마티" -s naver -p 5
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-k, --keyword` | 검색 키워드 (복수 가능) | 다리마티 |
| `-s, --source` | 크롤링 소스 (all/naver/google) | all |
| `-l, --lang` | Google News 언어 (ko/en/both) | both |
| `-p, --pages` | 네이버 검색 페이지 수 | 3 |
