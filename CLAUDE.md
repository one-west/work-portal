# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app does

사내 통합 업무 포털 — 법령검색·DART 재무제표 수집 등 업무 도구를 단일 Streamlit 멀티페이지 포털로 통합.  
배포: https://hytc-dart.streamlit.app/

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

`.env` 파일에 API 키 설정 (`.env`는 gitignore됨):
```
DART_API_KEY=...
LAW_API_KEY=...
```

Streamlit Cloud는 대시보드 Secrets에서 동일한 키를 설정.

## Directory structure

```
streamlit_dart/
├── app.py                   # 포털 메인 랜딩 페이지 (Streamlit Cloud 진입점)
├── pages/
│   ├── 1_법령검색.py         # 국가법령정보센터 API 연동
│   └── 2_DART재무제표.py     # OpenDART 재무제표 수집기
└── docs_cache/              # OpenDartReader corp_codes 캐시 (git 추적)
```

## Architecture

Streamlit 네이티브 멀티페이지 앱. `app.py`가 Streamlit Cloud 진입점이며 `pages/` 하위 파일이 자동으로 사이드바에 노출됨.

### pages/1_법령검색.py

- API: `GET http://www.law.go.kr/DRF/lawSearch.do` (params: `OC`, `target=law`, `type=XML`, `query`)
- 응답 XML `<law>` 태그 파싱 → DataFrame → `st.column_config.LinkColumn`으로 상세 링크 표시
- 상세 URL: `https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={법령일련번호}`
- `LAW_API_KEY`: `.env` → `st.secrets` → 사이드바 입력 순

### pages/2_DART재무제표.py

주요 함수:
- `to_number_strict(x)` — DART API 반환 숫자 문자열 정규화. 유니코드 공백 11종, 삼각형(△▲) 음수, 괄호 `(n)` 음수, en/em dash 처리
- `save_excel_with_comma_format(df, file_name)` — XlsxWriter로 셀 단위 쓰기 후 openpyxl로 2차 교정, `#,##0` 서식 적용
- `init_dart(key)` — `@st.cache_resource` 래핑된 OpenDartReader 초기화 (앱 재실행 시 재초기화 방지)

수집 흐름: API 키 로드 → corp_codes 캐시 복사 → `init_dart()` → UI → 버튼 클릭 → 진행률 표시(프로그레스바 + 상태 텍스트) → `finstate_all()` → XBRL 없으면 `finstate()` fallback (CFS→OFS) → 엑셀 저장 → DataFrame 미리보기 + 다운로드 버튼

## OpenDartReader 캐시

`docs_cache/opendartreader_corp_codes_{YYYYMMDD}.pkl` 형식으로 일별 캐시. Streamlit Cloud 파일시스템은 재시작마다 초기화되므로 앱 시작 시 기존 pkl을 오늘 날짜로 복사해 재사용. 캐시가 오래되면 최신 pkl로 교체 후 커밋.

## 기업 목록 변경

`pages/2_DART재무제표.py`의 `code_name_map` dict 수정. 키는 종목코드(6자리) 또는 DART 고유번호(8자리, 비상장사).

## API 동작 특이사항

- `finstate_all()` — XBRL 기반 API. 당일 제출 보고서 또는 일부 분기 보고서는 XBRL 처리 완료 전 빈 결과 반환
- `finstate()` — non-XBRL fallback. `finstate_all()` 빈 결과 시 CFS → OFS 순으로 시도
