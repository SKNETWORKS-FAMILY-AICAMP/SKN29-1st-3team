import streamlit as st

def render():
    st.title("🔍 전기차 관련 뉴스 워드클라우드")
    st.caption("전기차 관련 뉴스에서 자주 언급된 단어들을 시각화한 워드클라우드입니다.")

    wordcloud_path = "./wordcloud/wordcloud.png"
    try:
        st.image(wordcloud_path, width="stretch")
    except FileNotFoundError:
        st.error("워드클라우드 이미지가 없습니다.")

if __name__ == "__main__":
    render()