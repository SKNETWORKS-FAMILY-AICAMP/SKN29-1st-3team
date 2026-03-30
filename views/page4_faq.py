# """
# FAQ 페이지
# - 전기차 관련 FAQ를 브랜드 / 카테고리 / 키워드로 탐색
# """

import os
import re
import html
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from utils.db_connection import get_connection

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="전기차 FAQ 분석 대시보드",
    layout="wide"
)

@st.cache_data
def load_faq_data():
    """faq 테이블 전체 로드"""
    conn = get_connection()
    try:
        query = "SELECT * FROM faq"
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return df


# =========================
# 공통 CSS
# =========================
def inject_css():
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
        margin-bottom: 0.3rem;
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

    /* 사이드바 약간 정리 */
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
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM faq", conn)
    conn.close()
    return df


# =========================
# 텍스트 정제
# =========================
def clean_text_basic(text: str) -> str:
    if pd.isna(text):
        return ""

    text = str(text)
    text = html.unescape(text)

    # 특수 공백 / 개행 정리
    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")

    # 과도한 공백 제거
    text = re.sub(r"[ ]{2,}", " ", text)

    # 줄 단위 공백 정리
    lines = [line.strip() for line in text.split("\n")]

    cleaned_lines = []
    blank_count = 0

    for line in lines:
        # 완전히 비어있는 줄
        if not line:
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append("")
            continue

        blank_count = 0

        # 의미 없는 단독 문자 라인 약간 정리
        if line in {".", "·", "•"}:
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # 3개 이상 연속 개행 -> 2개
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_answer_text(text: str) -> str:
    text = clean_text_basic(text)

    # 자주 나오는 기호 통일
    text = text.replace("☞", "→")
    text = text.replace("▷", "•")
    text = text.replace("●", "•")

    # 깨진 slash 줄바꿈 정리
    text = text.replace("\n/\n", " / ")

    # 괄호 주변 줄바꿈 완화
    text = re.sub(r"\n([)\]])", r"\1", text)
    text = re.sub(r"([(\[])\n", r"\1", text)

    # URL 앞뒤 과도한 개행 정리
    text = re.sub(r"\n+(https?://\S+)\n+", r"\n\\1\n", text)

    # 특정 안내 문구 정리
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_faq_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["question", "answer", "category", "source"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    df["question"] = df["question"].apply(clean_text_basic)
    df["answer_raw"] = df["answer"]
    df["answer"] = df["answer"].apply(clean_answer_text)
    df["category"] = df["category"].apply(clean_text_basic)
    df["source"] = df["source"].apply(clean_text_basic)

    return df


# =========================
# 주제 분류
# =========================
def classify_topic(text: str) -> str:
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
    related = df[
        (df["topic"] == row["topic"]) &
        (df["id"] != row["id"])
    ].copy()

    if related.empty:
        return related

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
    if "selected_related_faq_id" not in st.session_state:
        st.session_state.selected_related_faq_id = None


# =========================
# 상단 헤더
# =========================
def render_page_header(total_count, filtered_count, selected_topic, selected_source):
    st.markdown('<div class="page-title">🚗 전기차 FAQ 분석 대시보드</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">브랜드별 전기차 FAQ를 주제별로 탐색하고, 자주 묻는 이슈를 분석할 수 있는 페이지입니다.</div>',
        unsafe_allow_html=True
    )

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

    source_list = ["전체"] + sorted(df["source"].dropna().unique().tolist())
    selected_source = st.sidebar.selectbox("브랜드", source_list)

    keyword = st.sidebar.text_input("검색", placeholder="질문 키워드를 입력하세요")

    filtered = df.copy()

    if selected_source != "전체":
        filtered = filtered[filtered["source"] == selected_source]

    if keyword:
        filtered = filtered[
            filtered["question"].str.contains(keyword, case=False, na=False)
        ]

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

    if filtered.empty:
        st.markdown(
            '<div class="empty-box">조건에 맞는 FAQ가 없습니다.<br>검색어를 바꾸거나 브랜드/주제를 다시 선택해보세요.</div>',
            unsafe_allow_html=True
        )
        return

    for _, row in filtered.iterrows():
        expander_title = f"{row['source']} · {row['topic']}  \n**{row['question']}**"

        with st.expander(expander_title):
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

            

            answer = highlight(row["answer"], keyword)
            st.markdown(f"<div class='faq-answer'>{answer}</div>", unsafe_allow_html=True)

            related = get_related_faqs(df, row, topn=3)

            if not related.empty:
                st.markdown("### 📌 관련 FAQ")

                for _, r in related.iterrows():
                    button_key = f"rel_{row['id']}_{r['id']}"

                    label = f"👉 {r['question']}"
                    if st.session_state.selected_related_faq_id == r["id"]:
                        label = f"🔽 {r['question']}"

                    if st.button(label, key=button_key, use_container_width=True):
                        if st.session_state.selected_related_faq_id == r["id"]:
                            st.session_state.selected_related_faq_id = None
                        else:
                            st.session_state.selected_related_faq_id = r["id"]
                        st.rerun()

                    if st.session_state.selected_related_faq_id == r["id"]:
                        rel_answer = highlight(r["answer"], keyword)
                        st.markdown(f"**[{r['source']}] {r['question']}**")
                        st.markdown(f"<div class='faq-answer'>{rel_answer}</div>", unsafe_allow_html=True)



# =========================
# 메인 실행
# =========================
def render():
    inject_css()
    init_session_state()

    df = load_data()
    df = clean_faq_dataframe(df)
    df["topic"] = df["question"].apply(classify_topic)

    main_tab1, main_tab2 = st.tabs(["📊 분석", "📂 FAQ 탐색"])

    with main_tab1:
        render_analysis_tab(df)

    with main_tab2:
        render_explore_tab(df)


if __name__ == "__main__":
    render()