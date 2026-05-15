import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from dotenv import load_dotenv

st.set_page_config(page_title="법령 검색", page_icon="⚖️", layout="wide")

load_dotenv()
api_key = os.getenv("LAW_API_KEY") or st.secrets.get("LAW_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input("법령 API 인증키(OC)를 입력하세요", type="password")
if not api_key:
    st.warning("법령 API 인증키가 필요합니다. 사이드바에서 입력하세요.")
    st.stop()

st.title("⚖️ 법령 검색")
st.markdown("국가법령정보센터 오픈 API를 활용한 실시간 법령 조회입니다.")

query = st.text_input("검색어를 입력하세요", placeholder="예: 근로기준법, 소득세법")

if st.button("🔍 검색", disabled=not query):
    with st.spinner("검색 중..."):
        try:
            resp = requests.get(
                "http://www.law.go.kr/DRF/lawSearch.do",
                params={"OC": api_key, "target": "law", "type": "XML", "query": query},
                timeout=10,
            )
            resp.raise_for_status()

            tree = ET.fromstring(resp.content)
            laws = tree.findall("law")

            if not laws:
                st.warning("검색 결과가 없습니다.")
                st.stop()

            rows = []
            for law in laws:
                serial = (law.findtext("법령일련번호") or "").strip()
                rows.append(
                    {
                        "법령명": law.findtext("법령명한글") or "",
                        "소관부처": law.findtext("소관부처명") or "",
                        "시행일자": law.findtext("시행일자") or "",
                        "상세보기": f"https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={serial}" if serial else "",
                    }
                )

            df = pd.DataFrame(rows)
            st.success(f"총 {len(df)}건 검색되었습니다.")
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "상세보기": st.column_config.LinkColumn("상세보기", display_text="열기")
                },
                hide_index=True,
            )

        except requests.exceptions.RequestException as e:
            st.error(f"API 통신 오류: {e}")
        except ET.ParseError as e:
            st.error(f"응답 파싱 오류: {e}")
