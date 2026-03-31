from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.db_connection import get_connection

# =========================
# 설정 영역 (크롤링 조건)
# =========================
QUERY = "전기차 보조금"  # 네이버 뉴스 검색 키워드
START_DATE = datetime(2022, 4, 1)   # 시작 날짜
END_DATE = datetime(2026, 3, 30)    # 종료 날짜

# =========================
# DB 연결 생성
# =========================
conn = get_connection()
cursor = conn.cursor()

# =========================
# Selenium 드라이버 설정
# =========================
# ChromeDriver 자동 설치 및 실행
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# =========================
# 크롤링 루프 (날짜 단위)
# =========================
current_date = START_DATE

while current_date <= END_DATE:
    # 날짜를 네이버 파라미터 형식으로 변환 (YYYY.MM.DD)
    ds = current_date.strftime("%Y.%m.%d")
    print(f"\n=== {ds} 수집 시작 ===")

    # 네이버 뉴스 검색 URL 구성
    url = (
        f"https://search.naver.com/search.naver?"
        f"ssc=tab.news.all&query={QUERY}"
        f"&sm=tab_opt&sort=0&photo=0&field=0"
        f"&pd=3&ds={ds}&de={ds}"  # 날짜 필터 (하루 단위)
    )

    # 페이지 로딩
    driver.get(url)
    time.sleep(2)  # 초기 렌더링 대기

    # =========================
    # Infinite Scroll 처리
    # =========================
    # 네이버 뉴스는 스크롤 시 추가 데이터 로딩됨
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 페이지 끝까지 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # 로딩 대기

        # 새로운 높이 측정
        new_height = driver.execute_script("return document.body.scrollHeight")

        # 더 이상 증가하지 않으면 끝
        if new_height == last_height:
            break

        last_height = new_height

    # =========================
    # HTML 파싱
    # =========================
    soup = BeautifulSoup(driver.page_source, "lxml")

    # 뉴스 제목 + 링크 선택자
    # (네이버 구조 변경 시 가장 먼저 깨지는 부분)
    news_list = soup.select('a[data-heatmap-target=".tit"]')

    data_batch = []
    seen = set()  # 중복 URL 제거용

    for news in news_list:
        title = news.get_text(strip=True)  # 뉴스 제목
        link = news.get("href")           # 뉴스 URL

        if not title or not link:
            continue

        # 동일 페이지 내 중복 제거
        if link in seen:
            continue
        seen.add(link)

        # DB insert용 튜플
        data_batch.append((title, link, current_date.date()))

    # =========================
    # DB 저장 (배치 insert)
    # =========================
    if data_batch:
        CREATE_SQL = """
        CREATE TABLE IF NOT EXISTS `ev_news` (
        `id` int NOT NULL AUTO_INCREMENT,
        `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '제목',
        `url` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'URL',
        `date` date NOT NULL COMMENT '날짜',
        PRIMARY KEY (`id`),
        UNIQUE KEY `unique_url` (`url`),
        KEY `idx_ev_news_date` (`date`)
        ) ENGINE=InnoDB 
        DEFAULT CHARSET=utf8mb4 
        COLLATE=utf8mb4_unicode_ci 
        COMMENT='전기차_뉴스';
        """
        cursor.execute(CREATE_SQL)
        conn.commit()

        sql = """
        INSERT IGNORE INTO ev_news (title, url, date)
        VALUES (%s, %s, %s)
        """
        # executemany → 여러 건 한번에 insert (성능 중요)
        cursor.executemany(sql, data_batch)
        conn.commit()

    print(f"{len(data_batch)}건 저장 완료")

    # 다음 날짜로 이동 (1일 단위)
    current_date += timedelta(days=1)

    # 서버/브라우저 부하 방지
    time.sleep(1)

# =========================
# 종료 처리
# =========================
driver.quit()   # 브라우저 종료
cursor.close()  # DB 커서 종료
conn.close()    # DB 연결 종료

print("\n전체 크롤링 완료")