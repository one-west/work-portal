import streamlit as st

st.set_page_config(
    page_title="사내 통합 업무 포털",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 사내 통합 업무 포털")
st.markdown("부서별 업무 도구를 한 곳에서 사용할 수 있는 통합 포털입니다.")

st.divider()

TOOLS = [
    ("⚖️ 법령 검색",
     "국가법령정보센터 API를 활용한 실시간 법령 조회. 법령명·소관부처·시행일 확인 및 상세 페이지 바로가기.",
     "pages/1_법령검색.py"),
    ("📊 DART 재무제표",
     "OpenDART API를 통한 한국 상장기업 재무제표 일괄 수집. 복수 기업·연도 선택 후 엑셀 다운로드.",
     "pages/2_DART재무제표.py"),
    ("✈️ 해외출장비 정산",
     "카드 매입/승인 내역에서 특정 카드 사용분을 추출해 정산서 2-1 법인카드 탭을 자동 작성. 카드 마스터로 출장자 매핑.",
     "pages/3_해외출장비정산.py"),
]

for col, (title, desc, page) in zip(st.columns(3), TOOLS):
    with col, st.container(border=True):
        st.subheader(title)
        st.write(desc)
        st.page_link(page, label="열기 →")

st.divider()
st.caption("좌측 사이드바에서 원하는 메뉴를 선택하세요. 추후 업무 도구가 지속적으로 추가될 예정입니다.")
