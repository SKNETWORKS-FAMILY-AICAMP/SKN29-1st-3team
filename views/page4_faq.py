import os
import re
import html
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db_connection import get_connection

# =========================
# 기본 설정
# =========================
# 스트림릿 페이지 기본 설정
st.set_page_config(
    page_title="전기차 FAQ 분석 대시보드",
    layout="wide"
)


# =========================
# 공통 CSS
# =========================
def inject_css():
    # 전체 페이지 스타일 커스텀
    st.markdown("""
    <style>
    .main {
        background-color: #f7f9fc;
    }

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1150px;
    }

    .page-title {
        font-size: 2rem;
        font-weight: 800;
        color: #16213e;
        margin-top: 0.8rem;
    }

    .page-subtitle {
        font-size: 0.98rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }

    .summary-wrap {
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }

    .summary-chip {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 999px;
        padding: 0.45rem 0.85rem;
        font-size: 0.88rem;
        color: #374151;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
        margin-top: 0.5rem;
        margin-bottom: 0.6rem;
    }

    .faq-meta {
        margin-bottom: 0.5rem;
    }

    .topic-badge {
        display: inline-block;
        background: #e8f1ff;
        color: #1d4ed8;
        border-radius: 999px;
        padding: 0.2rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-bottom: 0.2rem;
    }

    .brand-badge {
        display: inline-block;
        background: #f3f4f6;
        color: #374151;
        border-radius: 999px;
        padding: 0.2rem 0.65rem;
        font-size: 0.78rem;
        margin-right: 0.35rem;
        margin-bottom: 0.2rem;
    }

    

    .faq-answer {
        background: #fbfdff;
        border: 1px solid #eef2ff;
        border-radius: 12px;
        padding: 1rem;
        color: #374151;
        line-height: 1.75;
        margin-top: 0.4rem;
        white-space: pre-wrap;
    }

    .related-box {
        background: #f8fbff;
        border: 1px solid #dbeafe;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin-top: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .related-title {
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.55rem;
    }

    .empty-box {
        background: white;
        border: 1px dashed #cbd5e1;
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        color: #6b7280;
        margin-top: 1rem;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        margin-bottom: 0.9rem !important;
        background: #ffffff !important;
        box-shadow: 0 2px 10px rgba(17, 24, 39, 0.04) !important;
    }

    div[data-testid="stExpander"] details summary {
        padding-top: 0.4rem !important;
        padding-bottom: 0.4rem !important;
    }

    .top-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 10px rgba(17, 24, 39, 0.04);
        min-height: 110px;
    }

    .top-card-title {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 0.45rem;
    }

    .top-card-value {
        font-size: 1.35rem;
        font-weight: 800;
        color: #16213e;
        margin-bottom: 0.3rem;
    }

    .top-card-desc {
        font-size: 0.9rem;
        color: #4b5563;
    }

    mark {
        background-color: #fff3b0;
        padding: 0.05rem 0.2rem;
        border-radius: 0.2rem;
    }

    /* 사이드바 영역 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #f9fafb;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# 데이터 로드
# =========================
@st.cache_data
def load_data():
    # FAQ 테이블 전체 조회
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM faq", conn)
    conn.close()
    return df


# =========================
# 텍스트 정제
# =========================
def clean_text_basic(text: str) -> str:
    # 공통적으로 쓰는 기본 텍스트 정리
    if pd.isna(text):
        return ""

    text = str(text)
    text = html.unescape(text)

    # 특수 공백 / 개행 정리
    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")

    # 연속 공백 정리
    text = re.sub(r"[ ]{2,}", " ", text)

    # 줄 단위 앞뒤 공백 제거
    lines = [line.strip() for line in text.split("\n")]

    cleaned_lines = []
    blank_count = 0

    for line in lines:
        # 빈 줄은 1줄까지만 허용
        if not line:
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append("")
            continue

        blank_count = 0

        # 의미 없는 단독 기호 제거
        if line in {".", "·", "•"}:
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # 개행 너무 많이 붙은 경우 정리
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_answer_text(text: str) -> str:
    # answer 컬럼 전용 후처리
    text = clean_text_basic(text)

    # 기호 통일
    text = text.replace("☞", "→")
    text = text.replace("▷", "•")
    text = text.replace("●", "•")

    # slash가 줄 단위로 찢어진 경우 정리
    text = text.replace("\n/\n", " / ")

    # 괄호 주변 어색한 줄바꿈 정리
    text = re.sub(r"\n([)\]])", r"\1", text)
    text = re.sub(r"([(\[])\n", r"\1", text)

    # URL 앞뒤 개행 정리
    text = re.sub(r"\n+(https?://\S+)\n+", r"\n\1\n", text)

    # 개행 재정리
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_faq_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 문자열 컬럼 기본 정리
    for col in ["question", "answer", "category", "source"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # answer_clean이 없을 수도 있으니 대비
    if "answer_clean" in df.columns:
        df["answer_clean"] = df["answer_clean"].fillna("").astype(str)
    else:
        df["answer_clean"] = ""

    # 질문/카테고리/출처 기본 정리
    df["question"] = df["question"].apply(clean_text_basic)
    df["category"] = df["category"].apply(clean_text_basic)
    df["source"] = df["source"].apply(clean_text_basic)

    # 원본 answer는 따로 보관
    df["answer_raw"] = df["answer"]

    # 화면에 보여줄 answer 생성
    # 우선순위: answer_clean -> 없으면 answer 정제본
    df["answer_display"] = df["answer_clean"]

    empty_mask = df["answer_display"].str.strip() == ""
    df.loc[empty_mask, "answer_display"] = (
        df.loc[empty_mask, "answer"].apply(clean_answer_text)
    )

    return df


def extract_number_after_label(text: str, label: str):
    # 특정 라벨 뒤에 오는 숫자 1개 추출
    pattern = rf"{re.escape(label)}\s+([0-9.]+)"
    m = re.search(pattern, text)
    return m.group(1) if m else None


def extract_three_numbers_after_label(text: str, label: str):
    # 특정 라벨 뒤에 오는 숫자 3개 추출
    pattern = rf"{re.escape(label)}\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)"
    m = re.search(pattern, text)
    if not m:
        return None
    return [m.group(1), m.group(2), m.group(3)]


def parse_kepco_charge_tables(answer_raw: str):
    """
    한전 '충전요금' FAQ 전용 파서
    원본 텍스트에서 숫자를 뽑아서 표용 DataFrame으로 변환
    """
    if not answer_raw:
        return {
            "public_df": None,
            "apartment_fee_df": None,
            "time_zone_df": None
        }

    text = html.unescape(str(answer_raw))
    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()

    # -------------------------
    # 1) 공용 충전기 표
    # -------------------------
    under_100 = extract_number_after_label(text, "100kW미만")
    over_100 = extract_number_after_label(text, "100kW이상")

    public_df = None
    if under_100 or over_100:
        public_rows = []
        if under_100:
            public_rows.append({
                "구분": "100kW 미만",
                "KEPCO_PLUG 회원결제": under_100,
                "신용카드": under_100
            })
        if over_100:
            public_rows.append({
                "구분": "100kW 이상",
                "KEPCO_PLUG 회원결제": over_100,
                "신용카드": over_100
            })
        public_df = pd.DataFrame(public_rows)

    # -------------------------
    # 2) 아파트용 충전기 요금 표
    # -------------------------
    apt_low = extract_three_numbers_after_label(text, "경부하 시간대")
    apt_mid = extract_three_numbers_after_label(text, "중간부하 시간대")
    apt_peak = extract_three_numbers_after_label(text, "최대부하 시간대")

    apartment_fee_df = None
    if apt_low and apt_mid and apt_peak:
        apartment_fee_df = pd.DataFrame([
            {
                "구분": "경부하 시간대",
                "여름": apt_low[0],
                "봄·가을": apt_low[1],
                "겨울": apt_low[2]
            },
            {
                "구분": "중간부하 시간대",
                "여름": apt_mid[0],
                "봄·가을": apt_mid[1],
                "겨울": apt_mid[2]
            },
            {
                "구분": "최대부하 시간대",
                "여름": apt_peak[0],
                "봄·가을": apt_peak[1],
                "겨울": apt_peak[2]
            },
        ])

    # -------------------------
    # 3) 시간대 구분 표
    # -------------------------
    time_zone_df = None

    summer_match = re.search(
        r"여름철\s*\(6~8월\)\s*"
        r"([0-9:~∼]+)\s*"
        r"([0-9:~∼]+\s*[0-9:~∼]+\s*[0-9:~∼]+)\s*"
        r"([0-9:~∼]+\s*[0-9:~∼]+)",
        text
    )
    spring_match = re.search(
        r"봄·가을철\s*\(3~5,\s*9~10월\)\s*"
        r"([0-9:~∼]+)\s*"
        r"([0-9:~∼]+\s*[0-9:~∼]+\s*[0-9:~∼]+)\s*"
        r"([0-9:~∼]+\s*[0-9:~∼]+)",
        text
    )
    winter_match = re.search(
        r"겨울철\s*\(11~익년 2월\)\s*"
        r"([0-9:~∼]+)\s*"
        r"([0-9:~∼]+\s*[0-9:~∼]+\s*[0-9:~∼]+)\s*"
        r"([0-9:~∼]+\s*[0-9:~∼]+)",
        text
    )

    time_rows = []

    if summer_match:
        time_rows.append({
            "계절": "여름철(6~8월)",
            "경부하 시간대": summer_match.group(1),
            "중간부하 시간대": summer_match.group(2).replace(" ", "\n"),
            "최대부하 시간대": summer_match.group(3).replace(" ", "\n"),
        })

    if spring_match:
        time_rows.append({
            "계절": "봄·가을철(3~5월, 9~10월)",
            "경부하 시간대": spring_match.group(1),
            "중간부하 시간대": spring_match.group(2).replace(" ", "\n"),
            "최대부하 시간대": spring_match.group(3).replace(" ", "\n"),
        })

    if winter_match:
        time_rows.append({
            "계절": "겨울철(11~익년 2월)",
            "경부하 시간대": winter_match.group(1),
            "중간부하 시간대": winter_match.group(2).replace(" ", "\n"),
            "최대부하 시간대": winter_match.group(3).replace(" ", "\n"),
        })

    if time_rows:
        time_zone_df = pd.DataFrame(time_rows)

    return {
        "public_df": public_df,
        "apartment_fee_df": apartment_fee_df,
        "time_zone_df": time_zone_df
    }


def render_kepco_charge_tables(row: pd.Series):
    """
    한전 '충전요금' 질문일 때만
    파싱한 표를 화면에 출력
    """
    if row.get("source", "") != "한전":
        return

    if row.get("question", "").strip() != "충전요금":
        return

    parsed = parse_kepco_charge_tables(row.get("answer_raw", ""))

    if parsed["public_df"] is not None:
        st.markdown("#### 📊 공용 충전기 요금")
        st.dataframe(parsed["public_df"], use_container_width=True, hide_index=True)

    if parsed["apartment_fee_df"] is not None:
        st.markdown("#### 📊 아파트용 충전기 요금")
        st.dataframe(parsed["apartment_fee_df"], use_container_width=True, hide_index=True)

    if parsed["time_zone_df"] is not None:
        st.markdown("#### 🕒 계절별 시간대 구분")
        st.dataframe(parsed["time_zone_df"], use_container_width=True, hide_index=True)


# =========================
# 주제 분류
# =========================
def classify_topic(text: str) -> str:
    # 질문 키워드를 보고 주제 라벨 부여
    text = str(text).lower()

    charge_keywords = ["충전", "충전기", "수퍼차저", "급속", "완속", "qr", "카드", "플러그"]
    battery_keywords = ["배터리", "고전압", "회생제동", "주행거리", "전비", "화재", "폭발", "전자파"]
    payment_keywords = ["요금", "결제", "보조금", "환불", "취소", "비용", "가격"]
    service_keywords = ["서비스", "정비", "센터", "수리", "점검", "출동", "업그레이드", "예약"]
    account_keywords = ["가입", "해지", "인증", "비밀번호", "앱", "회원", "블루링크", "계정"]

    if any(k in text for k in charge_keywords):
        return "⚡ 충전"
    elif any(k in text for k in battery_keywords):
        return "🔋 배터리/주행"
    elif any(k in text for k in payment_keywords):
        return "💰 비용/결제"
    elif any(k in text for k in service_keywords):
        return "🛠️ 서비스/정비"
    elif any(k in text for k in account_keywords):
        return "📱 가입/앱"
    else:
        return "🚗 일반"


# =========================
# 검색어 하이라이트
# =========================
def highlight(text: str, keyword: str) -> str:
    # 검색어가 있으면 답변 내에서 강조 표시
    if not keyword:
        return text

    pattern = re.escape(keyword)
    return re.sub(
        pattern,
        lambda m: f"<mark>{m.group(0)}</mark>",
        text,
        flags=re.IGNORECASE
    )


# =========================
# 관련 FAQ 추천
# =========================
def get_related_faqs(df: pd.DataFrame, row: pd.Series, topn: int = 3) -> pd.DataFrame:
    # 같은 topic 안에서 현재 질문 제외 후 추천
    related = df[
        (df["topic"] == row["topic"]) &
        (df["id"] != row["id"])
    ].copy()

    if related.empty:
        return related

    # 같은 브랜드 우선, 질문 길이 차이 적은 순으로 정렬
    related["same_source"] = (related["source"] == row["source"]).astype(int)
    related["q_len_diff"] = (related["question"].str.len() - len(row["question"])).abs()

    related = related.sort_values(
        by=["same_source", "q_len_diff"],
        ascending=[False, True]
    )

    return related.head(topn)


# =========================
# 세션 상태 초기화
# =========================
def init_session_state():
    # 관련 FAQ 펼침 상태 저장용
    if "selected_related_faq_id" not in st.session_state:
        st.session_state.selected_related_faq_id = None


# =========================
# 상단 헤더
# =========================
def render_page_header(total_count, filtered_count, selected_topic, selected_source):
    # 현재 필터 상태 요약 표시
    st.markdown(f"""
        <div class="summary-wrap">
            <span class="summary-chip">총 FAQ {total_count}건</span>
            <span class="summary-chip">현재 표시 {filtered_count}건</span>
            <span class="summary-chip">선택 주제: {selected_topic}</span>
            <span class="summary-chip">브랜드: {selected_source}</span>
        </div>
        """, unsafe_allow_html=True)


# =========================
# 분석 탭
# =========================
def render_analysis_tab(df: pd.DataFrame):
    # 주요 지표 계산
    top_topic = df["topic"].value_counts().idxmax() if not df.empty else "-"
    top_topic_count = int(df["topic"].value_counts().max()) if not df.empty else 0

    top_source = df["source"].value_counts().idxmax() if not df.empty else "-"
    top_source_count = int(df["source"].value_counts().max()) if not df.empty else 0

    total_count = len(df)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="top-card">
            <div class="top-card-title">가장 많은 주제</div>
            <div class="top-card-value">{top_topic}</div>
            <div class="top-card-desc">{top_topic_count}건</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="top-card">
            <div class="top-card-title">FAQ가 많은 브랜드</div>
            <div class="top-card-value">{top_source}</div>
            <div class="top-card-desc">{top_source_count}건</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="top-card">
            <div class="top-card-title">전체 FAQ 수</div>
            <div class="top-card-value">{total_count}</div>
            <div class="top-card-desc">수집·정제된 FAQ 기준</div>
        </div>
        """, unsafe_allow_html=True)

    # 주제별 분포 그래프
    st.markdown("<div class='section-title'>📊 주제 분포</div>", unsafe_allow_html=True)
    topic_count = df["topic"].value_counts().reset_index()
    topic_count.columns = ["topic", "count"]

    fig = px.bar(
        topic_count,
        x="topic",
        y="count",
        color="topic",
        text_auto=True
    )
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # 브랜드별 분포 그래프
    st.markdown("<div class='section-title'>🏭 브랜드 분포</div>", unsafe_allow_html=True)
    source_count = df["source"].value_counts().reset_index()
    source_count.columns = ["source", "count"]

    fig2 = px.pie(
        source_count,
        names="source",
        values="count",
        hole=0.45
    )
    fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    # 자주 등장하는 질문 TOP 3
    st.markdown("<div class='section-title'>🔥 자주 등장하는 질문</div>", unsafe_allow_html=True)
    top_q = df["question"].value_counts().head(3)

    for i, q in enumerate(top_q.index, start=1):
        st.markdown(f"""
        <div class="top-card" style="margin-bottom:0.7rem;">
            <div class="top-card-title">TOP {i}</div>
            <div class="top-card-desc" style="font-size:1rem; color:#111827;">{q}</div>
        </div>
        """, unsafe_allow_html=True)


# =========================
# FAQ 탐색 탭
# =========================
def render_explore_tab(df: pd.DataFrame):
    st.sidebar.header("🔎 필터")

    # 브랜드 필터
    source_list = ["전체"] + sorted(df["source"].dropna().unique().tolist())
    selected_source = st.sidebar.selectbox("브랜드", source_list)

    # 질문 검색 키워드
    keyword = st.sidebar.text_input("검색", placeholder="질문 키워드를 입력하세요")

    filtered = df.copy()

    if selected_source != "전체":
        filtered = filtered[filtered["source"] == selected_source]

    if keyword:
        filtered = filtered[
            filtered["question"].str.contains(keyword, case=False, na=False)
        ]

    # topic 필터
    topics = ["전체"] + list(df["topic"].dropna().unique())

    selected_topic = st.radio(
        "주제 선택",
        topics,
        horizontal=True
    )

    if selected_topic != "전체":
        filtered = filtered[filtered["topic"] == selected_topic]

    render_page_header(
        total_count=len(df),
        filtered_count=len(filtered),
        selected_topic=selected_topic,
        selected_source=selected_source
    )

    # 조건에 맞는 결과가 없을 때
    if filtered.empty:
        st.markdown(
            '<div class="empty-box">조건에 맞는 FAQ가 없습니다.<br>검색어를 바꾸거나 브랜드/주제를 다시 선택해보세요.</div>',
            unsafe_allow_html=True
        )
        return

    # FAQ 목록 출력
    for _, row in filtered.iterrows():
        expander_title = f"{row['source']} · {row['topic']}  \n**{row['question']}**"

        with st.expander(expander_title):
            # 질문 메타 정보 표시
            st.markdown(
                f"""
                <div class="faq-meta">
                    <span class="topic-badge">{row['topic']}</span>
                    <span class="brand-badge">{row['source']}</span>
                    {"<span class='brand-badge'>" + row["category"] + "</span>" if row["category"] else ""}
                </div>
                """,
                unsafe_allow_html=True
            )

            # 한전 충전요금은 일반 텍스트 대신 표로 보여줌
            is_kepco_charge = (
                row.get("source", "") == "한전" and
                row.get("question", "").strip() == "충전요금"
            )

            if is_kepco_charge:
                st.markdown(
                    "<div class='faq-answer'>한전 충전요금은 아래 표에서 확인할 수 있습니다.</div>",
                    unsafe_allow_html=True
                )
                render_kepco_charge_tables(row)
            else:
                answer = highlight(row["answer_display"], keyword)
                st.markdown(f"<div class='faq-answer'>{answer}</div>", unsafe_allow_html=True)

            # 관련 FAQ 추천
            related = get_related_faqs(df, row, topn=3)

            if not related.empty:
                st.markdown("### 📌 관련 FAQ")

                for _, r in related.iterrows():
                    # 현재 질문 id + 관련 질문 id 조합으로 버튼 key 고유화
                    button_key = f"rel_{row['id']}_{r['id']}"

                    label = f"👉 {r['question']}"
                    if st.session_state.selected_related_faq_id == r["id"]:
                        label = f"🔽 {r['question']}"

                    # 버튼 누르면 열고/닫는 토글 처리
                    if st.button(label, key=button_key, use_container_width=True):
                        if st.session_state.selected_related_faq_id == r["id"]:
                            st.session_state.selected_related_faq_id = None
                        else:
                            st.session_state.selected_related_faq_id = r["id"]
                        st.rerun()

                    # 선택된 관련 FAQ 답변 표시
                    if st.session_state.selected_related_faq_id == r["id"]:
                        rel_answer = highlight(r["answer_display"], keyword)
                        st.markdown(f"**[{r['source']}] {r['question']}**")
                        st.markdown(f"<div class='faq-answer'>{rel_answer}</div>", unsafe_allow_html=True)


# =========================
# 메인 실행
# =========================
def render():
    inject_css()
    init_session_state()

    # 페이지 상단 제목
    st.markdown('<div class="page-title">🚗 전기차 FAQ 분석 대시보드</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">브랜드별 전기차 FAQ를 주제별로 탐색하고, 자주 묻는 이슈를 분석할 수 있는 페이지입니다.</div>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='margin-top:-10px'></div>", unsafe_allow_html=True)

    # 데이터 로드 및 전처리
    df = load_data()
    df = clean_faq_dataframe(df)

    # 질문 기준 topic 분류
    df["topic"] = df["question"].apply(classify_topic)

    # 탭 구성
    main_tab1, main_tab2 = st.tabs(["📊 분석", "📂 FAQ 탐색"])

    with main_tab1:
        render_analysis_tab(df)

    with main_tab2:
        render_explore_tab(df)


# 스크립트 직접 실행 시 main 호출
if __name__ == "__main__":
    render()