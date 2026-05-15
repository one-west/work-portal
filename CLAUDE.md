# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app does

사내 통합 업무 포털 — 법령검색·DART 재무제표 수집 등 부서별 업무 도구를 단일 Streamlit 멀티페이지 포털로 통합.
배포: https://hytc-dart.streamlit.app/

## Running locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

API 키는 `.env`에 설정:
```
DART_API_KEY=...
LAW_API_KEY=...
```
Streamlit Cloud는 `.streamlit/secret.toml` 또는 대시보드 Secrets 사용.

## Directory structure

```
streamlit_dart/
├── Home.py                  # 포털 메인 랜딩 페이지 (진입점)
├── pages/
│   ├── 1_법령검색.py         # 국가법령정보센터 API 연동
│   └── 2_DART재무제표.py     # OpenDART 재무제표 수집기
├── docs_cache/              # OpenDartReader corp_codes 캐시 (git 추적)
├── requirements.txt
└── CLAUDE.md
```

## Architecture

Streamlit 네이티브 멀티페이지 앱. `Home.py`가 진입점, `pages/` 하위 파일이 자동으로 사이드바에 노출됨.

### pages/1_법령검색.py
- API: `GET http://www.law.go.kr/DRF/lawSearch.do` (params: OC, target=law, type=XML, query)
- XML `<law>` 태그 파싱 → DataFrame → `st.column_config.LinkColumn`으로 상세 URL 표시
- 상세 URL 형식: `https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={법령일련번호}`
- LAW_API_KEY: `.env` → `st.secrets` → 사이드바 입력 순

### pages/2_DART재무제표.py
주요 함수:
- `to_number_strict(x)` — DART 숫자 문자열 정규화 (유니코드 공백·삼각형/괄호 음수 처리)
- `save_excel_with_comma_format(df, file_name)` — XlsxWriter + openpyxl 2중 저장, `#,##0` 서식
- `init_dart(key)` — `@st.cache_resource` 래핑된 OpenDartReader 초기화

실행 흐름: API 키 로드 → corp_codes 캐시 복사 → `init_dart()` → UI → 수집 버튼 → finstate_all() → (XBRL 없으면 finstate() fallback) → 엑셀 저장

## OpenDartReader 캐시 관리

`docs_cache/opendartreader_corp_codes_{YYYYMMDD}.pkl` 형식으로 캐시. Streamlit Cloud는 파일시스템이 일시적이라 앱 시작 시 기존 파일을 오늘 날짜로 복사해 재사용. 캐시가 오래되면 `docs_cache/`의 pkl 파일을 최신으로 교체 후 커밋.

## 기업 목록 변경

`pages/2_DART재무제표.py`의 `code_name_map` dict에 직접 추가/수정. 키는 종목코드(6자리) 또는 DART 고유번호(8자리, 비상장사).

## API 동작 특이사항

- `finstate_all()` — XBRL 기반. 당일 제출 보고서나 일부 분기 보고서는 XBRL 처리 전 빈 결과 반환
- `finstate()` — non-XBRL. fallback으로 사용 (CFS → OFS 순)

## Streamlit Cloud 배포 시 주의

메인 파일 설정을 `Home.py`로 지정해야 함 (대시보드 → App settings → Main file path).
