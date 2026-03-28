"""
Page 3 — 구매자 프로파일 분석
- 전기차(연료코드 5) 전 차종
- 성별 × 연령대 교차분석
- 코드 테이블 JOIN으로 한글명 표시
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db_connection import get_connection


@st.cache_data(ttl=300)
def load_profile_data():
    """
    DB에서 전기차 구매자 프로파일 데이터를 불러와 DataFrame 반환
    - car_registration_stats에 코드 테이블 3개 JOIN 
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.regist_yy AS year,
                    c.regist_mt AS month,
                    v.name AS car_type,
                    s.name AS gender,
                    a.name AS age_group,
                    c.cnt AS reg_count
                FROM car_registration_stats c
                LEFT JOIN code_vhcty_asort v ON c.vhcty_asort_code = v.code
                LEFT JOIN code_sexdstn s ON c.sexdstn = s.code
                LEFT JOIN code_agrde a ON c.agrde = a.code
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    df = pd.DataFrame(rows, columns=["year", "month", "car_type", "gender", "age_group", "reg_count"])
    df["year"]  = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    return df


def render():
    st.title("👤 구매자 프로파일 분석")
    st.caption("성별 × 연령대 × 차종 분석")

    df = load_profile_data()

    if df.empty:
        st.error("DB에 데이터가 없습니다")
        return

    # 사이드바 필터
    st.sidebar.header("필터")

    # 연도 필터
    years = ["전체"] + sorted(df["year"].unique().tolist())
    sel_year = st.sidebar.selectbox("연도", years, index=0)

    # 월 필터: 연도 전체 선택 시 전체 월 대상, 특정 연도 선택 시 해당 연도 월만
    if sel_year == "전체":
        months = ["전체"] + sorted(df["month"].unique().tolist())
    else:
        months = ["전체"] + sorted(df[df["year"] == int(sel_year)]["month"].unique().tolist())
    sel_month = st.sidebar.selectbox("월", months, index=0)

    # 차종 필터
    car_types = ["전체"] + sorted(df["car_type"].dropna().unique().tolist())
    sel_car = st.sidebar.selectbox("차종", car_types)

    # 필터 적용
    dff = df.copy()
    if sel_year != "전체":
        dff = dff[dff["year"] == int(sel_year)]
    if sel_month != "전체":
        dff = dff[dff["month"] == int(sel_month)]
    if sel_car != "전체":
        dff = dff[dff["car_type"] == sel_car]

    if dff.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        return

    # 선택 기간 표시
    if sel_year == "전체" and sel_month == "전체":
        period_label = "전체 기간"
    elif sel_year == "전체":
        period_label = f"전체 연도 {sel_month}월"
    elif sel_month == "전체":
        period_label = f"{sel_year}년 전체"
    else:
        period_label = f"{sel_year}년 {sel_month}월"
    st.markdown(f"### 📅 {period_label}")

    tab1, tab2, tab3 = st.tabs(["성별", "연령대", "차종"])

    # Tab1: 성별
    with tab1:
        gender_df = (
            dff.groupby("gender", dropna=False)["reg_count"]
            .sum().reset_index()
            .rename(columns={"gender": "성별", "reg_count": "등록 대수"})
        )
        fig = px.pie(
            gender_df, names="성별", values="등록 대수",
            title="성별 등록 비율",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(gender_df, use_container_width=True)

    # Tab2: 연령대 막대 + 성별×연령대 히트맵
    with tab2:
        age_df = (
            dff[dff["age_group"].notna()]
            .groupby("age_group")["reg_count"]
            .sum().reset_index()
            .rename(columns={"age_group": "연령대", "reg_count": "등록 대수"})
            .sort_values("연령대")
        )
        st.markdown("#### 연령대별 등록 대수")
        fig = px.bar(
            age_df, x="연령대", y="등록 대수",
            color="연령대", text_auto=True,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        st.plotly_chart(fig, use_container_width=True)

        # 성별 × 연령대 히트맵
        cross = (
            dff[dff["age_group"].notna() & dff["gender"].notna()]
            .groupby(["gender", "age_group"])["reg_count"]
            .sum().unstack(fill_value=0)
        )
        if not cross.empty:
            st.markdown("#### 성별 × 연령대 교차표")
            fig_heat = go.Figure(go.Heatmap(
                z=cross.values,
                x=cross.columns.tolist(),
                y=cross.index.tolist(),
                colorscale="PuBu",
                text=cross.values,
                texttemplate="%{text}",
            ))
            fig_heat.update_layout(xaxis_title="연령대", yaxis_title="성별", height=300)
            st.plotly_chart(fig_heat, use_container_width=True)

    # Tab3: 차종
    with tab3:
        car_df = (
            dff.groupby("car_type", dropna=False)["reg_count"]
            .sum().reset_index()
            .rename(columns={"car_type": "차종", "reg_count": "등록 대수"})
            .sort_values("등록 대수", ascending=False)
        )
        fig = px.bar(
            car_df, x="차종", y="등록 대수",
            title="차종별 등록 대수",
            color="차종", text_auto=True,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        st.plotly_chart(fig, use_container_width=True)

    # 요약 지표
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 등록 대수", f"{dff['reg_count'].sum():,} 대")

    col2.metric("분석 기간", period_label)

    # 법인 제외 후 최다 등록 연령대 계산
    top_age = (
        dff[dff["age_group"].notna()]
        .groupby("age_group")["reg_count"].sum().idxmax()
        if dff["age_group"].notna().any() else "N/A"
    )
    col3.metric("최다 등록 연령대", top_age)

    with st.expander("📋 원본 데이터 보기"):
        st.dataframe(
            dff.rename(columns={
                "year": "연도", "month": "월", "car_type": "차종",
                "gender": "성별", "age_group": "연령대",
                "reg_count": "등록 대수"
            }),
            use_container_width=True,
        )

if __name__ == "__main__":
    render()