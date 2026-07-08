import io
import os
import time

import pandas as pd
import requests
import urllib3
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import streamlit as st

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://hytc-dart.streamlit.app/",
}

_URL_HTTPS = "https://www.law.go.kr/DRF/lawSearch.do"
_URL_HTTP = "http://www.law.go.kr/DRF/lawSearch.do"

_CLS_OPTIONS = {
    "전체": "",
    "법률": "법률",
    "대통령령": "대통령령",
    "총리령": "총리령",
    "부령": "부령",
    "조례": "조례",
    "규칙": "규칙",
    "헌법": "헌법",
}


def _make_session(verify=True):
    session = requests.Session()
    retry = Retry(total=3, connect=3, backoff_factor=0.5, allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.verify = verify
    return session


def _fetch(params):
    session = _make_session()
    try:
        return session.get(_URL_HTTPS, params=params, headers=_HEADERS, timeout=15)
    except requests.exceptions.SSLError:
        session2 = _make_session(verify=False)
        return session2.get(_URL_HTTPS, params=params, headers=_HEADERS, timeout=15)
    except requests.exceptions.ConnectionError:
        time.sleep(1)
        return _make_session().get(_URL_HTTP, params=params, headers=_HEADERS, timeout=15)


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

with st.form("search_form"):
    query = st.text_input("검색어를 입력하세요", placeholder="예: 근로기준법, 소득세법")
    col1, col2 = st.columns([2, 1])
    with col1:
        cls_label = st.selectbox("법령 구분", list(_CLS_OPTIONS.keys()))
    with col2:
        display = st.slider("결과 수", min_value=20, max_value=100, value=20, step=10)
    submitted = st.form_submit_button("🔍 검색")

if submitted and query:
    with st.spinner("검색 중..."):
        try:
            params = {
                "OC": api_key,
                "target": "law",
                "type": "XML",
                "query": query,
                "display": display,
            }
            cls_val = _CLS_OPTIONS[cls_label]
            if cls_val:
                params["cls"] = cls_val

            resp = _fetch(params)
            resp.raise_for_status()

            tree = ET.fromstring(resp.content)
            laws = tree.findall("law")

            if not laws:
                st.warning("검색 결과가 없습니다. 검색어나 필터를 변경해보세요.")
                st.stop()

            rows = []
            for law in laws:
                serial = (law.findtext("법령일련번호") or "").strip()
                rows.append(
                    {
                        "법령명": law.findtext("법령명한글") or "",
                        "법령 구분": law.findtext("법령구분명") or "",
                        "소관부처": law.findtext("소관부처명") or "",
                        "시행일자": law.findtext("시행일자") or "",
                        "상세보기": f"https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={serial}" if serial else "",
                    }
                )

            df = pd.DataFrame(rows)
            st.success(f"총 {len(df)}건 검색되었습니다.")
            st.dataframe(
                df,
                width="stretch",
                column_config={
                    "상세보기": st.column_config.LinkColumn("상세보기", display_text="열기")
                },
                hide_index=True,
            )

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="법령검색")
            st.download_button(
                label="📁 엑셀 다운로드",
                data=buffer.getvalue(),
                file_name=f"법령검색_{query}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        except requests.exceptions.ConnectionError as e:
            st.error(f"연결 오류: 서버에 연결할 수 없습니다. 잠시 후 다시 시도하세요.\n({e})")
        except requests.exceptions.Timeout:
            st.error("요청 시간이 초과되었습니다. 잠시 후 다시 시도하세요.")
        except requests.exceptions.RequestException as e:
            st.error(f"API 통신 오류: {e}")
        except ET.ParseError as e:
            st.error(f"응답 파싱 오류: {e}")
