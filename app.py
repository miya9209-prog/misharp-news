
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("## MISHARP NEWS POST")
st.markdown("패션/IT/소비유통/경제기사 뉴스/정보 브리핑")

col1, col2 = st.columns(2)

with col1:
    st.subheader("오늘의 패션 · 유통 · IT · 마케팅 뉴스")
    if "left_limit" not in st.session_state:
        st.session_state.left_limit = 10
    news = [f"패션/IT 뉴스 {i}" for i in range(1, 51)]
    for n in news[:st.session_state.left_limit]:
        st.write("-", n)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("더보기", key="l_more"):
            st.session_state.left_limit = min(50, st.session_state.left_limit + 10)
    with c2:
        if st.button("접기", key="l_less"):
            st.session_state.left_limit = 10

with col2:
    st.subheader("오늘 주요 경제뉴스")
    if "right_limit" not in st.session_state:
        st.session_state.right_limit = 10
    news = [f"경제뉴스 {i}" for i in range(1, 51)]
    for n in news[:st.session_state.right_limit]:
        st.write("-", n)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("더보기", key="r_more"):
            st.session_state.right_limit = min(50, st.session_state.right_limit + 10)
    with c2:
        if st.button("접기", key="r_less"):
            st.session_state.right_limit = 10

st.markdown("---")
st.markdown("### 관련 정보 사이트")
st.write("정책브리핑 / 기업마당 / 중소벤처24 / 통계청 / 패션비즈 / 전자신문 등")

st.markdown("---")
st.caption("© MISHARP")
