import os
import re
import html
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.db_connection import get_connection
from dotenv import load_dotenv
import pymysql
load_dotenv()

# =========================
# 공통 정제 유틸
# =========================
def normalize_whitespace(text: str) -> str:
    # HTML 엔티티, 특수 공백, 줄바꿈 정리
    if not text:
        return ""

    text = html.unescape(str(text))

    # 깨지는 공백/제어문자 정리
    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = text.replace("\\1", " ")
    text = text.replace("​", " ")   # zero width
    text = text.replace("﻿", " ")   # BOM

    # 기호 통일 (UI용)
    text = text.replace("☞", "→")
    text = text.replace("▷", "•")
    text = text.replace("●", "•")

    # 줄 단위 trim + 공백 압축
    lines = [line.strip() for line in text.split("\n")]
    lines = [re.sub(r"[ ]{2,}", " ", line) for line in lines]

    return "\n".join(lines).strip()


def remove_noise_lines(lines):
    # 의미 없는 라인 제거 (링크, 버튼 텍스트 등)
    cleaned = []

    exact_noise = {
        "자세히 보기",
        "바로가기",
        "?",
        "APP",
        "App",
    }

    for line in lines:
        line = line.strip()

        if not line:
            cleaned.append("")
            continue

        # 단독 기호 제거
        if line in {".", "·", "•", "-", "—", "!", ","}:
            continue

        # 고정 노이즈 제거
        if line in exact_noise:
            continue

        # URL 단독 제거
        if re.fullmatch(r"https?://\S+", line):
            continue

        # 도메인만 있는 경우 제거
        if re.fullmatch(r"[A-Za-z0-9.-]+\.(com|net|org|kr|co\.kr)", line):
            continue

        # 줄 깨짐으로 생긴 / 제거
        if line == "/":
            continue

        cleaned.append(line)

    # 빈 줄 2개 이상 → 1개로 축소
    result = []
    blank_count = 0

    for line in cleaned:
        if line == "":
            blank_count += 1
            if blank_count <= 1:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    return result


def merge_broken_lines(lines):
    # 너무 짧은 문장 조각들을 앞뒤로 붙여서 자연스럽게 만듦
    result = []
    buffer = ""

    for line in lines:
        line = line.strip()

        if not line:
            if buffer:
                result.append(buffer.strip())
                buffer = ""
            result.append("")
            continue

        # 괄호만 따로 있는 경우 붙이기
        if line in {"(", ")"}:
            if buffer:
                buffer += line
            else:
                buffer = line
            continue

        # 짧은 파편 라인 → 버퍼에 누적
        if len(line) <= 3 and not re.search(r"[.!?)]$", line):
            if buffer:
                buffer += " " + line
            else:
                buffer = line
            continue

        # 버퍼 있으면 합치고 초기화
        if buffer:
            line = buffer + " " + line
            buffer = ""

        result.append(line)

    if buffer:
        result.append(buffer.strip())

    return result


def cleanup_symbols_and_breaks(text: str) -> str:
    # 줄바꿈 깨짐, 괄호 위치, 공백 정리
    text = text.replace("\n/\n", " / ")
    text = re.sub(r"\n([)\]])", r"\1", text)
    text = re.sub(r"([(\[])\n", r"\1", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def apply_common_rules(text: str) -> str:
    # 전체 정제 파이프라인
    text = normalize_whitespace(text)
    lines = text.split("\n")
    lines = remove_noise_lines(lines)
    lines = merge_broken_lines(lines)
    text = "\n".join(lines)
    text = cleanup_symbols_and_breaks(text)
    return text.strip()


# =========================
# 브랜드별 정제
# =========================
def clean_tesla_answer(text: str) -> str:
    # 테슬라 특유 노이즈 (🔽, 링크, shop 등) 제거
    text = apply_common_rules(text)

    filtered = []
    cut_mode = False  # 🔽 이후 전부 제거

    for line in text.split("\n"):
        s = line.strip()

        if "🔽" in s or "자세히 보기" in s:
            cut_mode = True
            continue

        if cut_mode:
            continue

        if "채우기" in s:
            continue
        if "..." in s or "…" in s:
            continue

        # 테슬라 링크/메뉴 제거
        if s in { "Tesla Shop", "Parts Catalog"}:
            continue
        if "blog.naver.com" in s:
            continue
        if "shop.tesla.com" in s:
            continue
        if "ts.la" in s:
            continue
        if s.startswith("Tesla |"):
            continue
        if "Tesla 자주 묻는 질문 Vol." in s:
            continue

        filtered.append(line)

    text = "\n".join(filtered)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_hyundai_kia_answer(text: str) -> str:
    # 현대/기아: 기본 정제 + 간단 안내문 제거
    text = apply_common_rules(text)

    lines = []
    for line in text.split("\n"):
        if line.strip() == "▶바로가기":
            continue
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def summarize_kepco_charge_table(text: str) -> str:
    # 문자열로 들어온 표 → 읽기 쉬운 문장으로 요약
    raw = normalize_whitespace(text)

    # 정규식으로 요금 값 추출
    under_100 = re.search(r"100kW미만\s+([0-9.]+)", raw)
    over_100 = re.search(r"100kW이상\s+([0-9.]+)", raw)

    apt_low = re.search(r"경부하 시간대\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", raw)
    apt_mid = re.search(r"중간부하 시간대\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", raw)
    apt_peak = re.search(r"최대부하 시간대\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", raw)

    parts = []
    parts.append("시행일자는 2023.5.16 기준입니다.")

    # 공용 충전기
    if under_100 and over_100:
        parts.append(
            f"공용 충전기 요금은 100kW 미만은 {under_100.group(1)}원/kWh, "
            f"100kW 이상은 {over_100.group(1)}원/kWh입니다."
        )

    # 아파트 충전기
    if apt_low and apt_mid and apt_peak:
        parts.append("아파트용 충전기 요금은 계절과 시간대에 따라 달라집니다.")
        parts.append(
            f"경부하: 여름 {apt_low.group(1)}, 봄·가을 {apt_low.group(2)}, 겨울 {apt_low.group(3)}"
        )

    # 공통 안내
    parts.append("로밍 결제 시 요금이 달라질 수 있습니다.")

    return "\n\n".join(parts).strip()


def clean_kepco_answer(question: str, text: str) -> str:
    # '충전요금' 질문이면 표 → 요약 변환
    if "충전요금" in question:
        return summarize_kepco_charge_table(text)

    text = apply_common_rules(text)
    return text.strip()


def clean_answer(question: str, answer: str, source: str, category: str) -> str:
    # source 기준으로 정제 로직 분기
    if source == "테슬라":
        return clean_tesla_answer(answer)

    if source == "한전":
        return clean_kepco_answer(question, answer)

    if source in {"현대자동차", "기아"}:
        return clean_hyundai_kia_answer(answer)

    # 기본 정제
    return apply_common_rules(answer)


# =========================
# DB 처리
# =========================
def fetch_faq_rows(conn):
    # FAQ 전체 조회
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT id, question, answer, category, source, answer_clean
        FROM faq
        ORDER BY id
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def update_cleaned_answer(conn, faq_id: int, cleaned_text: str):
    # 정제 결과 DB 업데이트
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE faq
        SET answer_clean = %s,
            cleaned_at = %s
        WHERE id = %s
    """, (cleaned_text, datetime.now(), faq_id))
    cursor.close()


def run_cleaning(update_all: bool = True):
    # 전체 정제 실행 메인 함수
    conn = get_connection()

    try:
        rows = fetch_faq_rows(conn)
        total = len(rows)
        updated = 0
        skipped = 0

        for row in rows:
            current_clean = (row.get("answer_clean") or "").strip()

            # 기존 값 있으면 스킵 (옵션)
            if not update_all and current_clean:
                skipped += 1
                continue

            # 핵심: 여기서 브랜드별 정제 실행
            cleaned = clean_answer(
                question=row.get("question", ""),
                answer=row.get("answer", ""),
                source=row.get("source", ""),
                category=row.get("category", ""),
            )

            update_cleaned_answer(conn, row["id"], cleaned)
            updated += 1

        conn.commit()
        print(f"[완료] 전체 {total}건 중 {updated}건 정제 업데이트, {skipped}건 건너뜀")

    finally:
        conn.close()


if __name__ == "__main__":
    # True: 전체 재정제
    # False: 비어있는 것만
    run_cleaning(update_all=True)