import re
import html
import time
from typing import List, Dict
from bs4 import BeautifulSoup
import requests
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.db_connection import get_connection

# Selenium 관련
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_html_tags(raw_html: str) -> str:
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
    return bool(item.get("question") and item.get("answer") and item.get("source"))


def deduplicate_items(items: List[Dict]) -> List[Dict]:
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


def safe_text(element) -> str:
    try:
        return clean_text(element.text)
    except Exception:
        return ""


def safe_inner_html_text(element) -> str:
    try:
        raw = element.get_attribute("innerHTML")
        return strip_html_tags(raw)
    except Exception:
        return ""


def create_driver():
    # 필요하면 headless=False로 바꿔서 브라우저 보면서 디버깅 가능
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


# =====================
# 크롤러: Kia (Selenium)
# =====================
def crawl_kia(driver) -> List[Dict]:
    print("Crawling Kia with Selenium...")
    results = []

    try:
        driver.get(KIA_URL)
        time.sleep(2)

        selector_candidates = [
            ".cmp-accordion__item",
            "[class*='accordion']",
            "[class*='faq'] li",
            "[class*='faq'] .item",
        ]

        faq_items = []
        matched_selector = None

        for selector in selector_candidates:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                faq_items = driver.find_elements(By.CSS_SELECTOR, selector)
                if faq_items:
                    matched_selector = selector
                    print(f"[Kia] matched selector: {selector}, count={len(faq_items)}")
                    break
            except TimeoutException:
                continue

        if not faq_items:
            print("[Kia] FAQ items not found")
            return []

        for item in faq_items:
            question = ""
            answer = ""

            # 질문 후보 태그 탐색
            for q_sel in ["button.cmp-accordion__button", "dt", "summary", "button", "h3", "h4"]:
                try:
                    q_el = item.find_element(By.CSS_SELECTOR, q_sel)
                    question = safe_text(q_el)
                    if question:
                        break
                except Exception:
                    continue

            # 답변 후보 태그 탐색
            for a_sel in [".cmp-accordion__panel", "dd", "[class*='panel']", "[class*='content']", "[class*='answer']", "div"]:
                try:
                    a_el = item.find_element(By.CSS_SELECTOR, a_sel)
                    answer = safe_inner_html_text(a_el)
                    if answer:
                        break
                except Exception:
                    continue

            row = {
                "question": question,
                "answer": answer,
                "category": "Kia EV Guide",
                "source": "기아",
            }

            if validate_item(row):
                results.append(row)

    except Exception as e:
        print(f"[Kia] failed: {e}")

    return deduplicate_items(results)


# =====================
# 크롤러: Tesla (정적 파싱 유지)
# =====================
def crawl_tesla() -> List[Dict]:
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

            if "se-quotation" in classes:
                question = clean_text(comp.get_text(separator=" "))

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

                i = j
            else:
                i += 1

    except Exception as e:
        print(f"[Tesla] failed: {e}")

    print(f"[Tesla] {len(results)}건 파싱 완료")
    return deduplicate_items(results)


# =====================
# 크롤러: KEPCO (REST API 유지)
# =====================
def crawl_kepco() -> List[Dict]:
    print("Crawling KEPCO API...")
    results = []

    try:
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
# 크롤러: Hyundai (Selenium)
# =====================
def crawl_hyundai(driver) -> List[Dict]:
    print("Crawling Hyundai with Selenium...")
    results = []

    try:
        driver.get(HYUNDAI_URL)
        time.sleep(2)

        while True:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ui_accordion.acc_01 dl"))
                )
            except TimeoutException:
                print("[Hyundai] FAQ items not found on this page")
                break

            time.sleep(1)

            faq_list = driver.find_elements(By.CSS_SELECTOR, "div.ui_accordion.acc_01 dl")
            if not faq_list:
                print("[Hyundai] FAQ items not found on this page")
                break

            print(f"[Hyundai] found {len(faq_list)} items on current page")

            for faq in faq_list:
                try:
                    dt = faq.find_element(By.CSS_SELECTOR, "dt")

                    try:
                        category_el = dt.find_element(By.CSS_SELECTOR, "b i")
                        category = safe_text(category_el)
                    except Exception:
                        category = "기타"

                    try:
                        title_el = dt.find_element(By.CSS_SELECTOR, "b span")
                        title = safe_text(title_el)
                    except Exception:
                        title = ""

                    if not title:
                        continue

                    # 아코디언 펼치기
                    driver.execute_script("arguments[0].click();", dt)
                    time.sleep(0.3)

                    try:
                        content_el = faq.find_element(By.CSS_SELECTOR, "dd div.exp")
                        content = safe_inner_html_text(content_el)
                    except Exception:
                        content = ""

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

            # 다음 페이지 버튼 찾기
            try:
                current_page = driver.find_element(By.CSS_SELECTOR, "div.pagination strong")
                next_btn = current_page.find_element(By.XPATH, "./following-sibling::a[1]")

                if not next_btn:
                    print("[Hyundai] no next page, done")
                    break

                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)

            except Exception:
                print("[Hyundai] pagination ended")
                break

    except Exception as e:
        print(f"[Hyundai] failed: {e}")

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
            cleaned_at    DATETIME NULL,
            category      VARCHAR(100),
            source        VARCHAR(100) NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """)
    conn.commit()
    cursor.close()
    print("[DB] 테이블 확인/생성 완료")


def save_to_db(items: List[Dict]):
    print(f"\n[DB] {len(items)}건 저장 시작...")

    conn = get_connection()
    create_table_if_not_exists(conn)

    cursor = conn.cursor()
    query = """
        INSERT INTO faq (question, answer, category, source)
        VALUES (%s, %s, %s, %s)
    """

    success = 0
    for item in items:
        try:
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

    for source, count in source_count.items():
        print(f"  - {source}: {count}건")

    print("=========================\n")


# =====================
# 메인
# =====================
def main():
    all_data = []

    driver = create_driver()

    try:
        # 동적 페이지는 Selenium 사용
        kia_data = crawl_kia(driver)
        hyundai_data = crawl_hyundai(driver)
    finally:
        driver.quit()

    # 정적/API는 기존 방식 유지
    kepco_data = crawl_kepco()
    tesla_data = crawl_tesla()

    all_data.extend(kia_data)
    all_data.extend(hyundai_data)
    all_data.extend(kepco_data)
    all_data.extend(tesla_data)

    all_data = deduplicate_items(all_data)

    print_summary(all_data)
    save_to_db(all_data)


if __name__ == "__main__":
    main()