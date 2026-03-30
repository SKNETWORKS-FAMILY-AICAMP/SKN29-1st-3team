"""
FAQ 페이지
- 전기차 관련 FAQ를 브랜드 / 카테고리 / 키워드로 탐색
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.db_connection import get_connection


# =========================
# 데이터 로드
# =========================
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
# 필터 함수
# =========================
def filter_faq(df, source, category, keyword):
    """브랜드 / 카테고리 / 키워드 조건으로 FAQ 필터링"""
    result = df.copy()

    if source != "전체":
        result = result[result["source"] == source]

    if category != "전체":
        result = result[result["category"] == category]

    if keyword:
        result = result[
            result["question"].str.contains(keyword, case=False, na=False) |
            result["answer"].str.contains(keyword, case=False, na=False)
        ]

    return result


# =========================
# UI
# =========================
def render():
    st.title("📘 기업 FAQ 조회")
    st.markdown("전기차 관련 FAQ를 브랜드 / 카테고리 / 키워드로 탐색")

    df = load_faq_data()

    # 사이드바 필터 
    st.sidebar.header("🔎 필터")

    source_list   = ["전체"] + sorted(df["source"].dropna().unique().tolist())
    category_list = ["전체"] + sorted(df["category"].dropna().unique().tolist())

    selected_source   = st.sidebar.selectbox("브랜드 선택", source_list)
    selected_category = st.sidebar.selectbox("카테고리 선택", category_list)
    keyword           = st.sidebar.text_input("키워드 검색")

    # 필터링
    filtered_df = filter_faq(df, selected_source, selected_category, keyword)

    # 요약 지표
    col1, col2, col3 = st.columns(3)
    col1.metric("전체 FAQ",  len(df))
    col2.metric("검색 결과", len(filtered_df))
    col3.metric("브랜드 수", df["source"].nunique())

    st.divider()

    # FAQ 목록 출력 
    if filtered_df.empty:
        st.warning("검색 결과가 없습니다.")
    else:
        for _, row in filtered_df.iterrows():
            with st.expander(f"[{row['source']}] {row['question']}"):
                st.markdown(f"**카테고리:** {row['category']}")
                st.markdown("---")
                st.write(row["answer"])


if __name__ == "__main__":
    render()