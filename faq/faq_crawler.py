import asyncio
import re
import html
from typing import List, Dict
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import mysql.connector
from dotenv import load_dotenv
import os

# =====================
# 환경변수 로드
# =====================
# .env 파일에서 DB 접속 정보 불러오기
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "car_db"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

# =====================
# 크롤링 대상 URL
# =====================
KIA_URL = "https://www.kia.com/kr/vehicles/kia-ev/guide/faq"
KEPCO_API_URL = "https://plug.kepco.co.kr:23001/api/v1/faq"
HYUNDAI_URL = "https://www.hyundai.com/kr/ko/faq.html"
TESLA_BLOG_URL = "https://blog.naver.com/teslakr_official/224174286716"


# =====================
# 공통 유틸
# =====================
def clean_text(text: str) -> str:
    # HTML 엔티티 변환 후 공백 정리
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_html_tags(raw_html: str) -> str:
    # HTML 태그 제거 + 줄바꿈/공백 정리
    if not raw_html:
        return ""
    raw_html = html.unescape(raw_html)
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def validate_item(item: Dict) -> bool:
    # 최소한 question, answer, source가 있어야 유효 데이터로 봄
    return bool(item.get("question") and item.get("answer") and item.get("source"))


def deduplicate_items(items: List[Dict]) -> List[Dict]:
    # 질문/답변/출처가 완전히 같은 데이터는 중복 제거
    seen = set()
    result = []
    for item in items:
        key = (
            item.get("question", "").strip(),
            item.get("answer", "").strip(),
            item.get("source", "").strip(),
        )
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


async def safe_inner_text(element) -> str:
    # Playwright 요소에서 텍스트 추출 실패 시 빈 문자열 반환
    try:
        return clean_text(await element.inner_text())
    except Exception:
        return ""


async def safe_inner_html_text(element) -> str:
    # Playwright 요소의 inner_html을 텍스트로 정리해서 반환
    try:
        raw = await element.inner_html()
        return strip_html_tags(raw)
    except Exception:
        return ""


# =====================
# 크롤러: Kia
# =====================
async def crawl_kia(browser) -> List[Dict]:
    print("Crawling Kia...")
    page = await browser.new_page()
    results = []

    try:
        # JS 렌더링까지 고려해서 페이지 로드
        await page.goto(KIA_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # 사이트 구조가 달라질 수 있어서 셀렉터 후보를 여러 개 둠
        selector_candidates = [
            ".cmp-accordion__item",
            "[class*='accordion']",
            "[class*='faq'] li",
            "[class*='faq'] .item",
        ]

        faq_items = []
        for selector in selector_candidates:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                faq_items = await page.query_selector_all(selector)
                if faq_items:
                    print(f"[Kia] matched selector: {selector}, count={len(faq_items)}")
                    break
            except PlaywrightTimeoutError:
                # 해당 셀렉터가 안 맞으면 다음 후보 시도
                continue

        if not faq_items:
            print("[Kia] FAQ items not found")
            return []

        for item in faq_items:
            question = ""
            answer = ""

            # 질문이 들어있을 가능성이 있는 태그들을 순서대로 확인
            for q_sel in ["button.cmp-accordion__button", "dt", "summary", "button", "h3", "h4"]:
                q_el = await item.query_selector(q_sel)
                if q_el:
                    question = await safe_inner_text(q_el)
                    if question:
                        break

            # 답변이 들어있을 가능성이 있는 태그들을 순서대로 확인
            for a_sel in [".cmp-accordion__panel", "dd", "[class*='panel']", "[class*='content']", "[class*='answer']", "div"]:
                a_el = await item.query_selector(a_sel)
                if a_el:
                    answer = await safe_inner_html_text(a_el)
                    if answer:
                        break

            row = {"question": question, "answer": answer, "category": "Kia EV Guide", "source": "기아"}
            if validate_item(row):
                results.append(row)

    except PlaywrightTimeoutError:
        print("[Kia] page load timeout")
    except Exception as e:
        print(f"[Kia] failed: {e}")
    finally:
        await page.close()

    return deduplicate_items(results)


# =====================
# 크롤러: Tesla (네이버 블로그 정적 파싱)
# =====================
def crawl_tesla() -> List[Dict]:
    """
    Tesla 공식 네이버 블로그 FAQ 크롤러
    - quotation 블록을 질문으로 보고
    - 다음 quotation 전까지를 답변으로 묶는 방식
    """
    print("Crawling Tesla Blog FAQ...")
    results = []

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Referer": "https://blog.naver.com/",
        }

        # 네이버 블로그 본문은 iframe 구조라 PostView URL로 직접 접근
        post_view_url = "https://blog.naver.com/PostView.naver?blogId=teslakr_official&logNo=224174286716"
        response = requests.get(post_view_url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")
        main = soup.select_one(".se-main-container")

        if not main:
            print("[Tesla] se-main-container를 찾지 못했습니다.")
            return []

        components = main.select(".se-component")
        print(f"[Tesla] 총 {len(components)}개 컴포넌트 발견")

        i = 0
        while i < len(components):
            comp = components[i]
            classes = comp.get("class", [])

            # 질문 블록 시작
            if "se-quotation" in classes:
                question = clean_text(comp.get_text(separator=" "))

                # 다음 질문 블록 전까지 답변 수집
                answer_parts = []
                j = i + 1
                while j < len(components):
                    next_comp = components[j]
                    next_classes = next_comp.get("class", [])
                    if "se-quotation" in next_classes or "se-horizontalLine" in next_classes:
                        break
                    text = strip_html_tags(str(next_comp))
                    if text:
                        answer_parts.append(text)
                    j += 1

                answer = "\n\n".join(answer_parts).strip()

                row_data = {
                    "question": question,
                    "answer": answer,
                    "category": "Tesla FAQ",
                    "source": "테슬라",
                }
                if validate_item(row_data):
                    results.append(row_data)

                i = j  # 이미 읽은 답변 영역은 건너뜀
            else:
                i += 1

    except Exception as e:
        print(f"[Tesla] failed: {e}")

    print(f"[Tesla] {len(results)}건 파싱 완료")
    return deduplicate_items(results)


# =====================
# 크롤러: KEPCO (REST API)
# =====================
def crawl_kepco() -> List[Dict]:
    print("Crawling KEPCO API...")
    results = []

    try:
        # API 응답을 바로 받아서 처리
        response = requests.get(KEPCO_API_URL, timeout=15, verify=False)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, list):
            print("[KEPCO] response is not list")
            return []

        for item in data:
            row = {
                "question": clean_text(item.get("question", "")),
                "answer": strip_html_tags(item.get("answer", "")),
                "category": "KEPCO PLUG FAQ",
                "source": "한전",
            }
            if validate_item(row):
                results.append(row)

    except Exception as e:
        print(f"[KEPCO] failed: {e}")

    return deduplicate_items(results)


# =====================
# 크롤러: Hyundai (Playwright)
# =====================
async def crawl_hyundai(browser) -> List[Dict]:
    print("Crawling Hyundai...")
    page = await browser.new_page()
    results = []

    try:
        await page.goto(HYUNDAI_URL, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

        while True:
            # 현재 페이지 FAQ 목록 로드 대기
            await page.wait_for_selector("div.ui_accordion.acc_01 dl", timeout=10000)
            await page.wait_for_timeout(1000)

            faq_list = await page.query_selector_all("div.ui_accordion.acc_01 dl")
            if not faq_list:
                print("[Hyundai] FAQ items not found on this page")
                break

            print(f"[Hyundai] found {len(faq_list)} items on current page")

            for faq in faq_list:
                try:
                    dt = await faq.query_selector("dt")
                    if not dt:
                        continue

                    category_el = await dt.query_selector("b i")
                    title_el = await dt.query_selector("b span")

                    category = await safe_inner_text(category_el) if category_el else "기타"
                    title = await safe_inner_text(title_el) if title_el else ""

                    if not title:
                        continue

                    # 아코디언 형태라 클릭해서 답변 펼친 뒤 내용 추출
                    await dt.evaluate("el => el.click()")
                    await page.wait_for_timeout(300)

                    content_el = await faq.query_selector("dd div.exp")
                    content = await safe_inner_html_text(content_el) if content_el else ""

                    row = {
                        "question": title,
                        "answer": content,
                        "category": category,
                        "source": "현대자동차",
                    }
                    if validate_item(row):
                        results.append(row)

                except Exception as e:
                    print(f"[Hyundai] item error: {e}")
                    continue

            # strong 다음 a 태그를 다음 페이지 버튼으로 사용
            try:
                next_btn = await page.query_selector("div.pagination strong + a")
                if not next_btn:
                    print("[Hyundai] no next page, done")
                    break

                await next_btn.evaluate("el => el.click()")
                await page.wait_for_timeout(2000)

            except Exception:
                print("[Hyundai] pagination ended")
                break

    except PlaywrightTimeoutError:
        print("[Hyundai] page load timeout")
    except Exception as e:
        print(f"[Hyundai] failed: {e}")
    finally:
        await page.close()

    return deduplicate_items(results)


# =====================
# DB 저장
# =====================
def create_table_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faq (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            question      TEXT NOT NULL,
            answer        LONGTEXT NOT NULL,
            answer_clean  LONGTEXT NULL,
            cleaned_at DATETIME NULL,
            category      VARCHAR(100),
            source        VARCHAR(100) NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """)
    conn.commit()
    cursor.close()
    print("[DB] 테이블 확인/생성 완료")


def save_to_db(items: List[Dict]):
    print(f"\n[DB] {len(items)}건 저장 시작...")

    conn = mysql.connector.connect(**DB_CONFIG)
    create_table_if_not_exists(conn)

    cursor = conn.cursor()
    query = """
        INSERT INTO faq (question, answer, category, source)
        VALUES (%s, %s, %s, %s)
    """

    success = 0
    for item in items:
        try:
            # 현재는 중복 검사 없이 그대로 insert
            cursor.execute(query, (
                item.get("question", ""),
                item.get("answer", ""),
                item.get("category", ""),
                item.get("source", ""),
            ))
            success += 1
        except Exception as e:
            print(f"[DB] insert error: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"[DB] 저장 완료: {success}/{len(items)}건")


# =====================
# 요약 출력
# =====================
def print_summary(items: List[Dict]):
    print("\n===== Crawl Summary =====")
    print(f"Total items: {len(items)}")

    source_count = {}
    for item in items:
        src = item["source"]
        source_count[src] = source_count.get(src, 0) + 1

    # 출처별 수집 개수 확인용
    for source, count in source_count.items():
        print(f"  - {source}: {count}건")

    print("=========================\n")


# =====================
# 메인
# =====================
async def main():
    all_data = []

    # Playwright가 필요한 사이트(기아, 현대) 먼저 처리
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        kia_data = await crawl_kia(browser)
        hyundai_data = await crawl_hyundai(browser)

        await browser.close()

    # requests 기반 사이트/API는 브라우저 없이 처리
    kepco_data = crawl_kepco()
    tesla_data = crawl_tesla()

    all_data.extend(kia_data)
    all_data.extend(hyundai_data)
    all_data.extend(kepco_data)
    all_data.extend(tesla_data)

    # 전체 한 번 더 중복 제거
    all_data = deduplicate_items(all_data)

    print_summary(all_data)
    save_to_db(all_data)


if __name__ == "__main__":
    asyncio.run(main())