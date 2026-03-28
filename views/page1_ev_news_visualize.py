"""
Page 1 — 정책 뉴스에 따른 전기차 등록 대수 시각화
- 월별 등록 대수를 차종별로 누적 막대로 표시
- 정책 뉴스 수를 꺽은선으로 함께 표시
- 차종 선택: 전체(누적 막대) / 개별 차종(해당 차종만)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db_connection import get_connection

# 정책 이벤트 마커 목록
POLICY_EVENTS = [
    {"year": 2026, "month": 2, "label": "21년 보조금 확정"},
    {"year": 2025, "month": 7, "label": "충전시설 의무설치 강화"},
    {"year": 2025, "month": 2, "label": "보조금 전면 개편"},
    {"year": 2023, "month": 2, "label": "24년 전기차 보조금 발표"},
]

VHCTY_NAME = {"1": "승용", "2": "승합", "3": "화물", "4": "특수"} # 차종코드
BAR_COLORS = {"승용": "#4373CC", "승합": "#F6D531", "화물": "#66CC54", "특수": "#8149CF"} # 차종별 막대 색상

@st.cache_data(ttl=300) # 함수 결과 캐싱 (300초)
def load_data():
    """
    DB에서 전기차 등록 대수와 월별 뉴스 수를 불러와 두 개의 DataFrame 반환
    - df_total : 월별 전체 합산 + 뉴스 수
    - df_pivot : 월별 차종별 피벗
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 월별·차종별 전기차 등록 대수 합산
            cur.execute("""
                SELECT regist_yy        AS year,
                       regist_mt        AS month,
                       vhcty_asort_code AS vhcty,
                       SUM(cnt)         AS reg_count
                FROM car_registration_stats
                GROUP BY regist_yy, regist_mt, vhcty_asort_code
                ORDER BY regist_yy, regist_mt, vhcty_asort_code
            """)
            reg_rows = cur.fetchall()

            # 월별 뉴스 수
            cur.execute("""
                SELECT year, month, news_count
                FROM ev_news_monthly
                ORDER BY year, month
            """)
            news_rows = cur.fetchall()
    finally:
        conn.close()

    df_reg = pd.DataFrame(reg_rows, columns=["year", "month", "vhcty", "reg_count"])
    df_news = pd.DataFrame(news_rows, columns=["year", "month", "news_count"])

    # 숫자형으로 변환
    df_reg["year"]  = pd.to_numeric(df_reg["year"])
    df_reg["month"] = pd.to_numeric(df_reg["month"])
    df_news["year"]  = pd.to_numeric(df_news["year"])
    df_news["month"] = pd.to_numeric(df_news["month"])

    df_reg["vhcty_name"] = df_reg["vhcty"].astype(str).map(VHCTY_NAME)

    def make_ym(df):
        """year/month 컬럼으로 datetime ym 컬럼 생성"""
        df = df.copy()
        df["ym"] = pd.to_datetime(
            df["year"].astype(int).astype(str) + "-" +
            df["month"].astype(int).astype(str).str.zfill(2) + "-01"
        )
        return df

    # 월별 전체 합산 후 뉴스 수 병합
    df_total = df_reg.groupby(["year", "month"])["reg_count"].sum().reset_index()
    df_total = pd.merge(df_total, df_news, on=["year", "month"], how="left").fillna(0)
    df_total = make_ym(df_total)

    # 차종별 등록 대수 테이블 만들기 (열: 승용/승합/화물/특수)
    df_pivot = df_reg.pivot_table(
        index=["year", "month"],        # 행 기준
        columns="vhcty_name",           # 열 기준
        values="reg_count",             # 값으로 사용할 컬럼
        aggfunc="sum"                   # 같은 셀에 값이 여러 개 있을 때 어떻게 합칠지
    ).reset_index().fillna(0)
    df_pivot = make_ym(df_pivot)
    df_pivot = pd.merge(df_pivot, df_news, on=["year", "month"], how="left").fillna(0)

    return df_total.sort_values("ym"), df_pivot.sort_values("ym")


def build_figure(df_total, df_pivot, sel_vhcty, show_events, sel_years):
    """
    선택된 연도, 차종 조건으로 이중축 그래프 생성
    - 차종별 누적 막대 (등록 대수)
    - 정책 뉴스 수 꺾은선
    - 반환값: (fig, 총등록대수, 월평균등록대수)
    """
    df_t = df_total[df_total["year"].isin(sel_years)]
    df_p = df_pivot[df_pivot["year"].isin(sel_years)]

    fig = go.Figure()

    # 선택된 차종만 막대 추가
    for vhcty in sel_vhcty:
        if vhcty in df_p.columns:
            fig.add_trace(go.Bar(
                x=df_p["ym"],
                y=df_p[vhcty],
                name=f"{vhcty} 등록",
                marker_color=BAR_COLORS.get(vhcty, "gray"),
                opacity=0.75,
                yaxis="y1",
            ))

    # 요약 지표 계산 (선택 차종 합산)
    reg_sum  = sum(df_p[v].sum() for v in sel_vhcty if v in df_p.columns)
    reg_mean = sum(df_p[v].mean() for v in sel_vhcty if v in df_p.columns)

    # 뉴스 꺾은선
    fig.add_trace(go.Scatter(
        x=df_t["ym"],
        y=df_t["news_count"],
        name="정책 뉴스 수",
        mode="lines+markers",
        line=dict(color="#FF5A5F", width=3),
        marker=dict(size=6),
        yaxis="y2",
    ))

    # 정책 이벤트 마커
    if show_events:
        ym_strs = df_t["ym"].dt.strftime("%Y-%m-%d").values
        for ev in POLICY_EVENTS:
            ev_str = f"{ev['year']}-{ev['month']:02d}-01"
            if ev_str in ym_strs:
                fig.add_shape(
                    type="line",
                    x0=ev_str, x1=ev_str,
                    y0=0, y1=1, yref="paper",
                    line=dict(color="gray", width=1.5, dash="dot")
                )
                fig.add_annotation(
                    x=ev_str, y=1, yref="paper",
                    text=ev["label"],
                    showarrow=False,
                    textangle=-90,
                    xanchor="right",
                    font=dict(size=11, color="gray"),
                )

    y1_title = "신규 등록 대수 (대) — " + ("전체" if len(sel_vhcty) == 4 else "+".join(sel_vhcty))
    
    fig.update_layout(
        title=dict(text="전기차 등록 추이와 정책 뉴스량 분석", font=dict(size=20)),
        barmode="stack", # 누적 막대
        xaxis=dict(title="연월", 
                   tickformat="%Y-%m",   # x축 눈금 포맷: 연-월
                   dtick="M3",           # 눈금 간격: 3개월마다
                   gridcolor="#F0F0F0" # x축 배경 그리드 색상
                   ),
        
        # y축1 설정 (왼쪽, 등록 대수)
        yaxis=dict(title=y1_title, 
                   side="left", 
                   showgrid=True, 
                   gridcolor="#F0F0F0"
                   ),
        
        # y축2 설정 (오른쪽, 뉴스 기사 수)
        yaxis2=dict(
            title="뉴스 기사 수 (건)",
            overlaying="y",         # y축1 위에 겹치도록 표시
            side="right", 
            showgrid=False,         # y2축 격자 표시 안함
            range=[0, df_t["news_count"].max() * 1.2 + 1],  # y2축 범위 설정
        ),
        
        # 범례(legend) 설정
        legend=dict(orientation="h",  # 가로형 범례
                    yanchor="bottom", # 범례 y 기준점: 아래
                    y=1.02,           # 범례 y 위치 (그래프 위쪽 약간 여백)
                    xanchor="right",  # 범례 x 기준점: 오른쪽
                    x=1               # 범례 x 위치 (그래프 오른쪽 끝)
                    ),
        margin=dict(l=50, r=50, t=100, b=50),  # 그래프 외부 여백(margin)
        hovermode="x unified",                 # 마우스 hover 시 x축 기준으로 모든 데이터 한 번에 표시
        plot_bgcolor="white",
        height=600,
    )

    return fig, reg_sum, reg_mean


def render():
    st.title("📈 정책 뉴스에 따른 전기차 등록 대수")

    df_total, df_pivot = load_data()

    if df_total.empty:
        st.error("DB에 데이터가 없습니다")
        return

    # 사이드바
    st.sidebar.header("필터")

    # 연도 슬라이더
    years = sorted(df_total["year"].unique())
    min_year, max_year = int(min(years)), int(max(years))
    
    st.sidebar.markdown("### 연도 범위 선택")
    sel_year_range = st.sidebar.slider(
        "year_range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),  # 기본: 전체 범위
        step=1,
        label_visibility="collapsed"
    )
    sel_years = list(range(sel_year_range[0], sel_year_range[1] + 1))

    show_events = st.sidebar.checkbox("정책 이벤트 마커 표시", value=True)

    # 차종 
    st.sidebar.markdown("### 차종 선택")
    vhcty_options = ["승용", "승합", "화물", "특수"]
    sel_vhcty = st.sidebar.multiselect(
        "미선택 시 전체",
        options=vhcty_options,
        default=[],  # 기본: 전체
        placeholder="전체",
    )
    # 빈 리스트면 전체로 처리
    if not sel_vhcty:
        sel_vhcty = vhcty_options

    # 그래프
    fig, reg_sum, reg_mean = build_figure(df_total, df_pivot, sel_vhcty, show_events, sel_years)
    st.plotly_chart(fig, use_container_width=True)

    # 요약 지표
    st.markdown("---")
    df_t = df_total[df_total["year"].isin(sel_years)]
    c1, c2, c3 = st.columns(3)
    c1.metric("선택 기간 총 등록", f"{int(reg_sum):,} 대")
    c2.metric("월평균 등록", f"{int(reg_mean):,} 대")
    c3.metric("총 뉴스 보도량", f"{int(df_t['news_count'].sum()):,} 건")

    # 데이터 테이블
    with st.expander("📋 원본 데이터 보기"):
        # 연도 selectbox로 해당 연도 데이터만 표시
        selected_year = st.selectbox("연도 선택", options=years, index=0)
        df_year = df_t[df_t["year"] == selected_year]
        st.dataframe(
            df_year[["year", "month", "reg_count", "news_count"]].rename(columns={
                "year": "연도", "month": "월",
                "reg_count": "등록 대수", "news_count": "뉴스 수",
            }),
            use_container_width=True,
        )

if __name__ == "__main__":
    render()