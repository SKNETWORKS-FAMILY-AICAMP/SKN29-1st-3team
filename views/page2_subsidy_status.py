"""
정책 보도자료 페이지
- 기후에너지환경부 보도·설명 게시판을 iframe으로 표시
- CSS injection으로 헤더/푸터/네비 등 불필요한 영역 숨김
"""

import streamlit as st
import streamlit.components.v1 as components

LIST_URL = (
    "https://www.mcee.go.kr/home/web/board/list.do"
    "?menuId=10525&boardMasterId=1&boardCategoryId="
    "&maxIndexPages=10&maxPageItems=10"
    "&searchKey=titleOrContent"
    "&searchValue=%EC%A0%84%EA%B8%B0%EC%B0%A8+%EB%B3%B4%EC%A1%B0%EA%B8%88"
    "&condition.fromDate=2017-01-01"
)


def render():
    st.title("📋 전기차 보조금 정책 보도자료")
    st.caption("기후에너지환경부 보도·설명 게시판 — '전기차 보조금' 검색 결과")

    # iframe을 HTML로 감싸서 CSS injection으로 불필요한 영역 숨김
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; }}
            iframe {{ border: none; width: 100%; height: 900px; }}
        </style>
    </head>
    <body>
        <iframe
            src="{LIST_URL}"
            scrolling="yes"
            onload="
                try {{
                    var doc = this.contentDocument || this.contentWindow.document;
                    var style = doc.createElement('style');
                    style.innerHTML =
                        '.visual_wrap, .nav_wrap, .footer_wrap, #header,' +
                        '.location_wrap, .side_wrap, .sub_title_wrap {{ display: none !important; }}' +
                        '.content_wrap {{ margin: 0 !important; padding: 10px !important; }}';
                    doc.head.appendChild(style);
                }} catch(e) {{}}
            "
        ></iframe>
    </body>
    </html>
    """

    components.html(html, height=920, scrolling=False)


if __name__ == "__main__":
    render()