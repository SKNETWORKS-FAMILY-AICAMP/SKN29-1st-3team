import streamlit as st

st.set_page_config(
    page_title="전기차 등록 대시보드",
    page_icon="⚡",
    layout="wide",
)

# 페이지 메뉴
MENU = {
    "정책 뉴스 & 전기차 등록 대수": "views.page1_ev_news_visualize",
    "구매자 프로파일": "views.page2_buyer_profile",
    "FAQ" : "views.page3_faq"
}

# 사이드바
st.sidebar.markdown("# ⚡ EV Dashboard")
st.sidebar.markdown("---")
st.sidebar.caption("MENU")

# MENU[0]을 current_page로 설정
if "current_page" not in st.session_state:
    st.session_state.current_page = list(MENU.keys())[0]

# 네비 버튼 렌더링
def render_nav():
    for label in MENU.keys():
        is_selected = st.session_state.current_page == label

        if st.sidebar.button(
            label,
            use_container_width=True,
            key=f"nav_{label}",
            type="primary" if is_selected else "secondary"
        ):
            st.session_state.current_page = label
            st.rerun()

render_nav()

# 페이지 렌더링
page = st.session_state.current_page
module_path = MENU[page]

module = __import__(module_path, fromlist=["render"])
module.render()