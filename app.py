import streamlit as st

st.set_page_config(
    page_title="사내 통합 업무 포털",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 사내 통합 업무 포털")
st.markdown("부서별 업무 도구를 한 곳에서 사용할 수 있는 통합 포털입니다.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("⚖️ 법령 검색")
    st.markdown(
        """
        국가법령정보센터 API를 활용한 실시간 법령 조회.
        법령명·소관부처·시행일 확인 및 상세 페이지 바로가기.
        """
    )

with col2:
    st.subheader("📊 DART 재무제표")
    st.markdown(
        """
        OpenDART API를 통한 한국 상장기업 재무제표 일괄 수집.
        복수 기업·연도 선택 후 엑셀 다운로드.
        """
    )

st.divider()
st.caption("좌측 사이드바에서 원하는 메뉴를 선택하세요. 추후 업무 도구가 지속적으로 추가될 예정입니다.")
